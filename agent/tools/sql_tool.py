"""
SQL Tool -- Natural Language -> SQL -> Results
=============================================
Converts natural language questions into SQL queries using an LLM,
executes them against the SQLite database, and returns results as
a pandas DataFrame.

Key features:
  * Full schema context injection so the LLM knows every table/column.
  * Self-correction loop: if the generated SQL fails, the error is fed
    back to the LLM for up to ``MAX_RETRIES`` attempts.
  * Automatic JOIN detection -- the LLM is prompted with foreign-key
    relationships so it can compose multi-table queries.
  * Returns structured ``SQLResult`` with query, data, row count,
    and execution metadata.

Usage:
    from agent.tools.sql_tool import SQLTool

    tool = SQLTool(db_path="data/database.db")
    result = tool.run("What are the top 5 products by total sales?")
    print(result.dataframe)
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from utils.db_loader import get_schema_description

# Load environment variables
load_dotenv()

# -- Constants --------------------------------------------------------------

MAX_RETRIES: int = 3
DEFAULT_MODEL: str = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.0  # deterministic SQL generation
MAX_ROWS: int = 500  # safety limit on returned rows


# -- Data classes ----------------------------------------------------------

@dataclass
class SQLResult:
    """Structured result from the SQL tool.

    Attributes:
        success:        Whether the query executed successfully.
        question:       The original natural language question.
        sql_query:      The SQL query that was executed.
        dataframe:      Query results as a pandas DataFrame (empty on failure).
        row_count:      Number of rows returned.
        error:          Error message if execution failed.
        retries_used:   Number of retry attempts used.
        execution_time: Wall-clock time in seconds for the full pipeline.
        explanation:    LLM's natural language explanation of the results.
    """
    success: bool = False
    question: str = ""
    sql_query: str = ""
    dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    row_count: int = 0
    error: str = ""
    retries_used: int = 0
    execution_time: float = 0.0
    explanation: str = ""


# -- System prompt ---------------------------------------------------------

SQL_SYSTEM_PROMPT = """You are an expert SQL analyst. Your job is to convert
natural language questions into correct SQLite SQL queries.

RULES:
1. Output ONLY the SQL query -- no explanations, no markdown fences, no
   preamble. Just raw SQL.
2. Always use SQLite-compatible syntax.
3. Use table and column names EXACTLY as shown in the schema below.
4. When a question requires data from multiple tables, use appropriate
   JOINs. The key relationships are:
     * orders.customer_id  -> customers.customer_id
     * orders.product_id   -> products.product_id
     * orders.order_id     -> returns.order_id
5. For date filtering use the format 'YYYY-MM-DD'.
6. Use aliases to make output columns human-readable.
7. Always include ORDER BY for ranking queries.
8. Use LIMIT when the user asks for "top N" or "bottom N".
9. For aggregations, always GROUP BY the non-aggregated columns.
10. Prefer SUM/AVG/COUNT over subqueries where possible.
11. Never use DELETE, DROP, INSERT, UPDATE, ALTER, or CREATE statements.
    You are read-only.
12. When searching for names, search terms, or text values, always use case-insensitive partial matching (e.g., `LOWER(column) LIKE '%value%'` or `LIKE '%value%'`) rather than exact matches (`=`) to account for trailing spaces, first/last name variations, or differences in case.
13. If asked about teammates, group members, or relationships of a person in a multi-student/multi-person schema, search for their name across ALL candidate columns (e.g., `student_1`, `student_2`, `student_3`) to match their group, and return all group details from the matching rows.

{schema}
"""

SQL_FIX_PROMPT = """The previous SQL query failed with this error:

Query:
{query}

Error:
{error}

Fix the query. Output ONLY the corrected SQL -- nothing else.
Remember: use SQLite-compatible syntax and the exact column/table names
from the schema.
"""

EXPLAIN_PROMPT = """Given the question and the SQL query results below,
provide a clear, concise natural language answer. Be specific with
numbers. If the data is empty, say so honestly.

Question: {question}

SQL Query:
{query}

Results (first 20 rows):
{results}

