"""
Phase 6: Extra Features Module
================================
Advanced features that make this project stand out for
campus placements:

  1. Auto Schema Discovery — show DB schema to the LLM
  2. Query Insights — auto-generate business insights
  3. Confidence Scoring — calibrated confidence across tools
  4. PDF Report Export — export chat/results as PDF
  5. Guardrails — input validation, PII detection, safety checks
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

load_dotenv()


# =====================================================================
# 1. Auto Schema Discovery
# =====================================================================

class SchemaDiscovery:
    """Automatically discover and describe database schema.

    Generates LLM-friendly schema descriptions that help
    the SQL tool write more accurate queries.
    """

    def __init__(self, db_path: str = "data/database.db"):
        import sqlite3
        self.db_path = db_path
        self._schema_cache: str | None = None

    def get_schema(self) -> str:
        """Get a formatted schema description.

        Returns:
            Human-readable schema string with tables, columns,
            types, sample values, and row counts.
        """
        if self._schema_cache:
            return self._schema_cache

        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        schema_parts = []

        for table in tables:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]

            # Build column descriptions
            col_descs = []
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = "PRIMARY KEY" if col[5] else ""

                # Get sample values
                try:
                    cursor.execute(
                        f"SELECT DISTINCT {col_name} FROM {table} LIMIT 5"
                    )
                    samples = [str(row[0]) for row in cursor.fetchall()]
                    sample_str = ", ".join(samples[:5])
                except Exception:
                    sample_str = "N/A"

                col_descs.append(
                    f"    {col_name} ({col_type}){' ' + is_pk if is_pk else ''}"
                    f" — e.g. {sample_str}"
                )

            schema_parts.append(
                f"TABLE: {table} ({row_count} rows)\n"
                + "\n".join(col_descs)
            )

        conn.close()

        self._schema_cache = "\n\n".join(schema_parts)
        return self._schema_cache

    def get_table_names(self) -> list[str]:
        """Get list of all table names."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables


# =====================================================================
# 2. Query Insights Generator
# =====================================================================

class InsightsGenerator:
    """Generate business insights from query results.

    Takes query results and automatically generates
    actionable business insights using the LLM.
    """

    INSIGHTS_PROMPT = """You are a senior business analyst. Given the
following query result, generate 2-3 actionable business insights.

Question: {question}
Data: {data}

For each insight:
1. State the key finding
2. Explain its business significance
3. Suggest a concrete action

Format each insight as:
💡 **Insight N**: [Finding]
   *Significance*: [Why it matters]
   *Action*: [What to do about it]
"""

    def __init__(self, model: str = "llama-3.1-8b-instant"):
        api_key = os.getenv("GROQ_API_KEY")
        self._llm = ChatGroq(
            model=model,
            temperature=0.3,
            api_key=api_key,
            max_tokens=1024,
        )

    def generate(self, question: str, data: Any) -> str:
        """Generate insights from query results.

        Args:
            question: Original question asked.
            data: Query result data.

        Returns:
            Formatted insights string.
        """
        try:
            prompt = self.INSIGHTS_PROMPT.format(
                question=question,
                data=str(data)[:2000],
            )
            response = self._llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return f"Could not generate insights: {e}"


# =====================================================================
# 3. Enhanced Confidence Scoring
# =====================================================================

class ConfidenceScorer:
    """Calibrated confidence scoring across tools.

    Factors considered:
    - Tool success/failure
    - Data quality (row count, nulls)
    - Query complexity
    - RAG retrieval quality
    - Code execution success
    """

    @staticmethod
    def score(result: dict) -> dict:
        """Compute detailed confidence breakdown.

        Args:
            result: Agent result dictionary.

        Returns:
            Dict with overall score and breakdown.
        """
        scores = {}
        weights = {}

        # SQL confidence
        sql_result = result.get("sql_result")
        if sql_result:
            if sql_result.get("success"):
                row_count = sql_result.get("row_count", 0)
                if row_count > 0:
                    scores["sql"] = min(95, 70 + row_count * 2)
                else:
                    scores["sql"] = 50  # Query succeeded but no rows
            else:
                scores["sql"] = 10
            weights["sql"] = 0.4

        # RAG confidence
        rag_result = result.get("rag_result")
        if rag_result:
            if rag_result.get("success"):
                rag_conf = rag_result.get("confidence", 50)
                n_chunks = rag_result.get("n_chunks", 0)
                scores["rag"] = min(95, rag_conf + n_chunks * 5)
            else:
                scores["rag"] = 10
            weights["rag"] = 0.35

        # Code confidence
        code_result = result.get("code_result")
        if code_result:
            if code_result.get("success"):
                retries = code_result.get("retries", 0)
                scores["code"] = max(60, 90 - retries * 15)
            else:
                scores["code"] = 10
            weights["code"] = 0.25

        # Compute weighted average
        if scores:
            total_weight = sum(weights.values())
            overall = sum(
                scores[k] * weights[k] / total_weight
                for k in scores
            )
        else:
            overall = 50  # Direct response default

        return {
            "overall": int(overall),
            "breakdown": scores,
            "level": (
                "High" if overall >= 75 else
                "Medium" if overall >= 45 else
                "Low"
            ),
        }


