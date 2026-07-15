"""
Design System v2 — Ultra-Premium Theme & Components
=====================================================
Comprehensive Streamlit CSS overrides for a world-class AI platform look.
"""

from __future__ import annotations
import math

# ═══════════════════════════════════════════════════════════════
# THEME PALETTES
# ═══════════════════════════════════════════════════════════════

DARK = dict(
    # Backgrounds
    bg_app="#080C1A",
    bg_sidebar="#0C1023",
    bg_card="rgba(15,20,45,0.85)",
    bg_input="rgba(255,255,255,0.05)",
    bg_hover="rgba(108,99,255,0.08)",
    bg_elevated="rgba(20,26,55,0.95)",
    # Text
    tx1="#F1F5F9",
    tx2="#94A3B8",
    tx3="#64748B",
    # Accent
    ac1="#7C6BFF",
    ac2="#A78BFA",
    ac3="#00D4FF",
    ac4="#FF6B9D",
    glow="rgba(124,107,255,0.25)",
    glow2="rgba(124,107,255,0.12)",
    # Status
    ok="#34D399",
    warn="#FBBF24",
    err="#FB7185",
    # Borders / Shadows
    bd="rgba(148,163,184,0.08)",
    bd2="rgba(124,107,255,0.35)",
    sh1="0 1px 3px rgba(0,0,0,0.4)",
    sh2="0 8px 32px rgba(0,0,0,0.45)",
    sh3="0 0 40px rgba(124,107,255,0.15)",
    # Gradients
    gr1="linear-gradient(135deg,#7C6BFF 0%,#4F46E5 50%,#3B82F6 100%)",
    gr2="linear-gradient(135deg,#7C6BFF 0%,#FF6B9D 100%)",
    gr3="linear-gradient(160deg,#080C1A 0%,#0F1430 50%,#131A3D 100%)",
    gr_user="linear-gradient(135deg,#7C6BFF 0%,#6366F1 100%)",
    gr_bot="rgba(15,20,45,0.7)",
    glass="rgba(255,255,255,0.03)",
    glass_bd="rgba(255,255,255,0.06)",
)

LIGHT = dict(
    bg_app="#F5F7FF",
    bg_sidebar="#EDEFFA",
    bg_card="rgba(255,255,255,0.95)",
    bg_input="rgba(0,0,0,0.03)",
    bg_hover="rgba(90,82,224,0.06)",
    bg_elevated="#FFFFFF",
    tx1="#0F172A",
    tx2="#475569",
    tx3="#94A3B8",
    ac1="#6356E5",
    ac2="#8B5CF6",
    ac3="#0284C7",
    ac4="#E11D79",
    glow="rgba(99,86,229,0.18)",
    glow2="rgba(99,86,229,0.08)",
    ok="#059669",
    warn="#D97706",
    err="#E11D48",
    bd="rgba(15,23,42,0.07)",
    bd2="rgba(99,86,229,0.35)",
    sh1="0 1px 3px rgba(0,0,0,0.06)",
    sh2="0 8px 32px rgba(0,0,0,0.08)",
    sh3="0 0 40px rgba(99,86,229,0.08)",
    gr1="linear-gradient(135deg,#6356E5 0%,#4F46E5 50%,#3B82F6 100%)",
    gr2="linear-gradient(135deg,#6356E5 0%,#E11D79 100%)",
    gr3="linear-gradient(160deg,#F5F7FF 0%,#EEF0FF 50%,#E8ECFF 100%)",
    gr_user="linear-gradient(135deg,#6356E5 0%,#4F46E5 100%)",
    gr_bot="rgba(255,255,255,0.9)",
    glass="rgba(255,255,255,0.55)",
    glass_bd="rgba(15,23,42,0.06)",
)

THEMES = {"dark": DARK, "light": LIGHT}


# ═══════════════════════════════════════════════════════════════
# MEGA CSS
# ═══════════════════════════════════════════════════════════════

