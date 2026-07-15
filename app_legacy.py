"""
Streamlit UI v2 — Autonomous Data Analyst Agent
==================================================
Fully redesigned premium AI data-analysis platform.

Usage:  streamlit run app.py
"""

from __future__ import annotations

import base64, os, re as _re, sys, time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── Bootstrap ─────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv()

from auth.auth_manager import AuthManager
from chat_history.history_manager import ChatHistoryManager
from styles import (
    get_full_css, render_tool_badge, render_confidence_ring,
    render_source_tags, render_user_avatar,
)

st.set_page_config(
    page_title="AI Data Analyst", page_icon="🤖",
    layout="wide", initial_sidebar_state="expanded",
)

# ╔═══════════════════════════════════════════════════════════════╗
# ║  SESSION STATE                                                ║
# ╚═══════════════════════════════════════════════════════════════╝

def _boot():
    for k, v in dict(
        auth=False, user=None, profile=None, theme="dark",
        page="landing", sid=None, msgs=[], agent=None,
        ready=False, nq=0, nc=0,
    ).items():
        if k not in st.session_state:
            st.session_state[k] = v if not isinstance(v, list) else list(v)

@st.cache_resource
def _am(): return AuthManager()

@st.cache_resource
def _hm(): return ChatHistoryManager()

# ╔═══════════════════════════════════════════════════════════════╗
# ║  AGENT                                                        ║
# ╚═══════════════════════════════════════════════════════════════╝

def _agent_init():
    if st.session_state.agent is not None:
        return
    with st.spinner("🔄 Initialising AI engine — this may take a moment…"):
        try:
            from agent.graph import DataAnalystAgent
            db = str(ROOT / "data" / "database.db")
            dd = str(ROOT / "data" / "docs")
            if not Path(db).exists():
                from utils.generate_data import generate_all
                from utils.db_loader import load_csvs_to_sqlite
                generate_all(data_dir=str(ROOT / "data"))
                load_csvs_to_sqlite(data_dir=str(ROOT / "data"), db_path=db)
            if not Path(dd).exists() or not list(Path(dd).glob("*.pdf")):
                from utils.generate_docs import generate_all_docs
                generate_all_docs(outdir=dd)
            st.session_state.agent = DataAnalystAgent(db_path=db, docs_dir=dd, verbose=False)
            st.session_state.ready = True
        except Exception as e:
            st.error(f"❌ Agent error: {e}")

# ╔═══════════════════════════════════════════════════════════════╗
# ║  HELPER: robot image as b64                                   ║
# ╚═══════════════════════════════════════════════════════════════╝

@st.cache_data
def _robot_b64():
    p = ROOT / "static" / "robot_mascot.jpg"
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return None

# ╔═══════════════════════════════════════════════════════════════╗
# ║  AUTH PAGE                                                     ║
# ╚═══════════════════════════════════════════════════════════════╝