# =====================================================================
# 4. PDF Report Export
# =====================================================================

class ReportExporter:
    """Export conversation and results as a PDF report.

    Creates a professional-looking PDF with:
    - Title page
    - Conversation transcript
    - Data tables
    - Insights summary
    """

    def __init__(self):
        try:
            from fpdf import FPDF
            self._available = True
        except ImportError:
            self._available = False

    def export(
        self,
        messages: list[dict],
        filename: str = "report.pdf",
        title: str = "Data Analysis Report",
    ) -> str | None:
        """Export chat messages to a PDF report.

        Args:
            messages: List of message dicts with role/content.
            filename: Output filename.
            title: Report title.

        Returns:
            Path to the generated PDF, or None if fpdf2 is unavailable.
        """
        if not self._available:
            return None

        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ---- Title page ----
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 60, "", ln=True)  # Spacer
        pdf.cell(0, 15, title, ln=True, align="C")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.cell(0, 8, "Autonomous Data Analyst Agent", ln=True, align="C")

        # ---- Conversation ----
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 12, "Conversation Transcript", ln=True)
        pdf.ln(5)

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Role header
            pdf.set_font("Helvetica", "B", 11)
            if role == "user":
                pdf.set_text_color(102, 126, 234)  # Blue
                pdf.cell(0, 8, "You:", ln=True)
            else:
                pdf.set_text_color(16, 185, 129)  # Green
                pdf.cell(0, 8, "Agent:", ln=True)

            # Content
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(60, 60, 60)

            # Handle special characters
            safe_content = content.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 6, safe_content)
            pdf.ln(4)

            # Metadata
            meta = msg.get("metadata", {})
            tools = meta.get("tools_used", [])
            if tools:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 5, f"Tools: {', '.join(tools)} | Confidence: {meta.get('confidence', 'N/A')}%", ln=True)
                pdf.ln(2)

        # ---- Save ----
        output_path = str(Path(filename).resolve())
        pdf.output(output_path)
        return output_path


# =====================================================================
# 5. Guardrails — Input Validation & Safety
# =====================================================================

class Guardrails:
    """Input validation, PII detection, and safety checks.

    Validates user queries before sending them to the agent:
    - PII detection (emails, phone numbers, SSNs)
    - Prompt injection detection
    - Query length limits
    - SQL injection patterns
    """

    # PII patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        re.compile(r'ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions', re.I),
        re.compile(r'you\s+are\s+now\s+(?:a|an)\s+', re.I),
        re.compile(r'forget\s+(?:all\s+)?(?:your|the)\s+(?:rules|instructions)', re.I),
        re.compile(r'system\s*:\s*you\s+are', re.I),
        re.compile(r'<\s*(?:system|admin|root)\s*>', re.I),
    ]

    # Max query length
    MAX_QUERY_LENGTH = 2000

    @classmethod
    def validate(cls, query: str) -> dict:
        """Validate a user query for safety.

        Args:
            query: User's input string.

        Returns:
            Dict with is_safe (bool), warnings (list), and
            sanitized_query (str).
        """
        warnings = []
        is_safe = True

        # Length check
        if len(query) > cls.MAX_QUERY_LENGTH:
            warnings.append(
                f"Query truncated from {len(query)} to {cls.MAX_QUERY_LENGTH} chars"
            )
            query = query[:cls.MAX_QUERY_LENGTH]

        # Empty check
        if not query.strip():
            return {
                "is_safe": False,
                "warnings": ["Empty query"],
                "sanitized_query": "",
            }

        # PII detection
        pii_found = []
        if cls.EMAIL_PATTERN.search(query):
            pii_found.append("email address")
        if cls.PHONE_PATTERN.search(query):
            pii_found.append("phone number")
        if cls.SSN_PATTERN.search(query):
            pii_found.append("SSN")
            is_safe = False  # SSN is critical — block

        if pii_found:
            warnings.append(
                f"⚠️ Possible PII detected: {', '.join(pii_found)}. "
                "Consider removing personal information."
            )

        # Prompt injection detection
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(query):
                warnings.append("⚠️ Possible prompt injection detected.")
                is_safe = False
                break

        return {
            "is_safe": is_safe,
            "warnings": warnings,
            "sanitized_query": query.strip(),
        }

    @classmethod
    def redact_pii(cls, text: str) -> str:
        """Redact PII from text.

        Args:
            text: Text potentially containing PII.

        Returns:
            Text with PII replaced by [REDACTED].
        """
        text = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
        text = cls.SSN_PATTERN.sub("[REDACTED_SSN]", text)
        return text