_CSS = r"""
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

/* ══════════ GLOBAL ══════════ */
html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background: V_gr3 !important;
    color: V_tx1 !important;
}
#MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }

/* ══════════ SIDEBAR ══════════ */
section[data-testid="stSidebar"] {
    background: V_bg_sidebar !important;
    border-right: 1px solid V_bd !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1rem !important; }
section[data-testid="stSidebar"] * { color: V_tx1 !important; }
section[data-testid="stSidebar"] hr { border-color: V_bd !important; opacity: 0.5; }

/* ══════════ BUTTONS ══════════ */
.stButton > button {
    background: V_gr1 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.01em;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: V_sh1 !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: V_sh2, V_sh3 !important;
    filter: brightness(1.08) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Secondary / delete buttons in sidebar */
section[data-testid="stSidebar"] .stButton > button {
    background: V_bg_input !important;
    border: 1px solid V_bd !important;
    color: V_tx2 !important;
    box-shadow: none !important;
    font-size: 0.78rem !important;
    padding: 0.45rem 0.8rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: V_bg_hover !important;
    border-color: V_ac1 !important;
    color: V_ac1 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ══════════ INPUTS ══════════ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: V_bg_input !important;
    border: 1.5px solid V_bd !important;
    border-radius: 10px !important;
    color: V_tx1 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 0.9rem !important;
    transition: all 0.25s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: V_ac1 !important;
    box-shadow: 0 0 0 3px V_glow !important;
    outline: none !important;
}
.stTextInput label, .stTextArea label, .stFileUploader label,
.stSelectbox label, .stMultiSelect label {
    color: V_tx2 !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
}

/* ══════════ CHAT ══════════ */
[data-testid="stChatInput"] { background: transparent !important; }
[data-testid="stChatInput"] textarea {
    background: V_bg_elevated !important;
    border: 1.5px solid V_bd !important;
    border-radius: 14px !important;
    color: V_tx1 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: V_ac1 !important;
    box-shadow: 0 0 0 3px V_glow !important;
}
[data-testid="stChatInput"] button {
    background: V_gr1 !important;
    border: none !important;
    border-radius: 10px !important;
}
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.3rem 0 !important;
}

/* ══════════ TABS ══════════ */
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent !important; border-bottom: none !important; }
.stTabs [data-baseweb="tab"] {
    background: V_bg_input !important;
    border: 1px solid V_bd !important;
    border-radius: 10px !important;
    color: V_tx2 !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    padding: 0.5rem 1.3rem !important;
    transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    background: V_gr1 !important;
    color: #fff !important;
    border-color: transparent !important;
    box-shadow: V_sh1, V_sh3 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ══════════ METRICS ══════════ */
[data-testid="stMetric"] {
    background: V_glass !important;
    border: 1px solid V_glass_bd !important;
    border-radius: 12px !important;
    padding: 0.7rem !important;
}
[data-testid="stMetricValue"] { color: V_ac1 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: V_tx3 !important; }

/* ══════════ FILE UPLOADER ══════════ */
[data-testid="stFileUploader"] section {
    border: 2px dashed V_bd !important;
    border-radius: 14px !important;
    padding: 0.6rem !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: V_ac1 !important;
    background: V_bg_hover !important;
}

/* ══════════ EXPANDER ══════════ */
details[data-testid="stExpander"] {
    background: V_glass !important;
    border: 1px solid V_glass_bd !important;
    border-radius: 12px !important;
    overflow: hidden;
}
details[data-testid="stExpander"] summary { color: V_tx1 !important; font-weight: 500 !important; }
details[data-testid="stExpander"] summary span { color: V_tx1 !important; }

/* ══════════ FORMS ══════════ */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* ══════════ DATAFRAME ══════════ */
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden; }

/* ══════════ DIVIDER ══════════ */
hr { border-color: V_bd !important; margin: 0.6rem 0 !important; }

/* ══════════ SCROLLBAR ══════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: V_tx3; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: V_tx2; }

/* ══════════ TOAST ══════════ */
[data-testid="stToast"] { background: V_bg_elevated !important; border: 1px solid V_bd !important; border-radius: 12px !important; }

/* ══════════ CUSTOM COMPONENTS ══════════ */

.auth-wrap {
    max-width: 460px;
    margin: 0 auto;
    padding: 2.5rem 2rem;
    background: V_bg_card;
    border: 1px solid V_glass_bd;
    border-radius: 28px;
    backdrop-filter: blur(24px);
    box-shadow: V_sh2, V_sh3;
    animation: scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.auth-logo {
    text-align: center;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: V_gr2;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}
.auth-sub {
    text-align: center;
    color: V_tx3;
    font-size: 0.88rem;
    margin-bottom: 1.8rem;
    font-weight: 400;
}

.page-header {
    background: V_gr1;
    padding: 1rem 1.4rem;
    border-radius: 14px;
    margin-bottom: 1rem;
    box-shadow: V_sh1, V_sh3;
    animation: slideDown 0.35s ease-out;
}
.page-header h2 { color: #fff; font-size: 1.15rem; font-weight: 700; margin: 0; }
.page-header p { color: rgba(255,255,255,0.75); font-size: 0.78rem; margin: 0.15rem 0 0; }

.hero {
    text-align: center;
    padding: 1.5rem 0.5rem 0.5rem;
    animation: fadeUp 0.5s ease-out;
}
.hero h1 {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: V_gr2;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.6rem 0 0.3rem;
}
.hero .sub {
    color: V_tx2;
    font-size: 1rem;
    max-width: 560px;
    margin: 0 auto;
    line-height: 1.55;
}

.robo-box {
    position: relative;
    display: inline-block;
    animation: floaty 3.5s ease-in-out infinite;
}
.robo-box img {
    width: 240px;
    height: auto;
    border-radius: 22px;
    box-shadow: V_sh2, 0 0 80px V_glow;
    border: 2px solid V_glass_bd;
}
.robo-ring {
    position: absolute;
    inset: -18px;
    border-radius: 30px;
    border: 2px solid V_glass_bd;
    animation: ringPulse 2.5s ease-in-out infinite;
    pointer-events: none;
}

.feat-card {
    background: V_glass;
    border: 1px solid V_glass_bd;
    border-radius: 14px;
    padding: 1.3rem 0.8rem;
    text-align: center;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
}
.feat-card:hover {
    transform: translateY(-3px);
    border-color: V_ac1;
    box-shadow: V_sh1, V_sh3;
    background: V_bg_hover;
}
.feat-card .ic { font-size: 1.8rem; margin-bottom: 0.35rem; }
.feat-card .tt { font-size: 0.88rem; font-weight: 600; color: V_tx1; margin-bottom: 0.2rem; }
.feat-card .ds { font-size: 0.74rem; color: V_tx3; line-height: 1.4; }

.tool-badge {
    display: inline-block;
    padding: 0.18rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 0.3rem;
    margin-top: 0.3rem;
    letter-spacing: 0.02em;
}
.b-sql { background: rgba(59,130,246,0.12); color: #60A5FA; border: 1px solid rgba(59,130,246,0.25); }
.b-rag { background: rgba(52,211,153,0.12); color: #34D399; border: 1px solid rgba(52,211,153,0.25); }
.b-code { background: rgba(251,191,36,0.12); color: #FBBF24; border: 1px solid rgba(251,191,36,0.25); }
.b-multi { background: rgba(167,139,250,0.12); color: #A78BFA; border: 1px solid rgba(167,139,250,0.25); }
.b-direct { background: rgba(148,163,184,0.12); color: #94A3B8; border: 1px solid rgba(148,163,184,0.25); }

.conf-ring { display: inline-flex; align-items: center; gap: 6px; margin-top: 0.3rem; }
.conf-ring svg { transform: rotate(-90deg); }
.conf-ring .cl { font-size: 0.72rem; color: V_tx3; font-weight: 500; }

.src-tag {
    display: inline-block;
    background: V_glass;
    border: 1px solid V_glass_bd;
    padding: 0.12rem 0.5rem;
    border-radius: 7px;
    font-size: 0.68rem;
    margin: 0.12rem;
    color: V_tx3;
    transition: all 0.2s ease;
}
.src-tag:hover { border-color: V_ac1; color: V_ac2; }

.s-card {
    background: V_glass;
    border: 1px solid V_glass_bd;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    transition: all 0.2s ease;
    margin-bottom: 0.6rem;
}
.s-card:hover { background: V_bg_hover; border-color: V_bd2; }
.s-card .st { font-size: 0.84rem; font-weight: 500; color: V_tx1; }
.s-card .sm { font-size: 0.68rem; color: V_tx3; margin-top: 3px; }

.dot-loader { display: flex; align-items: center; gap: 5px; padding: 0.5rem 0; }
.dot-loader span {
    width: 7px; height: 7px;
    background: V_ac1;
    border-radius: 50%;
    animation: dotBounce 1.2s infinite ease-in-out both;
}
.dot-loader span:nth-child(1) { animation-delay: -0.24s; }
.dot-loader span:nth-child(2) { animation-delay: -0.12s; }
.dot-loader span:nth-child(3) { animation-delay: 0s; }

.avatar-circle {
    width: 40px; height: 40px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.95rem;
    color: #fff;
    flex-shrink: 0;
    box-shadow: V_sh1;
}

/* ══════════ ANIMATIONS ══════════ */
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
@keyframes floaty { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
@keyframes ringPulse { 0%, 100% { opacity: 0.3; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.03); } }
@keyframes dotBounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 50% { box-shadow: 0 0 0 12px rgba(239,68,68,0); } }
"""


