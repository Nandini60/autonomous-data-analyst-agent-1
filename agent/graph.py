"""
LangGraph Agent -- Autonomous Data Analyst Orchestrator
=========================================================
The core agent that autonomously decides which tool(s) to use
for each user question:

  * SQL Tool   -- for database queries (Superstore Sales)
  * RAG Tool   -- for document-based Q&A (uploaded PDFs)
  * Code Tool  -- for calculations, charts, and analysis

Architecture (LangGraph StateGraph):

  [START]
     |
     v
  [ROUTER]  -- LLM classifies the question
     |
     +---> [SQL_NODE]   --+
     +---> [RAG_NODE]   --+---> [SYNTHESIZER] ---> [END]
     +---> [CODE_NODE]  --+
     +---> [MULTI_HOP]  --+

Key features:
  * Intelligent routing via LLM classification
  * Multi-hop: combine SQL + RAG + Code for complex questions
  * Conversation memory (ConversationBufferMemory)
  * Structured state tracking with full audit trail
  * Graceful error handling and fallback

Usage:
    from agent.graph import DataAnalystAgent

    agent = DataAnalystAgent()
    result = agent.run("What were total sales last quarter?")
    print(result["answer"])
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL: str = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.1


# ---------------------------------------------------------------------------
# Tool type enum
# ---------------------------------------------------------------------------

class ToolType(str, Enum):
    """Available tool types for the agent."""
    SQL = "sql"
    RAG = "rag"
    CODE = "code"
    MULTI = "multi"       # multiple tools needed
    DIRECT = "direct"     # LLM can answer directly


# ---------------------------------------------------------------------------
# Agent State (TypedDict for LangGraph)
# ---------------------------------------------------------------------------

class AgentState(TypedDict, total=False):
    """State dictionary passed through the LangGraph nodes.

    Attributes:
        question:        The user's original question.
        route:           Which tool(s) to use (ToolType value).
        route_reasoning: LLM's explanation for the routing decision.
        sql_result:      Result from the SQL tool.
        rag_result:      Result from the RAG tool.
        code_result:     Result from the Code tool.
        answer:          Final synthesized answer.
        sources:         List of source citations.
        figures:         List of Plotly figure objects.
        dataframes:      List of pandas DataFrames.
        confidence:      Confidence score (0-100).
        error:           Error message if something failed.
        execution_time:  Total wall-clock time.
        tools_used:      List of tool names that were invoked.
        chat_history:    Conversation history messages.
        multi_steps:     Steps for multi-hop queries.
        active_document: Active document name.
    """
    question: str
    route: str
    route_reasoning: str
    sql_result: dict
    rag_result: dict
    code_result: dict
    answer: str
    sources: list[str]
    figures: list
    dataframes: list
    confidence: int
    error: str
    execution_time: float
    tools_used: list[str]
    chat_history: list
    multi_steps: list[dict]
    active_document: str


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

ROUTER_PROMPT = """You are an intelligent query router for a data analyst system.
You have access to these tools:

1. SQL -- Query a SQLite database.
   Currently loaded tables: {database_tables}
   USE FOR: Questions about sales, profits, counts, rankings, trends, filtering by criteria, or any custom loaded spreadsheet.

2. RAG -- Search uploaded PDF business documents.
   Active document for this session: {active_document}
   USE FOR: Questions about company policies, strategic plans, market analysis, or qualitative/text information from the active PDF/Word/Text document.

3. CODE -- Write and execute Python code for computation/visualization.
   USE FOR: Mathematical calculations, statistical analysis, creating charts/visualizations, forecasting.

4. MULTI -- Combine multiple tools for complex multi-step questions.
   USE FOR: Questions that need data from SQL AND RAG, or that need to query data AND then visualize/analyze it.

5. DIRECT -- Answer directly without any tool.
   USE FOR: Greetings, general knowledge, clarification questions, or capabilities summary.

{doc_routing_instruction}

Given the user's question, respond with EXACTLY this format:
ROUTE: <tool_name>
REASON: <one sentence explanation>

{history_context}

Question: {question}"""

MULTI_PLAN_PROMPT = """You are planning a multi-step analysis. Break down this
complex question into sequential steps. For each step, specify which tool to use.

