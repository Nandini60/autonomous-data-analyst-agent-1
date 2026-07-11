"""
Streamlit UI -- Autonomous Data Analyst Agent
================================================
Premium, dark-themed chat interface for interacting with the
autonomous data analyst agent.

Features:
  * Chat interface with conversation history
  * Plotly chart rendering
  * Source citation display
  * Confidence score indicator
  * Tool routing badge display
  * Sidebar with system info and controls

Usage:
    streamlit run app.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Autonomous Data Analyst Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for premium dark theme
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }

    .main-header h1 {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
    }

    /* Chat messages */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 12px rgba(102, 126, 234, 0.25);
    }

    .agent-msg {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e0e0e0;
        padding: 1rem 1.2rem;
        border-radius: 16px 16px 16px 4px;
        margin: 0.5rem 0;
        max-width: 85%;
        backdrop-filter: blur(10px);
    }

    /* Tool badges */
    .tool-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
        letter-spacing: 0.03em;
    }

    .badge-sql {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    .badge-rag {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .badge-code {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-multi {
        background: rgba(139, 92, 246, 0.2);
        color: #a78bfa;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }

    .badge-direct {
        background: rgba(156, 163, 175, 0.2);
        color: #9ca3af;
        border: 1px solid rgba(156, 163, 175, 0.3);
    }

    /* Confidence indicator */
    .confidence-bar {
        height: 6px;
        border-radius: 3px;
        background: rgba(255, 255, 255, 0.1);
        overflow: hidden;
        margin: 0.5rem 0;
    }

    .confidence-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }

    .conf-high { background: linear-gradient(90deg, #10b981, #34d399); }
    .conf-med { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .conf-low { background: linear-gradient(90deg, #ef4444, #f87171); }

    /* Source tags */
    .source-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.7rem;
        margin: 0.15rem;
        color: #9ca3af;
    }

    /* Stats cards */
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        backdrop-filter: blur(10px);
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
    }

    .stat-label {
        font-size: 0.75rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Sidebar */
    .sidebar-section {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animate-in {
        animation: fadeIn 0.3s ease-out;
    }

    /* SQL code display */
    .sql-display {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 0.8rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.8rem;
        color: #60a5fa;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def init_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "total_queries" not in st.session_state:
        st.session_state.total_queries = 0
    if "total_charts" not in st.session_state:
        st.session_state.total_charts = 0
    if "agent_ready" not in st.session_state:
        st.session_state.agent_ready = False
    if "uploaded_tables" not in st.session_state:
        st.session_state.uploaded_tables = []


def load_agent():
    """Initialize the agent (cached in session state)."""
    if st.session_state.agent is None:
        try:
            from agent.graph import DataAnalystAgent

            # Use data paths
            db_path = "data/database.db"
            docs_dir = "data/docs"

            # Generate data if not present
            if not Path(db_path).exists():
                from utils.generate_data import generate_all
                from utils.db_loader import load_csvs_to_sqlite
                generate_all(data_dir="data")
                load_csvs_to_sqlite(data_dir="data", db_path=db_path)

            if not Path(docs_dir).exists() or not list(Path(docs_dir).glob("*.pdf")):
                from utils.generate_docs import generate_all_docs
                generate_all_docs(outdir=docs_dir)

            st.session_state.agent = DataAnalystAgent(
                db_path=db_path,
                docs_dir=docs_dir,
                verbose=False,
            )
            st.session_state.agent_ready = True
        except Exception as e:
            st.error(f"❌ Failed to initialize agent: {e}")
            st.session_state.agent_ready = False


# ---------------------------------------------------------------------------
# UI Helper functions
# ---------------------------------------------------------------------------

def get_tool_badge(tool: str) -> str:
    """Return HTML for a tool badge."""
    badge_class = {
        "SQL": "badge-sql",
        "RAG": "badge-rag",
        "CODE": "badge-code",
        "MULTI": "badge-multi",
        "DIRECT": "badge-direct",
    }.get(tool, "badge-direct")

    icons = {
        "SQL": "🗄️",
        "RAG": "📄",
        "CODE": "🐍",
        "MULTI": "🔗",
        "DIRECT": "💬",
    }

    return f'<span class="tool-badge {badge_class}">{icons.get(tool, "⚡")} {tool}</span>'


def get_confidence_html(confidence: int) -> str:
    """Return HTML for a confidence indicator."""
    if confidence >= 70:
        cls = "conf-high"
    elif confidence >= 40:
        cls = "conf-med"
    else:
        cls = "conf-low"

    return f"""
    <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
        <span style="font-size:0.75rem;color:#9ca3af;">Confidence:</span>
        <div class="confidence-bar" style="flex:1;max-width:120px;">
            <div class="confidence-fill {cls}" style="width:{confidence}%"></div>
        </div>
        <span style="font-size:0.75rem;color:#9ca3af;">{confidence}%</span>
    </div>
    """


def render_sources(sources: list[str]) -> str:
    """Render source citation tags."""
    if not sources:
        return ""
    tags = "".join(f'<span class="source-tag">📎 {s}</span>' for s in sources[:5])
    return f'<div style="margin-top:6px;">{tags}</div>'


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render the sidebar with system info and controls."""
    with st.sidebar:
        st.markdown("### 🤖 Agent Controls")

        # System status
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        if st.session_state.agent_ready:
            st.success("✅ Agent Online")
        else:
            st.warning("⏳ Initializing...")
        st.markdown('</div>', unsafe_allow_html=True)

        # Stats
        st.markdown("### 📊 Session Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries", st.session_state.total_queries)
        with col2:
            st.metric("Charts", st.session_state.total_charts)

        st.divider()

        # Example queries
        st.markdown("### 💡 Try These Queries")

        examples = {
            "🗄️ SQL": [
                "How many orders are there?",
                "Top 5 products by profit",
                "Total sales by region",
            ],
            "📄 RAG": [
                "What is the return policy for furniture?",
                "What are the 2024 sales targets?",
                "Q1 revenue performance",
            ],
            "🐍 Code": [
                "Calculate CAGR from 10K to 25K over 5 years",
                "Create a pie chart of sales by segment",
            ],
            "🔗 Multi-hop": [
                "Get sales by category and create a chart",
            ],
        }

        for category, queries in examples.items():
            st.markdown(f"**{category}**")
            for q in queries:
                if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
                    st.session_state.example_query = q
                    st.rerun()

        st.divider()

        # --- CSV Upload ---
        st.markdown("### 📂 Upload Your Data")
        uploaded_file = st.file_uploader(
            "Drop a CSV file to add it to the database",
            type=["csv"],
            help="The CSV will be loaded as a new table. You can then query it with natural language!",
        )

        if uploaded_file is not None:
            import pandas as pd
            import re as _re

            # Read the uploaded file
            try:
                df_preview = pd.read_csv(uploaded_file)
                uploaded_file.seek(0)  # Reset for later read

                # Auto-suggest table name from filename
                raw_name = Path(uploaded_file.name).stem
                default_name = _re.sub(r'[^a-z0-9_]', '_', raw_name.lower()).strip('_')
                default_name = _re.sub(r'_+', '_', default_name)  # collapse multi-underscores

                table_name = st.text_input(
                    "Table name",
                    value=default_name,
                    help="This will be the SQL table name. Use lowercase with underscores.",
                    key="csv_table_name",
                )

                # Preview
                st.markdown(f"**Preview** — {len(df_preview):,} rows × {len(df_preview.columns)} cols")
                st.dataframe(df_preview.head(10), use_container_width=True, height=200)

                # Column types
                with st.expander("📋 Detected Columns"):
                    col_info = pd.DataFrame({
                        "Column": df_preview.columns,
                        "Type": [str(dt) for dt in df_preview.dtypes],
                        "Non-Null": [f"{df_preview[c].notna().sum()}/{len(df_preview)}" for c in df_preview.columns],
                        "Sample": [str(df_preview[c].dropna().iloc[0])[:40] if df_preview[c].notna().any() else "—" for c in df_preview.columns],
                    })
                    st.dataframe(col_info, use_container_width=True, hide_index=True)

                # Validate table name
                valid_name = bool(_re.match(r'^[a-z][a-z0-9_]*$', table_name)) and len(table_name) >= 2
                if not valid_name:
                    st.warning("⚠️ Table name must start with a letter, use only `a-z`, `0-9`, `_`, and be ≥ 2 chars.")

                # Load button
                if st.button(
                    f"📥 Load into database as `{table_name}`",
                    use_container_width=True,
                    disabled=not valid_name,
                    type="primary",
                ):
                    with st.spinner(f"Loading {len(df_preview):,} rows into `{table_name}`..."):
                        try:
                            # Save temp CSV
                            temp_path = Path("data") / f"_upload_{table_name}.csv"
                            temp_path.parent.mkdir(parents=True, exist_ok=True)
                            df_preview.to_csv(temp_path, index=False)

                            # Ingest into SQLite
                            from utils.db_loader import load_custom_csv_to_sqlite
                            col_types = load_custom_csv_to_sqlite(
                                csv_path=str(temp_path),
                                table_name=table_name,
                                db_path="data/database.db",
                            )

                            # Clean up temp file
                            temp_path.unlink(missing_ok=True)

                            # Track uploaded tables
                            if "uploaded_tables" not in st.session_state:
                                st.session_state.uploaded_tables = []
                            st.session_state.uploaded_tables.append({
                                "name": table_name,
                                "rows": len(df_preview),
                                "cols": len(df_preview.columns),
                                "columns": list(df_preview.columns),
                            })

                            # Force agent to reinitialize SQL tool so it picks up new tables
                            if st.session_state.agent:
                                st.session_state.agent._sql_tool = None

                            st.success(
                                f"✅ Loaded **{len(df_preview):,} rows** into "
                                f"table `{table_name}` ({len(col_types)} columns).\n\n"
                                f"Try asking: *\"Show me the first 5 rows from {table_name}\"*"
                            )
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Failed to load CSV: {e}")

            except Exception as e:
                st.error(f"❌ Could not read CSV file: {e}")

        # Show uploaded tables
        if st.session_state.get("uploaded_tables"):
            st.markdown("**📊 Your Tables:**")
            for tbl in st.session_state.uploaded_tables:
                st.markdown(
                    f"- `{tbl['name']}` — {tbl['rows']:,} rows, {tbl['cols']} cols"
                )

        st.divider()

        # Export PDF
        st.markdown("### 📥 Export")
        if st.button("📄 Export Chat as PDF", use_container_width=True):
            from agent.extras import ReportExporter
            exporter = ReportExporter()
            output = exporter.export(
                st.session_state.messages,
                filename="data/analysis_report.pdf",
            )
            if output:
                with open(output, "rb") as f:
                    st.download_button(
                        "⬇️ Download PDF",
                        data=f.read(),
                        file_name="analysis_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.warning("PDF export requires fpdf2")

        st.divider()

        # DB Schema
        st.markdown("### 🗄️ Database Schema")
        with st.expander("View Schema"):
            from agent.extras import SchemaDiscovery
            try:
                schema = SchemaDiscovery(db_path="data/database.db")
                st.code(schema.get_schema(), language="text")
            except Exception:
                st.info("Schema unavailable — generate data first.")

        st.divider()

        # Clear chat
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.total_queries = 0
            st.session_state.total_charts = 0
            st.session_state.uploaded_tables = []
            if st.session_state.agent:
                st.session_state.agent.clear_memory()
            st.rerun()

        # About section
        st.divider()
        st.markdown("### ℹ️ About")
        st.markdown("""
        **Autonomous Data Analyst Agent**

        Built with:
        - 🧠 LangGraph (Agent Framework)
        - ⚡ Groq (LLM - Llama 3.3 70B)
        - 🔍 ChromaDB (Vector Store)
        - 📊 Plotly (Charts)
        - 🛡️ Guardrails (PII + Injection)
        """)


# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

def render_chat():
    """Render the main chat area."""
    # Header
    st.markdown("""
    <div class="main-header animate-in">
        <h1>🤖 Autonomous Data Analyst Agent</h1>
        <p>Ask questions about sales data, documents, or request calculations & charts</p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])

                # Show metadata if available
                meta = msg.get("metadata", {})

                # Tool badges
                tools = meta.get("tools_used", [])
                if tools:
                    badges = " ".join(get_tool_badge(t) for t in tools)
                    st.markdown(badges, unsafe_allow_html=True)

                # Confidence
                conf = meta.get("confidence", 0)
                if conf > 0:
                    st.markdown(get_confidence_html(conf), unsafe_allow_html=True)

                # SQL query
                sql = meta.get("sql")
                if sql:
                    with st.expander("🔍 SQL Query"):
                        st.code(sql, language="sql")

                # Sources
                sources = meta.get("sources", [])
                if sources:
                    st.markdown(render_sources(sources), unsafe_allow_html=True)

                # Figures
                figures = meta.get("figures", [])
                for fig in figures:
                    st.plotly_chart(fig, use_container_width=True)

                # Execution time
                exec_time = meta.get("execution_time", 0)
                if exec_time:
                    st.caption(f"⏱️ {exec_time:.1f}s")


def process_query(query: str):
    """Process a user query through the agent."""
    if not st.session_state.agent:
        st.error("Agent not initialized. Please check your API key.")
        return

    # --- Guardrails: validate input ---
    from agent.extras import Guardrails
    validation = Guardrails.validate(query)

    if not validation["is_safe"]:
        st.session_state.messages.append({"role": "user", "content": query})
        blocked_msg = "🛡️ **Query blocked by safety guardrails.**\n\n"
        for w in validation["warnings"]:
            blocked_msg += f"- {w}\n"
        st.session_state.messages.append({
            "role": "assistant", "content": blocked_msg, "metadata": {},
        })
        return

    # Show guardrail warnings (non-blocking)
    if validation["warnings"]:
        for w in validation["warnings"]:
            st.toast(w, icon="⚠️")

    query = validation["sanitized_query"]

    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})

    # Show user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    # Process with agent
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🧠 Thinking..."):
            try:
                result = st.session_state.agent.run(query)

                answer = result.get("answer", "I couldn't generate a response.")
                st.markdown(answer)

                # Tool badges
                tools = result.get("tools_used", [])
                if tools:
                    badges = " ".join(get_tool_badge(t) for t in tools)
                    st.markdown(badges, unsafe_allow_html=True)

                # Enhanced confidence scoring
                from agent.extras import ConfidenceScorer
                conf_data = ConfidenceScorer.score(result)
                conf = conf_data["overall"]
                if conf > 0:
                    st.markdown(get_confidence_html(conf), unsafe_allow_html=True)

                # SQL
                sql_result = result.get("sql_result", {})
                sql = sql_result.get("sql") if sql_result else None
                if sql:
                    with st.expander("🔍 SQL Query"):
                        st.code(sql, language="sql")

                # Sources
                sources = result.get("sources", [])
                if sources:
                    st.markdown(render_sources(sources), unsafe_allow_html=True)

                # Figures
                figures = result.get("figures", [])
                for fig in figures:
                    st.plotly_chart(fig, use_container_width=True)

                # Auto-generate business insights for SQL results
                if sql_result and sql_result.get("success"):
                    with st.expander("💡 Business Insights"):
                        with st.spinner("Generating insights..."):
                            from agent.extras import InsightsGenerator
                            gen = InsightsGenerator()
                            insights = gen.generate(
                                question=query,
                                data=sql_result.get("data", []),
                            )
                            st.markdown(insights)

                # Execution time
                exec_time = result.get("execution_time", 0)
                if exec_time:
                    st.caption(f"⏱️ {exec_time:.1f}s")

                # Store message with metadata
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "metadata": {
                        "tools_used": tools,
                        "confidence": conf,
                        "sql": sql,
                        "sources": sources,
                        "figures": figures,
                        "execution_time": exec_time,
                    },
                })

                # Update stats
                st.session_state.total_queries += 1
                st.session_state.total_charts += len(figures)

            except Exception as e:
                error_msg = f"❌ An error occurred: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "metadata": {},
                })


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    """Main application entry point."""
    init_session_state()
    load_agent()

    render_sidebar()
    render_chat()

    # Handle example query from sidebar
    if "example_query" in st.session_state:
        query = st.session_state.pop("example_query")
        process_query(query)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask me anything about the data..."):
        process_query(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