def get_full_css(theme: str = "dark") -> str:
    t = THEMES.get(theme, DARK)
    css = _CSS
    for key, val in t.items():
        css = css.replace(f"V_{key}", val)
    return f"<style>{css}</style>"


# ═══════════════════════════════════════════════════════════════
# COMPONENT RENDERERS
# ═══════════════════════════════════════════════════════════════

def render_tool_badge(tool: str) -> str:
    ic = {"SQL": "🗄️", "RAG": "📄", "CODE": "🐍", "MULTI": "🔗", "DIRECT": "💬"}
    cl = {"SQL": "b-sql", "RAG": "b-rag", "CODE": "b-code", "MULTI": "b-multi", "DIRECT": "b-direct"}
    return f'<span class="tool-badge {cl.get(tool,"b-direct")}">{ic.get(tool,"⚡")} {tool}</span>'


def render_confidence_ring(score: int, size: int = 36) -> str:
    r = size / 2 - 3
    c = 2 * math.pi * r
    o = c * (1 - score / 100)
    color = "#34D399" if score >= 70 else "#FBBF24" if score >= 40 else "#FB7185"
    return (
        f'<div class="conf-ring">'
        f'<svg width="{size}" height="{size}">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="rgba(148,163,184,0.15)" stroke-width="3"/>'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{color}" stroke-width="3" '
        f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{o:.1f}" stroke-linecap="round"/>'
        f'</svg><span class="cl">{score}%</span></div>'
    )


def render_source_tags(sources: list[str]) -> str:
    if not sources:
        return ""
    return '<div style="margin-top:4px">' + "".join(
        f'<span class="src-tag">📎 {s}</span>' for s in sources[:5]
    ) + "</div>"


def render_user_avatar(name: str, color: str) -> str:
    ini = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    return f'<div class="avatar-circle" style="background:{color}">{ini}</div>'