Available tools: SQL, RAG, CODE

Question: {question}

Respond in this EXACT format (2-4 steps max):
STEP 1: [TOOL] description of what to do
STEP 2: [TOOL] description of what to do
...

Example:
STEP 1: [SQL] Query total sales by category from the database
STEP 2: [CODE] Create a bar chart of the sales data"""

SYNTHESIZE_PROMPT = """You are a professional data analyst. Synthesize the
following tool results into a clear, comprehensive answer.

Question: {question}

{tool_results}

Provide a clear, well-structured answer that:
1. Directly addresses the user's question
2. Cites specific data points and sources
3. Highlights key insights
4. Is professional but conversational
5. If charts were generated, mention them

Keep the answer concise but thorough (3-5 sentences for simple questions,
more for complex analysis)."""


# ---------------------------------------------------------------------------
# DataAnalystAgent
# ---------------------------------------------------------------------------

class DataAnalystAgent:
    """Autonomous data analyst agent using LangGraph.

    Orchestrates SQL, RAG, and Code tools to answer natural language
    questions about business data. Uses LLM-based routing to pick
    the right tool(s) for each question.

    Args:
        db_path:          Path to the SQLite database.
        docs_dir:         Path to the PDF documents directory.
        vectorstore_dir:  Path for ChromaDB persistent storage.
        model:            Groq LLM model identifier.
        verbose:          If True, print progress messages.
    """

    def __init__(
        self,
        db_path: str = "data/superstore.db",
        docs_dir: str = "data/docs",
        vectorstore_dir: str = "vectorstore",
        model: str = DEFAULT_MODEL,
        verbose: bool = True,
    ) -> None:
        self.verbose = verbose
        self.model = model

        # Initialize LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        self._llm = ChatGroq(
            model=model,
            temperature=DEFAULT_TEMPERATURE,
            api_key=api_key,
            max_tokens=2048,
        )

        # Initialize tools (lazy -- only create when first needed)
        self._db_path = db_path
        self._docs_dir = docs_dir
        self._vectorstore_dir = vectorstore_dir
        self._sql_tool = None
        self._rag_tool = None
        self._code_tool = None

        # Conversation memory
        self._chat_history: list = []

        # Build the LangGraph
        self._graph = self._build_graph()

        self._log("Agent initialized")

    # -- Tool initialization (lazy) ----------------------------------------

    def _get_sql_tool(self):
        """Lazily initialize the SQL tool."""
        if self._sql_tool is None:
            from agent.tools.sql_tool import SQLTool
            self._sql_tool = SQLTool(
                db_path=self._db_path,
                verbose=self.verbose,
            )
            self._log("SQL Tool initialized")
        return self._sql_tool

    def _get_rag_tool(self):
        """Lazily initialize the RAG tool."""
        if self._rag_tool is None:
            from agent.tools.rag_tool import RAGTool
            self._rag_tool = RAGTool(
                docs_dir=self._docs_dir,
                vectorstore_dir=self._vectorstore_dir,
                verbose=self.verbose,
            )
            self._log("RAG Tool initialized")
        return self._rag_tool

    def _get_code_tool(self):
        """Lazily initialize the Code tool."""
        if self._code_tool is None:
            from agent.tools.code_tool import CodeTool
            self._code_tool = CodeTool(verbose=self.verbose)
            self._log("Code Tool initialized")
        return self._code_tool

    # -- Logging -----------------------------------------------------------

    def _log(self, msg: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [Agent] {msg}")

    # -- Graph construction ------------------------------------------------

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph.

        Graph structure:
          START -> router -> {sql_node, rag_node, code_node,
                              multi_node, direct_node}
                          -> synthesizer -> END

        Returns:
            Compiled StateGraph.
        """
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("router", self._router_node)
        graph.add_node("sql_node", self._sql_node)
        graph.add_node("rag_node", self._rag_node)
        graph.add_node("code_node", self._code_node)
        graph.add_node("multi_node", self._multi_node)
        graph.add_node("direct_node", self._direct_node)
        graph.add_node("synthesizer", self._synthesizer_node)

        # Set entry point
        graph.set_entry_point("router")

        # Conditional edges from router
        graph.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "sql": "sql_node",
                "rag": "rag_node",
                "code": "code_node",
                "multi": "multi_node",
                "direct": "direct_node",
            },
        )

        # All tool nodes -> synthesizer
        graph.add_edge("sql_node", "synthesizer")
        graph.add_edge("rag_node", "synthesizer")
        graph.add_edge("code_node", "synthesizer")
        graph.add_edge("multi_node", "synthesizer")
        graph.add_edge("direct_node", "synthesizer")

        # Synthesizer -> END
        graph.add_edge("synthesizer", END)

        return graph.compile()

    # -- Routing -----------------------------------------------------------

    def _route_decision(self, state: AgentState) -> str:
        """Extract the routing decision from state.

        Args:
            state: Current agent state.

        Returns:
            Route key string ("sql", "rag", "code", "multi", "direct").
        """
        return state.get("route", "direct")

    def _router_node(self, state: AgentState) -> AgentState:
        """Classify the question and decide which tool to use.

        Uses the LLM to analyze the question and route it to
        the appropriate tool node.

        Args:
            state: Current agent state with the question.

        Returns:
            Updated state with route and route_reasoning.
        """
        question = state["question"]
        self._log(f"Routing: \"{question[:80]}...\"" if len(question) > 80
                  else f"Routing: \"{question}\"")

        # Build history context
        history_ctx = ""
        if self._chat_history:
            recent = self._chat_history[-6:]  # last 3 exchanges
            history_lines = []
            for msg in recent:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                history_lines.append(f"{role}: {msg.content[:150]}")
            history_ctx = "Recent conversation:\n" + "\n".join(history_lines)

        # Build dynamic list of database tables
        try:
            sql_tool = self._get_sql_tool()
            tables = sql_tool.get_table_names()
            database_tables = ", ".join(tables)
        except Exception:
            database_tables = "orders, products, customers, returns"

        active_doc = state.get("active_document") or "None (General Chat)"

        # Generate doc-type-specific routing instructions
        doc_routing_instruction = ""
        if active_doc and active_doc != "None (General Chat)":
            from pathlib import Path
            ext = Path(active_doc).suffix.lower()
            if ext in (".csv", ".xlsx", ".xls"):
                import re
                stem = Path(active_doc).stem.lower()
                stem_clean = re.sub(r"[^a-z0-9_]", "_", stem).strip("_")
                stem_clean = re.sub(r"_+", "_", stem_clean)
                # Match file_processor._sanitize_table_name: add t_ prefix if starts with digit
                if not stem_clean or not stem_clean[0].isalpha():
                    stem_clean = "t_" + stem_clean
                stem_clean = stem_clean[:50]
                
                try:
                    sql_tool = self._get_sql_tool()
                    all_tables = sql_tool.get_table_names()
                    matching = [t for t in all_tables if t == stem_clean or t.startswith(f"{stem_clean}_")]
                except Exception:
                    matching = []
                
                if matching:
                    doc_routing_instruction = (
                        f"CRITICAL DOCUMENT ROUTING RULE: The active document '{active_doc}' is a SPREADSHEET loaded into "
                        f"database table(s): {', '.join(matching)}. Any questions asking about contents of, lists in, "
                        f"or queries on this document MUST be routed to SQL (to query the tables) or CODE (to process/visualize). "
                        "Do NOT route queries about this spreadsheet to RAG."
                    )
                else:
                    doc_routing_instruction = (
                        f"CRITICAL DOCUMENT ROUTING RULE: The active document '{active_doc}' is a spreadsheet. "
                        "Ensure queries about it are routed to SQL or CODE, NOT RAG."
                    )
            else:
                doc_routing_instruction = (
                    f"CRITICAL DOCUMENT ROUTING RULE: The active document '{active_doc}' is a TEXT document (PDF/Doc/Text) indexed in RAG. "
                    "All questions seeking summaries, searches, or text contents from this document must be routed to RAG."
                )

        # If it is a spreadsheet, RAG has no access to it, so we mask active_document for RAG template parameter
        rag_active_doc = active_doc
        if active_doc and active_doc != "None (General Chat)":
            from pathlib import Path
            if Path(active_doc).suffix.lower() in (".csv", ".xlsx", ".xls"):
                rag_active_doc = "None (Spreadsheets are loaded into SQL tables, not RAG)"

        prompt = ROUTER_PROMPT.format(
            question=question,
            history_context=history_ctx,
            database_tables=database_tables,
            active_document=rag_active_doc,
            doc_routing_instruction=doc_routing_instruction,
        )

        try:
            response = self._llm.invoke([HumanMessage(content=prompt)])
            text = response.content.strip()

            # Parse ROUTE and REASON
            route = "direct"
            reason = "Default routing"

            for line in text.split("\n"):
                line = line.strip()
                if line.upper().startswith("ROUTE:"):
                    route_val = line.split(":", 1)[1].strip().lower()
                    # Normalize
                    if route_val in ("sql", "database", "db", "query"):
                        route = "sql"
                    elif route_val in ("rag", "document", "doc", "pdf"):
                        route = "rag"
                    elif route_val in ("code", "python", "compute", "chart",
                                       "calculate", "visualize"):
                        route = "code"
                    elif route_val in ("multi", "multiple", "combined",
                                       "multi-hop", "multi_hop"):
                        route = "multi"
                    elif route_val in ("direct", "none", "general"):
                        route = "direct"
                    else:
                        route = "direct"
                elif line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            self._log(f"Route -> {route.upper()} ({reason})")

        except Exception as e:
            route = "direct"
            reason = f"Router error: {e}"
            self._log(f"[!] Router failed: {e}, defaulting to DIRECT")

        return {
            **state,
            "route": route,
            "route_reasoning": reason,
            "tools_used": [],
            "sources": [],
            "figures": [],
            "dataframes": [],
        }

    # -- Tool Nodes --------------------------------------------------------

    def _sql_node(self, state: AgentState) -> AgentState:
        """Execute the SQL tool for database queries.

        Args:
            state: Current state with the question.

        Returns:
            Updated state with sql_result.
        """
        question = state["question"]
        doc = state.get("active_document")
        self._log(f"Executing SQL Tool ... (active doc: {doc})")

        # Find tables matching active_document
        active_tables = []
        if doc:
            try:
                import re
                from pathlib import Path
                stem = Path(doc).stem.lower()
                stem_clean = re.sub(r"[^a-z0-9_]", "_", stem).strip("_")
                stem_clean = re.sub(r"_+", "_", stem_clean)
                # Match file_processor._sanitize_table_name: add t_ prefix if starts with digit
                if not stem_clean or not stem_clean[0].isalpha():
                    stem_clean = "t_" + stem_clean
                stem_clean = stem_clean[:50]

                sql_tool = self._get_sql_tool()
                all_tables = sql_tool.get_table_names()

                # Check for direct match or prefix match
                for t in all_tables:
                    if t == stem_clean or t.startswith(f"{stem_clean}_"):
                        active_tables.append(t)
            except Exception as ex:
                self._log(f"[WARN] Error matching active tables: {ex}")

        try:
            sql_tool = self._get_sql_tool()
            result = sql_tool.run(question, active_tables=active_tables or None, chat_history=state.get("chat_history"))

            # Extract data from the DataFrame
            data_list = []
            col_list = []
            if result.dataframe is not None and not result.dataframe.empty:
                data_list = result.dataframe.head(20).values.tolist()
                col_list = result.dataframe.columns.tolist()

            sql_result = {
                "success": result.success,
                "answer": result.explanation if result.success else result.error,
                "sql": result.sql_query,
                "data": data_list,
                "columns": col_list,
                "row_count": result.row_count,
            }

            tools_used = state.get("tools_used", []) + ["SQL"]
            self._log(f"SQL: {'OK' if result.success else 'FAIL'} "
                      f"({result.row_count} rows)")

            return {**state, "sql_result": sql_result, "tools_used": tools_used}

        except Exception as e:
            self._log(f"SQL Error: {e}")
            return {
                **state,
                "sql_result": {"success": False, "answer": str(e)},
                "tools_used": state.get("tools_used", []) + ["SQL"],
            }

    def _rag_node(self, state: AgentState) -> AgentState:
        """Execute the RAG tool for document Q&A.

        Args:
            state: Current state with the question.

        Returns:
            Updated state with rag_result.
        """
        question = state["question"]
        self._log("Executing RAG Tool ...")

        try:
            rag_tool = self._get_rag_tool()
            result = rag_tool.run(question, active_document=state.get("active_document"))

            rag_result = {
                "success": result.success,
                "answer": result.answer,
                "sources": result.sources,
                "confidence": result.confidence,
                "n_chunks": result.n_chunks_used,
            }

            tools_used = state.get("tools_used", []) + ["RAG"]
            sources = state.get("sources", []) + result.sources
            self._log(f"RAG: {'OK' if result.success else 'FAIL'} "
                      f"(confidence={result.confidence}%)")

            return {
                **state,
                "rag_result": rag_result,
                "tools_used": tools_used,
                "sources": sources,
            }

        except Exception as e:
            self._log(f"RAG Error: {e}")
            return {
                **state,
                "rag_result": {"success": False, "answer": str(e)},
                "tools_used": state.get("tools_used", []) + ["RAG"],
            }

    def _code_node(self, state: AgentState) -> AgentState:
        """Execute the Code tool for computation/charts.

        Args:
            state: Current state with the question.

        Returns:
            Updated state with code_result, figures, dataframes.
        """
        question = state["question"]
        self._log("Executing Code Tool ...")

        # Build data context from prior SQL results if available
        data_context = {}
        sql_result = state.get("sql_result")
        if sql_result and sql_result.get("success") and sql_result.get("data"):
            import pandas as pd_module
            try:
                df = pd_module.DataFrame(
                    sql_result["data"],
                    columns=sql_result["columns"],
                )
                data_context["query_result"] = df
            except Exception:
                pass

        try:
            code_tool = self._get_code_tool()
            result = code_tool.run(question, data_context=data_context or None)

            code_result = {
                "success": result.success,
                "answer": result.output if result.success else result.error,
                "explanation": result.explanation,
                "code": result.code,
                "retries": result.retries_used,
            }

            tools_used = state.get("tools_used", []) + ["CODE"]
            figures = state.get("figures", []) + result.figures
            dataframes = state.get("dataframes", []) + result.dataframes

            self._log(f"Code: {'OK' if result.success else 'FAIL'} "
                      f"({len(result.figures)} figures)")

            return {
                **state,
                "code_result": code_result,
                "tools_used": tools_used,
                "figures": figures,
                "dataframes": dataframes,
            }

        except Exception as e:
            self._log(f"Code Error: {e}")
            return {
                **state,
                "code_result": {"success": False, "answer": str(e)},
                "tools_used": state.get("tools_used", []) + ["CODE"],
            }

    def _multi_node(self, state: AgentState) -> AgentState:
        """Handle multi-hop queries requiring multiple tools.

        Plans and executes a sequence of tool calls, passing
        results between steps.

        Args:
            state: Current state with the question.

        Returns:
            Updated state with results from all tools used.
        """
        question = state["question"]
        self._log("Planning multi-hop query ...")

        # Get the execution plan from LLM
        try:
            prompt = MULTI_PLAN_PROMPT.format(question=question)
            response = self._llm.invoke([HumanMessage(content=prompt)])
            plan_text = response.content.strip()
            self._log(f"Plan:\n    {plan_text.replace(chr(10), chr(10) + '    ')}")
        except Exception as e:
            self._log(f"Planning failed: {e}")
            plan_text = "STEP 1: [SQL] Query the database for relevant data"

        # Parse steps
        steps = []
        for line in plan_text.split("\n"):
            line = line.strip()
            if line.upper().startswith("STEP"):
                # Extract tool and description
                if "[SQL]" in line.upper():
                    steps.append({"tool": "sql", "desc": line})
                elif "[RAG]" in line.upper():
                    steps.append({"tool": "rag", "desc": line})
                elif "[CODE]" in line.upper():
                    steps.append({"tool": "code", "desc": line})

        if not steps:
            steps = [{"tool": "sql", "desc": "Query database"}]

        # Execute each step sequentially
        current_state = {**state, "multi_steps": steps}

        for i, step in enumerate(steps, 1):
            self._log(f"Multi-hop step {i}/{len(steps)}: {step['tool'].upper()}")

            if step["tool"] == "sql":
                current_state = self._sql_node(current_state)
            elif step["tool"] == "rag":
                current_state = self._rag_node(current_state)
            elif step["tool"] == "code":
                current_state = self._code_node(current_state)

        return current_state

    def _direct_node(self, state: AgentState) -> AgentState:
        """Handle questions that can be answered directly by the LLM.

        Args:
            state: Current state with the question.

        Returns:
            Updated state with the direct answer.
        """
        question = state["question"]
        self._log("Answering directly (no tool needed)")

        active_doc = state.get("active_document") or "None"
        try:
            messages = [
                SystemMessage(content=(
                    f"You are a helpful data analyst assistant. The active document in this chat session is: '{active_doc}'.\n"
                    "Answer the user's question or greeting directly.\n"
                    "If the user asks about the active document or says they provided/uploaded a document, inform them that the document is loaded and active in this session, and explain how you can help them analyze it.\n"
                    "Specifically, if the active document is a spreadsheet (.csv, .xlsx, .xls), explain that it is loaded into the SQLite database and you can write SQL queries to search, list, filter, or calculate its columns.\n"
                    "If it is a text document (PDF/Word/Text), explain that it is indexed in RAG and you can search its textual contents.\n"
                    "If the user is giving a brief acknowledgment (like 'ok', 'thanks', 'cool', 'got it') or feedback (like 'you did correct'), "
                    "just respond politely, acknowledge their comment, and invite them to ask more questions about the active document or data.\n"
                    "Do NOT say that you don't have access to the document or that you don't see it, as it is already active in this session.\n"
                    "If they're asking about your capabilities, explain that you can query databases (SQL), search documents (RAG), write & execute Python code, and create visualizations."
                )),
            ]
            # Add chat history
            messages.extend(self._chat_history[-6:])
            messages.append(HumanMessage(content=question))

            response = self._llm.invoke(messages)
            answer = response.content

            return {
                **state,
                "answer": answer,
                "tools_used": ["DIRECT"],
                "confidence": 90,
            }
        except Exception as e:
            return {
                **state,
                "answer": f"I encountered an error: {e}",
                "tools_used": ["DIRECT"],
            }

    # -- Synthesizer -------------------------------------------------------

    def _synthesizer_node(self, state: AgentState) -> AgentState:
        """Synthesize results from tool nodes into a final answer.

        Combines outputs from all tools used and generates a
        coherent, well-structured response.

        Args:
            state: Current state with tool results.

        Returns:
            Updated state with final answer and confidence.
        """
        # If direct answer already set, skip synthesis
        if state.get("answer") and "DIRECT" in state.get("tools_used", []):
            return state

        question = state["question"]
        tools_used = state.get("tools_used", [])
        self._log(f"Synthesizing results from: {tools_used}")

        # Collect tool results
        result_parts = []

        sql_result = state.get("sql_result")
        if sql_result and sql_result.get("success"):
            result_parts.append(
                f"DATABASE QUERY RESULT:\n"
                f"SQL: {sql_result.get('sql', 'N/A')}\n"
                f"Answer: {sql_result.get('answer', 'No data')}\n"
                f"Rows returned: {sql_result.get('row_count', 0)}\n"
                f"Data: {sql_result.get('data', [])[:5]}"
            )

        rag_result = state.get("rag_result")
        if rag_result and rag_result.get("success"):
            result_parts.append(
                f"DOCUMENT SEARCH RESULT:\n"
                f"Answer: {rag_result.get('answer', 'No data')}\n"
                f"Sources: {', '.join(rag_result.get('sources', []))}\n"
                f"Confidence: {rag_result.get('confidence', 0)}%"
            )

        code_result = state.get("code_result")
        if code_result and code_result.get("success"):
            result_parts.append(
                f"CODE EXECUTION RESULT:\n"
                f"Output: {code_result.get('answer', 'No output')}\n"
                f"Explanation: {code_result.get('explanation', 'N/A')}\n"
                f"Charts generated: {len(state.get('figures', []))}"
            )

        if not result_parts:
            # All tools failed
            error_msgs = []
            if sql_result and not sql_result.get("success"):
                error_msgs.append(f"SQL: {sql_result.get('answer', 'failed')}")
            if rag_result and not rag_result.get("success"):
                error_msgs.append(f"RAG: {rag_result.get('answer', 'failed')}")
            if code_result and not code_result.get("success"):
                error_msgs.append(f"Code: {code_result.get('answer', 'failed')}")

            return {
                **state,
                "answer": (
                    "I wasn't able to find a complete answer. "
                    f"Errors: {'; '.join(error_msgs)}"
                ),
                "confidence": 10,
            }

        # Synthesize with LLM
        try:
            tool_results_text = "\n\n---\n\n".join(result_parts)
            prompt = SYNTHESIZE_PROMPT.format(
                question=question,
                tool_results=tool_results_text,
            )

            response = self._llm.invoke([
                SystemMessage(content="You are a professional data analyst."),
                HumanMessage(content=prompt),
            ])

            answer = response.content

            # Compute confidence
            confidence = self._compute_confidence(state)

            self._log(f"Synthesis complete (confidence={confidence}%)")

            return {
                **state,
                "answer": answer,
                "confidence": confidence,
            }

        except Exception as e:
            # Fallback: concatenate raw results
            self._log(f"Synthesis failed: {e}, using raw results")
            fallback = "\n\n".join(
                r.get("answer", "") for r in [sql_result, rag_result, code_result]
                if r and r.get("success")
            )
            return {
                **state,
                "answer": fallback or f"Error synthesizing results: {e}",
                "confidence": 30,
            }

    def _compute_confidence(self, state: AgentState) -> int:
        """Compute overall confidence from tool results.

        Args:
            state: Current agent state.

        Returns:
            Confidence score 0-100.
        """
        scores = []

        sql_result = state.get("sql_result")
        if sql_result and sql_result.get("success"):
            scores.append(85)

        rag_result = state.get("rag_result")
        if rag_result and rag_result.get("success"):
            scores.append(rag_result.get("confidence", 70))

        code_result = state.get("code_result")
        if code_result and code_result.get("success"):
            scores.append(80)

        if not scores:
            return 10

        return int(sum(scores) / len(scores))

    # -- Public API --------------------------------------------------------

    def run(self, question: str, active_document: str = None, chat_history: list = None) -> dict[str, Any]:
        """Run the agent on a user question.

        Args:
            question: Natural language question.
            active_document: Optional active document name.
            chat_history: Optional list of LangChain message objects to load.

        Returns:
            Dict with answer, sources, figures, confidence, etc.
        """
        start = time.time()
        self._log(f"Question: {question} (active doc: {active_document})")

        # Load chat history if provided
        if chat_history is not None:
            self._chat_history = list(chat_history)

        # Build initial state
        initial_state: AgentState = {
            "question": question,
            "route": "",
            "route_reasoning": "",
            "answer": "",
            "sources": [],
            "figures": [],
            "dataframes": [],
            "confidence": 0,
            "error": "",
            "tools_used": [],
            "chat_history": list(self._chat_history[-6:]),
            "active_document": active_document,
        }

        # Run the graph
        try:
            final_state = self._graph.invoke(initial_state)
        except Exception as e:
            self._log(f"[FAIL] Graph execution error: {e}")
            final_state = {
                **initial_state,
                "answer": f"An error occurred: {e}",
                "error": str(e),
                "confidence": 0,
            }

        # Update chat history
        self._chat_history.append(HumanMessage(content=question))
        self._chat_history.append(
            AIMessage(content=final_state.get("answer", ""))
        )

        # Keep history manageable (last 20 messages)
        if len(self._chat_history) > 20:
            self._chat_history = self._chat_history[-20:]

        execution_time = time.time() - start
        final_state["execution_time"] = execution_time
        self._log(f"Done in {execution_time:.2f}s")

        return dict(final_state)

    def clear_memory(self) -> None:
        """Clear conversation history."""
        self._chat_history.clear()
        self._log("Memory cleared")

    def get_memory(self) -> list:
        """Get current conversation history.

        Returns:
            List of LangChain message objects.
        """
        return list(self._chat_history)