Total rows returned: {row_count}
"""


# -- SQL Tool class --------------------------------------------------------

class SQLTool:
    """Natural language -> SQL -> DataFrame tool with self-correction.

    Args:
        db_path:     Path to the SQLite database.
        model:       Groq model identifier.
        temperature: LLM temperature (0.0 for deterministic SQL).
        max_retries: Max self-correction attempts on SQL errors.
        verbose:     If True, prints intermediate steps to stdout.
    """

    def __init__(
        self,
        db_path: str | Path = "data/database.db",
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = MAX_RETRIES,
        verbose: bool = True,
    ) -> None:
        self.db_path = Path(db_path)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.verbose = verbose

        # Validate database exists
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                "Run `python utils/generate_data.py` and "
                "`python utils/db_loader.py` first."
            )

        # Create SQLAlchemy engine
        self._engine: Engine = create_engine(f"sqlite:///{self.db_path}")

        # Initialize Groq LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.startswith("gsk_your"):
            raise ValueError(
                "GROQ_API_KEY is not set or is still the placeholder.\n"
                "Get a free key at https://console.groq.com/keys and "
                "set it in your .env file."
            )

        self._llm = ChatGroq(
            model=model,
            temperature=temperature,
            api_key=api_key,
            max_tokens=1024,
        )

        # Cache the schema description (regenerated when schema changes)
        self._schema: str = get_schema_description(self.db_path)

    # -- Private helpers ------------------------------------------------

    def _log(self, msg: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [SQL Tool] {msg}")

    def _extract_sql(self, raw: str) -> str:
        """Extract clean SQL from LLM output.

        Handles cases where the LLM wraps the query in markdown
        code fences or adds explanatory text.

        Args:
            raw: Raw LLM output string.

        Returns:
            Cleaned SQL query string.
        """
        # Remove markdown code fences (```sql ... ``` or ``` ... ```)
        fenced = re.search(r"```(?:sql)?\s*\n?(.*?)```", raw, re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1).strip()

        # Remove any leading text before SELECT/WITH
        match = re.search(r"(SELECT|WITH)\b", raw, re.IGNORECASE)
        if match:
            return raw[match.start():].strip().rstrip(";") + ";"

        return raw.strip()

    def _is_safe_query(self, sql: str) -> bool:
        """Check that the SQL is a read-only SELECT/WITH statement.

        Rejects any DDL/DML statements (INSERT, UPDATE, DELETE, DROP,
        ALTER, CREATE, ATTACH, DETACH, PRAGMA).

        Args:
            sql: The SQL query to validate.

        Returns:
            True if the query is safe (read-only), False otherwise.
        """
        forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
            "CREATE", "ATTACH", "DETACH", "PRAGMA",
            "REPLACE INTO", "VACUUM",
        ]
        upper_sql = sql.upper()
        for keyword in forbidden_keywords:
            # Match keyword as a word boundary to avoid false positives
            if re.search(rf"\b{keyword}\b", upper_sql):
                return False
        return True

    def _generate_sql(self, question: str, active_tables: list[str] = None, chat_history: list = None) -> str:
        """Call the LLM to generate SQL from a natural language question.

        Args:
            question: The user's natural language question.
            active_tables: Optional list of dynamic tables relevant to this session.
            chat_history: Optional session-specific message history.

        Returns:
            A cleaned SQL query string.
        """
        system = SQL_SYSTEM_PROMPT.format(schema=self._schema)
        if active_tables:
            system = (
                f"CONTEXT: The user is currently querying table(s): {', '.join(active_tables)}. "
                "Unless specified otherwise, write your SQL queries to target these tables rather than default ones.\n\n"
                + system
            )
        messages = [
            SystemMessage(content=system),
        ]
        if chat_history:
            messages.extend(chat_history[-4:])
        messages.append(HumanMessage(content=question))
        response = self._llm.invoke(messages)
        raw_sql = response.content
        return self._extract_sql(raw_sql)

    def _fix_sql(self, question: str, failed_query: str, error: str, active_tables: list[str] = None, chat_history: list = None) -> str:
        """Ask the LLM to fix a failed SQL query.

        Args:
            question:     Original natural language question.
            failed_query: The SQL query that failed.
            error:        The error message from execution.
            active_tables: Optional list of dynamic tables relevant to this session.
            chat_history: Optional session-specific message history.

        Returns:
            A corrected SQL query string.
        """
        system = SQL_SYSTEM_PROMPT.format(schema=self._schema)
        if active_tables:
            system = (
                f"CONTEXT: The user is currently querying table(s): {', '.join(active_tables)}. "
                "Unless specified otherwise, write your SQL queries to target these tables rather than default ones.\n\n"
                + system
            )
        fix_msg = SQL_FIX_PROMPT.format(query=failed_query, error=error)
        messages = [
            SystemMessage(content=system),
        ]
        if chat_history:
            messages.extend(chat_history[-4:])
        messages.append(HumanMessage(content=question))
        messages.append(HumanMessage(content=fix_msg))
        response = self._llm.invoke(messages)
        return self._extract_sql(response.content)

    def _execute_sql(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame.

        Args:
            sql: The SQL query to execute.

        Returns:
            A pandas DataFrame with the query results.

        Raises:
            ValueError: If the query is not read-only.
            Exception:  Any SQLAlchemy/SQLite execution error.
        """
        if not self._is_safe_query(sql):
            raise ValueError(
                "Blocked: only SELECT/WITH queries are allowed. "
                "The query contained a forbidden keyword."
            )

        with self._engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)

        # Safety limit
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)

        return df

    def _explain_results(
        self, question: str, sql: str, df: pd.DataFrame
    ) -> str:
        """Generate a natural language explanation of query results.

        Args:
            question: Original user question.
            sql:      The executed SQL query.
            df:       The results DataFrame.

        Returns:
            A concise natural language answer.
        """
        # Format results for the prompt (limit to 20 rows)
        results_str = df.head(20).to_string(index=False)
        prompt = EXPLAIN_PROMPT.format(
            question=question,
            query=sql,
            results=results_str,
            row_count=len(df),
        )

        messages = [
            SystemMessage(content="You are a helpful data analyst. Answer clearly and concisely."),
            HumanMessage(content=prompt),
        ]
        response = self._llm.invoke(messages)
        return response.content

    # -- Public API -----------------------------------------------------

    def run(self, question: str, active_tables: list[str] = None, chat_history: list = None) -> SQLResult:
        """Execute the full NL -> SQL -> Results pipeline.

        The pipeline:
          1. Sends the question + schema to the LLM.
          2. Extracts and validates the SQL query.
          3. Executes the query on SQLite.
          4. If execution fails, feeds the error back to the LLM
             and retries up to ``max_retries`` times.
          5. Generates a natural language explanation of the results.

        Args:
            question: A natural language question about the data.
            active_tables: Optional list of dynamic tables relevant to this session.
            chat_history: Optional session-specific message history.

        Returns:
            A ``SQLResult`` dataclass with all execution details.
        """
        start = time.time()
        result = SQLResult(question=question)

        self._log(f"Question: {question} (active tables: {active_tables})")

        # -- Step 1: Generate SQL --------------------------------------
        try:
            sql = self._generate_sql(question, active_tables=active_tables, chat_history=chat_history)
        except Exception as e:
            result.error = f"LLM generation failed: {e}"
            result.execution_time = time.time() - start
            self._log(f"[FAIL] Generation error: {e}")
            return result

        self._log(f"Generated SQL: {sql}")

        # -- Step 2: Execute with self-correction loop -----------------
        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                df = self._execute_sql(sql)
                result.success = True
                result.sql_query = sql
                result.dataframe = df
                result.row_count = len(df)
                result.retries_used = attempt - 1
                self._log(f"[OK] Query succeeded ({len(df)} rows, attempt {attempt})")
                break

            except Exception as e:
                last_error = str(e)
                self._log(f"[FAIL] Attempt {attempt}/{self.max_retries} failed: {last_error}")

                if attempt < self.max_retries:
                    try:
                        sql = self._fix_sql(question, sql, last_error, active_tables=active_tables, chat_history=chat_history)
                        self._log(f"  Fixed SQL: {sql}")
                    except Exception as fix_err:
                        self._log(f"  Fix attempt failed: {fix_err}")
                        result.error = f"Self-correction failed: {fix_err}"
                        break
                else:
                    result.error = (
                        f"Query failed after {self.max_retries} attempts. "
                        f"Last error: {last_error}"
                    )

        # -- Step 3: Generate explanation ------------------------------
        if result.success and not result.dataframe.empty:
            try:
                result.explanation = self._explain_results(
                    question, result.sql_query, result.dataframe
                )
                self._log("[OK] Explanation generated")
            except Exception as e:
                result.explanation = f"(Could not generate explanation: {e})"
                self._log(f"[!] Explanation failed: {e}")
        elif result.success and result.dataframe.empty:
            result.explanation = (
                "The query executed successfully but returned no results. "
                "This might mean no data matches the criteria in your question."
            )

        result.execution_time = time.time() - start
        self._log(f"Total time: {result.execution_time:.2f}s")
        return result

    def refresh_schema(self) -> str:
        """Re-read the database schema.

        Call this after loading new data (e.g., a user-uploaded CSV)
        so the LLM gets updated table/column information.

        Returns:
            The updated schema description string.
        """
        self._schema = get_schema_description(self.db_path)
        self._log("Schema refreshed")
        return self._schema

    @property
    def schema(self) -> str:
        """Return the current schema description string."""
        return self._schema

    def get_table_names(self) -> list[str]:
        """Return a list of all table names in the database.

        Returns:
            A list of table name strings.
        """
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(self._engine)
        return inspector.get_table_names()