def _auth_page():
    # Spacer
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2, 1.6, 1.2])
    with c2:
        st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)

        # Robot avatar
        b64 = _robot_b64()
        if b64:
            st.markdown(
                f'<div style="text-align:center;margin-bottom:0.6rem">'
                f'<img src="data:image/jpeg;base64,{b64}" '
                f'style="width:120px;border-radius:50%;border:3px solid rgba(124,107,255,0.3);'
                f'box-shadow:0 0 30px rgba(124,107,255,0.2)"/></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="auth-logo">🤖 AI Data Analyst</div>'
            '<div class="auth-sub">Sign in to start analysing your data</div>',
            unsafe_allow_html=True,
        )

        t1, t2 = st.tabs(["🔑  Sign In", "📝  Create Account"])

        with t1:
            with st.form("login", clear_on_submit=False):
                u = st.text_input("Username", placeholder="your username")
                p = st.text_input("Password", type="password", placeholder="••••••••")
                if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                    r = _am().login(u, p)
                    if r["success"]:
                        st.session_state.update(auth=True, user=r["user"]["username"], profile=r["user"])
                        st.rerun()
                    else:
                        st.error(r["message"])

        with t2:
            with st.form("register", clear_on_submit=True):
                nu = st.text_input("Username", placeholder="choose a username", key="ru")
                dn = st.text_input("Full Name", placeholder="John Doe", key="rd")
                np = st.text_input("Password", type="password", placeholder="min 4 chars", key="rp")
                cp = st.text_input("Confirm Password", type="password", placeholder="re-enter", key="rc")
                if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                    if np != cp:
                        st.error("Passwords don't match.")
                    else:
                        r = _am().register(nu, np, dn)
                        st.success(r["message"]) if r["success"] else st.error(r["message"])

        st.markdown("</div>", unsafe_allow_html=True)

    # Theme toggle at bottom
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    _, tc, _ = st.columns([2, 1, 2])
    with tc:
        lbl = "☀️ Switch to Light" if st.session_state.theme == "dark" else "🌙 Switch to Dark"
        if st.button(lbl, use_container_width=True, key="auth_theme"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

# ╔═══════════════════════════════════════════════════════════════╗
# ║  SIDEBAR                                                      ║
# ╚═══════════════════════════════════════════════════════════════╝

def _sidebar():
    with st.sidebar:
        pr = st.session_state.profile or {}
        name = pr.get("display_name", "User")
        color = pr.get("avatar_color", "#7C6BFF")
        uname = pr.get("username", "")

        # ── Profile ──
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:0 0 0.4rem">'
            f'{render_user_avatar(name, color)}'
            f'<div><div style="font-weight:600;font-size:0.88rem">{name}</div>'
            f'<div style="font-size:0.7rem;opacity:0.45">@{uname}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Actions row ──
        a1, a2, a3 = st.columns(3)
        with a1:
            t = "☀️" if st.session_state.theme == "dark" else "🌙"
            if st.button(t, use_container_width=True, key="sb_theme", help="Toggle theme"):
                st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                st.rerun()
        with a2:
            if st.button("🏠", use_container_width=True, key="sb_home", help="Home"):
                st.session_state.update(page="landing", sid=None)
                st.rerun()
        with a3:
            if st.button("📚", use_container_width=True, key="sb_hist", help="All history"):
                st.session_state.page = "history"
                st.rerun()

        st.divider()

        # ── New chat ──
        if st.button("➕  New Chat", use_container_width=True, type="primary", key="sb_new"):
            sid = _hm().create_session(st.session_state.user)
            st.session_state.update(sid=sid, msgs=[], page="chat")
            if st.session_state.agent:
                st.session_state.agent.clear_memory()
            st.rerun()

        st.divider()

        # ── History ──
        st.caption("RECENT CHATS")
        sessions = _hm().get_sessions(st.session_state.user)
        if not sessions:
            st.markdown('<div style="font-size:0.78rem;opacity:0.4;padding:0.3rem 0">No chats yet</div>', unsafe_allow_html=True)

        for s in sessions[:12]:
            title = s.get("title") or "New Chat"
            doc = s.get("document_name")
            ic = "📎" if doc else "💬"
            short = title[:28] + ("…" if len(title) > 28 else "")
            active = s["id"] == st.session_state.sid

            c1, c2 = st.columns([7, 1])
            with c1:
                style = "primary" if active else "secondary"
                if st.button(f"{ic} {short}", key=f"h_{s['id']}", use_container_width=True,
                             type=style if active else "secondary"):
                    st.session_state.update(
                        sid=s["id"],
                        msgs=_hm().get_messages(s["id"]),
                        page="chat",
                    )
                    if st.session_state.agent:
                        st.session_state.agent.clear_memory()
                    st.rerun()
            with c2:
                if st.button("×", key=f"x_{s['id']}"):
                    _hm().delete_session(s["id"])
                    if st.session_state.sid == s["id"]:
                        st.session_state.update(sid=None, msgs=[], page="landing")
                    st.rerun()

        st.divider()

        # ── Upload ──
        st.caption("QUICK UPLOAD")
        up = st.file_uploader("PDF or CSV", type=["pdf", "csv"], key="sb_up", label_visibility="collapsed")
        if up:
            _do_upload(up)

        st.divider()

        # ── Stats ──
        st.caption("SESSION STATS")
        m1, m2 = st.columns(2)
        with m1: st.metric("Queries", st.session_state.nq)
        with m2: st.metric("Charts", st.session_state.nc)

        # ── Schema ──
        with st.expander("🗄️ DB Schema"):
            try:
                from agent.extras import SchemaDiscovery
                st.code(SchemaDiscovery(db_path=str(ROOT / "data" / "database.db")).get_schema(), language="text")
            except Exception:
                st.info("Not available yet.")

        # ── Export ──
        if st.button("📄 Export PDF", use_container_width=True, key="sb_exp"):
            try:
                from agent.extras import ReportExporter
                out = ReportExporter().export(
                    st.session_state.msgs,
                    filename=str(ROOT / "data" / "report.pdf"),
                )
                if out:
                    st.download_button("⬇️ Download", open(out, "rb").read(),
                                       "report.pdf", "application/pdf", use_container_width=True)
            except Exception:
                st.warning("Export unavailable.")

        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True, key="sb_out"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

# ╔═══════════════════════════════════════════════════════════════╗
# ║  FILE UPLOAD                                                   ║
# ╚═══════════════════════════════════════════════════════════════╝

def _do_upload(f):
    nm = f.name.lower()
    if nm.endswith(".pdf"):
        with st.spinner(f"Loading {f.name}…"):
            dd = ROOT / "data" / "docs"
            dd.mkdir(parents=True, exist_ok=True)
            p = dd / f.name
            p.write_bytes(f.read())
            if st.session_state.agent:
                try: st.session_state.agent._get_rag_tool().load_pdf(str(p))
                except Exception as e: st.error(str(e)); return
            sid = _hm().create_session(st.session_state.user, f"📄 {f.name}", f.name)
            st.session_state.update(sid=sid, msgs=[], page="chat")
            st.toast(f"✅ {f.name} loaded!", icon="📄")
            st.rerun()

    elif nm.endswith(".csv"):
        import pandas as pd
        df = pd.read_csv(f); f.seek(0)
        raw = Path(f.name).stem
        tbl = _re.sub(r"_+", "_", _re.sub(r"[^a-z0-9_]", "_", raw.lower()).strip("_"))

        st.markdown(f"**Preview** — {len(df):,} rows × {len(df.columns)} cols")
        st.dataframe(df.head(6), use_container_width=True, height=200)
        tbl = st.text_input("Table name", value=tbl, key="up_tbl")
        ok = bool(_re.match(r"^[a-z][a-z0-9_]*$", tbl)) and len(tbl) >= 2

        if not ok:
            st.warning("Name: a-z start, only a-z 0-9 _, min 2 chars")
        if st.button("📥 Load", disabled=not ok, type="primary", key="up_go"):
            with st.spinner("Loading…"):
                try:
                    tmp = ROOT / "data" / f"_u_{tbl}.csv"
                    df.to_csv(tmp, index=False)
                    from utils.db_loader import load_custom_csv_to_sqlite
                    load_custom_csv_to_sqlite(str(tmp), tbl, str(ROOT / "data" / "database.db"))
                    tmp.unlink(missing_ok=True)
                    if st.session_state.agent: st.session_state.agent._sql_tool = None
                    sid = _hm().create_session(st.session_state.user, f"📊 {tbl}", f.name)
                    st.session_state.update(sid=sid, msgs=[], page="chat")
                    st.toast(f"✅ {len(df):,} rows → {tbl}", icon="📊")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

# ╔═══════════════════════════════════════════════════════════════╗
# ║  LANDING PAGE                                                  ║
# ╚═══════════════════════════════════════════════════════════════╝

def _landing():
    # Hero
    st.markdown('<div class="hero">', unsafe_allow_html=True)

    b64 = _robot_b64()
    if b64:
        st.markdown(
            f'<div class="robo-box">'
            f'<div class="robo-ring"></div>'
            f'<img src="data:image/jpeg;base64,{b64}" alt="AI Robot"/>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<h1>Your Intelligent Data Analyst</h1>'
        '<p class="sub">Upload documents, ask questions in plain English, and get '
        'instant insights with charts. I handle SQL queries, document analysis, '
        'Python calculations, and multi-step reasoning.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Upload section
    st.markdown("---")
    st.markdown("#### 📁  Upload Your Data")
    u1, u2 = st.columns(2)
    with u1:
        pdf = st.file_uploader("Drop a **PDF** to ask questions about it", type=["pdf"], key="lp")
        if pdf: _do_upload(pdf)
    with u2:
        csv = st.file_uploader("Drop a **CSV** to query with natural language", type=["csv"], key="lc")
        if csv: _do_upload(csv)

    # Features
    st.markdown("---")
    st.markdown("#### ✨  Capabilities")
    feats = [
        ("🗄️", "SQL Analysis", "Ask questions → I write & run SQL automatically"),
        ("📄", "Document Q&A", "Upload PDFs → ask anything about the content"),
        ("🐍", "Code Execution", "Calculations, statistics & chart generation"),
        ("🔗", "Multi-Hop", "Chain multiple tools for complex analysis"),
    ]
    cols = st.columns(4)
    for col, (ic, tt, ds) in zip(cols, feats):
        with col:
            st.markdown(
                f'<div class="feat-card">'
                f'<div class="ic">{ic}</div>'
                f'<div class="tt">{tt}</div>'
                f'<div class="ds">{ds}</div></div>',
                unsafe_allow_html=True,
            )

    # Example queries
    st.markdown("---")
    st.markdown("#### 💡  Try These")
    examples = [
        ("🗄️", "Top 5 products by profit"),
        ("📊", "Total sales by region"),
        ("📄", "What is the return policy?"),
        ("🐍", "Compound interest: $10K, 8%, 5yr"),
        ("🔗", "Sales by category → bar chart"),
    ]
    ecols = st.columns(len(examples))
    for col, (ic, q) in zip(ecols, examples):
        with col:
            if st.button(f"{ic} {q}", key=f"e_{q[:12]}", use_container_width=True):
                sid = _hm().create_session(st.session_state.user)
                st.session_state.update(sid=sid, msgs=[], page="chat", _pend=q)
                st.rerun()

    # Direct chat
    st.markdown("---")
    st.markdown("#### 💬  Or Start Chatting")
    if prompt := st.chat_input("Ask me anything about the data…", key="li"):
        sid = _hm().create_session(st.session_state.user)
        st.session_state.update(sid=sid, msgs=[], page="chat", _pend=prompt)
        st.rerun()

# ╔═══════════════════════════════════════════════════════════════╗
# ║  CHAT PAGE                                                     ║
# ╚═══════════════════════════════════════════════════════════════╝

def _chat():
    # Header
    sess = _hm().get_session(st.session_state.sid) if st.session_state.sid else None
    title = (sess or {}).get("title", "AI Data Analyst")
    doc = (sess or {}).get("document_name", "")

    st.markdown(
        f'<div class="page-header">'
        f'<h2>🤖 {title}</h2>'
        f'<p>{"📎 Analysing: " + doc if doc else "Ask questions about your data, documents, or request calculations"}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Messages
    for msg in st.session_state.msgs:
        av = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=av):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _render_meta(msg.get("metadata") or {})

    # Pending query
    if "_pend" in st.session_state:
        q = st.session_state.pop("_pend")
        _run(q)
        st.rerun()

    # Voice mic
    _mic()

    # Input
    if prompt := st.chat_input("Ask me anything…"):
        _run(prompt)
        st.rerun()


def _render_meta(m):
    """Render tool badges, confidence, SQL, sources, figures under a bot message."""
    tools = m.get("tools_used", [])
    if tools:
        st.markdown(" ".join(render_tool_badge(t) for t in tools), unsafe_allow_html=True)
    conf = m.get("confidence", 0)
    if conf > 0:
        st.markdown(render_confidence_ring(conf), unsafe_allow_html=True)
    sql = m.get("sql")
    if sql:
        with st.expander("🔍 SQL Query"):
            st.code(sql, language="sql")
    sources = m.get("sources", [])
    if sources:
        st.markdown(render_source_tags(sources), unsafe_allow_html=True)
    for fig in m.get("figures", []):
        try: st.plotly_chart(fig, use_container_width=True)
        except: pass
    et = m.get("execution_time", 0)
    if et:
        st.caption(f"⏱️ {et:.1f}s")


def _run(query: str):
    """Process a user query through the agent pipeline."""
    if not st.session_state.agent:
        st.error("Agent not ready. Check your GROQ_API_KEY in .env")
        return

    from agent.extras import Guardrails
    v = Guardrails.validate(query)
    if not v["is_safe"]:
        st.session_state.msgs.append({"role": "user", "content": query})
        bl = "🛡️ **Blocked by safety guardrails.**\n" + "\n".join(f"- {w}" for w in v["warnings"])
        st.session_state.msgs.append({"role": "assistant", "content": bl, "metadata": {}})
        _save2(); return

    for w in v.get("warnings", []):
        st.toast(w, icon="⚠️")
    query = v["sanitized_query"]

    st.session_state.msgs.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🧠 Thinking…"):
            try:
                res = st.session_state.agent.run(query)
                ans = res.get("answer", "I couldn't generate a response.")
                st.markdown(ans)

                tools = res.get("tools_used", [])
                if tools:
                    st.markdown(" ".join(render_tool_badge(t) for t in tools), unsafe_allow_html=True)

                from agent.extras import ConfidenceScorer
                conf = ConfidenceScorer.score(res).get("overall", 0)
                if conf > 0:
                    st.markdown(render_confidence_ring(conf), unsafe_allow_html=True)

                sr = res.get("sql_result") or {}
                sql = sr.get("sql")
                if sql:
                    with st.expander("🔍 SQL Query"): st.code(sql, language="sql")

                sources = res.get("sources", [])
                if sources:
                    st.markdown(render_source_tags(sources), unsafe_allow_html=True)

                figs = res.get("figures", [])
                for fig in figs:
                    st.plotly_chart(fig, use_container_width=True)

                if sr and sr.get("success"):
                    with st.expander("💡 Insights"):
                        try:
                            from agent.extras import InsightsGenerator
                            st.markdown(InsightsGenerator().generate(query, sr.get("data", [])))
                        except: st.info("Insights unavailable.")

                et = res.get("execution_time", 0)
                if et: st.caption(f"⏱️ {et:.1f}s")

                meta = dict(tools_used=tools, confidence=conf, sql=sql,
                            sources=sources, figures=figs, execution_time=et)
                st.session_state.msgs.append({"role": "assistant", "content": ans, "metadata": meta})
                st.session_state.nq += 1
                st.session_state.nc += len(figs)
                _save2()

            except Exception as e:
                err = f"❌ Error: {e}"
                st.error(err)
                st.session_state.msgs.append({"role": "assistant", "content": err, "metadata": {}})
                _save2()


def _save2():
    """Persist last user+assistant pair to DB."""
    sid = st.session_state.sid
    if not sid: return
    h = _hm()
    for m in st.session_state.msgs[-2:]:
        safe = {k: v for k, v in (m.get("metadata") or {}).items() if k != "figures"}
        h.add_message(sid, m["role"], m["content"], safe)


def _mic():
    """Voice-input mic button using Web Speech API."""
    st.html("""
    <div style="text-align:right;padding:2px 0">
        <button id="mc" title="🎤 Click to speak your question"
            style="width:42px;height:42px;border-radius:50%;border:none;
            background:linear-gradient(135deg,#7C6BFF,#4F46E5);color:#fff;
            font-size:1.1rem;cursor:pointer;
            box-shadow:0 3px 12px rgba(124,107,255,0.3);transition:all .25s ease"
            onmouseover="this.style.transform='scale(1.08)'"
            onmouseout="this.style.transform='scale(1)'"
            onclick="tgl()">🎤</button>
        <span id="ms" style="display:none;margin-left:6px;font-size:.76rem;
            font-family:Inter,sans-serif;color:#94A3B8">Listening…</span>
    </div>
    <script>
    let R=null,on=false;
    function tgl(){on?stp():go()}
    function go(){
        const S=window.SpeechRecognition||window.webkitSpeechRecognition;
        if(!S){alert('Use Chrome or Edge for voice input');return}
        R=new S();R.continuous=false;R.interimResults=false;R.lang='en-US';
        R.onresult=e=>{
            const t=e.results[0][0].transcript;
            const a=window.parent.document.querySelectorAll('textarea');
            for(const ta of a){
                if(ta.closest('[data-testid="stChatInput"]')){
                    const s=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
                    s.call(ta,t);ta.dispatchEvent(new Event('input',{bubbles:true}));
                    setTimeout(()=>{const f=ta.closest('form');
                        if(f){const b=f.querySelector('button[type="submit"]');if(b)b.click()}},350);
                    break;
                }
            }
            stp();
        };
        R.onerror=()=>stp();R.onend=()=>stp();R.start();on=true;
        document.getElementById('mc').style.background='linear-gradient(135deg,#EF4444,#F87171)';
        document.getElementById('mc').textContent='⏹';
        document.getElementById('ms').style.display='inline';
    }
    function stp(){
        if(R)R.stop();on=false;
        document.getElementById('mc').style.background='linear-gradient(135deg,#7C6BFF,#4F46E5)';
        document.getElementById('mc').textContent='🎤';
        document.getElementById('ms').style.display='none';
    }
    </script>
    """)

# ╔═══════════════════════════════════════════════════════════════╗
# ║  HISTORY PAGE                                                  ║
# ╚═══════════════════════════════════════════════════════════════╝

def _history():
    st.markdown(
        '<div class="page-header"><h2>📚 Chat History</h2>'
        '<p>Browse and resume past conversations</p></div>',
        unsafe_allow_html=True,
    )
    sessions = _hm().get_sessions(st.session_state.user)
    if not sessions:
        st.info("🗂️ No conversations yet — start a new chat!")
        return

    q = st.text_input("🔍 Search…", placeholder="Filter by title or document", key="hs")
    if q:
        sessions = [s for s in sessions
                    if q.lower() in (s.get("title") or "").lower()
                    or q.lower() in (s.get("document_name") or "").lower()]

    for i in range(0, len(sessions), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j >= len(sessions): break
            s = sessions[i + j]
            with col:
                title = s.get("title") or "New Chat"
                doc = s.get("document_name") or ""
                mc = s.get("message_count", 0)
                dt = (s.get("updated_at") or "")[:10]
                ic = "📎" if doc else "💬"

                st.markdown(
                    f'<div class="s-card">'
                    f'<div class="st">{ic} {title}</div>'
                    f'<div class="sm">{mc} msgs · {dt}{"  ·  " + doc if doc else ""}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Open →", key=f"ho_{s['id']}", use_container_width=True):
                    st.session_state.update(
                        sid=s["id"], msgs=_hm().get_messages(s["id"]), page="chat"
                    )
                    st.rerun()

# ╔═══════════════════════════════════════════════════════════════╗
# ║  MAIN                                                          ║
# ╚═══════════════════════════════════════════════════════════════╝

def main():
    _boot()
    st.markdown(get_full_css(st.session_state.theme), unsafe_allow_html=True)

    if not st.session_state.auth:
        _auth_page()
        return

    _agent_init()
    _sidebar()

    pg = st.session_state.page
    if pg == "chat" and st.session_state.sid:
        _chat()
    elif pg == "history":
        _history()
    else:
        _landing()


if __name__ == "__main__":
    main()
