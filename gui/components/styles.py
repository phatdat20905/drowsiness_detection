# ============================================================
#  components/styles.py  –  Global CSS (dark professional theme)
# ============================================================

THEME_CSS = """
<style>
/* ── Google Fonts ────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
.material-icons,
.material-symbols-rounded,
.material-symbols-outlined {
    font-family: "Material Icons" !important;
}

/* ── Root variables ─────────────────────────────────────── */
:root {
    --bg-base:    #0d1117;
    --bg-surface: #161b22;
    --bg-card:    #1c2333;
    --bg-hover:   #21262d;
    --border:     #30363d;
    --accent:     #2f81f7;
    --accent-dim: #1f6feb33;
    --success:    #3fb950;
    --warning:    #d29922;
    --danger:     #f85149;
    --text-pri:   #e6edf3;
    --text-sec:   #8b949e;
    --text-muted: #484f58;
    --radius:     10px;
    --radius-lg:  16px;
}

/* ── App shell ───────────────────────────────────────────── */
.stApp { background: var(--bg-base) !important; color: var(--text-pri) !important; }
.stApp {
    font-family: 'Inter', sans-serif;
}


/* Hide Streamlit chrome */
#MainMenu,
footer {
    visibility: hidden;
}

.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 100% !important;
}

/* ── Sidebar ────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text-pri) !important; }

/* ── KPI Cards ───────────────────────────────────────────── */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s, transform .15s;
}
.kpi-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0;
    width: 3px; height: 100%;
}
.kpi-card.accent::before  { background: var(--accent); }
.kpi-card.success::before { background: var(--success); }
.kpi-card.warning::before { background: var(--warning); }
.kpi-card.danger::before  { background: var(--danger); }

.kpi-label {
    font-size: 11px; font-weight: 600; letter-spacing: .08em;
    text-transform: uppercase; color: var(--text-sec); margin-bottom: 6px;
}
.kpi-value {
    font-size: 2.4rem; font-weight: 700; color: var(--text-pri);
    line-height: 1; margin-bottom: 4px;
}
.kpi-delta {
    font-size: 12px; color: var(--text-sec);
}
.kpi-icon {
    position: absolute; right: 20px; top: 50%;
    transform: translateY(-50%);
    font-size: 2rem; opacity: .15;
}

/* ── Status badges ───────────────────────────────────────── */
.badge {
    display: inline-block; border-radius: 6px;
    padding: 3px 10px; font-size: 12px; font-weight: 600;
}
.badge-normal { background: #1e3a2a; color: var(--success); }
.badge-tired  { background: #3a2e1a; color: var(--warning); }
.badge-drowsy { background: #3a1a1a; color: var(--danger); }
.badge-admin  { background: var(--accent-dim); color: var(--accent); }
.badge-driver { background: #1e3a3a; color: #39c5cf; }

/* ── Section header ─────────────────────────────────────── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px; margin: 24px 0 16px;
}
.section-header h3 {
    font-size: 15px; font-weight: 600; color: var(--text-pri);
    margin: 0;
}
.section-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); flex-shrink: 0;
}

/* ── Score bar ───────────────────────────────────────────── */
.score-container { margin: 8px 0; }
.score-bar-bg {
    height: 8px; background: var(--bg-hover);
    border-radius: 4px; overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 4px; transition: width .4s; }
.score-normal { background: var(--success); }
.score-tired  { background: var(--warning); }
.score-drowsy { background: var(--danger); }

/* ── Alert banner ────────────────────────────────────────── */
.alert-drowsy {
    background: #3a1a1a; border: 1px solid var(--danger);
    border-radius: var(--radius); padding: 16px 20px;
    display: flex; align-items: center; gap: 12px;
    animation: pulse-border 1.5s infinite;
}
@keyframes pulse-border {
    0%, 100% { border-color: var(--danger); }
    50%       { border-color: #ff847a; }
}
.alert-tired {
    background: #3a2e1a; border: 1px solid var(--warning);
    border-radius: var(--radius); padding: 12px 20px;
}

/* ── Tables ─────────────────────────────────────────────── */
.stDataFrame { background: var(--bg-card) !important; }
div[data-testid="stDataFrame"] table { background: var(--bg-card) !important; }

/* ── Inputs ──────────────────────────────────────────────── */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-pri) !important;
    border-radius: var(--radius) !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-dim) !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-pri) !important;
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    transition: all .15s !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
}

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-surface);
    border-radius: var(--radius);
    gap: 4px; padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    color: var(--text-sec) !important;
    font-size: 13px; font-weight: 500;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--text-pri) !important;
}

/* ── Sidebar nav item ────────────────────────────────────── */
.nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 14px; border-radius: var(--radius);
    color: var(--text-sec); font-size: 14px; font-weight: 500;
    cursor: pointer; transition: all .15s;
    margin-bottom: 2px;
    text-decoration: none;
}
.nav-item:hover { background: var(--bg-hover); color: var(--text-pri); }
.nav-item.active { background: var(--accent-dim); color: var(--accent); }
.nav-icon { font-size: 16px; width: 20px; text-align: center; }

/* ── Page title ──────────────────────────────────────────── */
.page-title {
    font-size: 22px; font-weight: 700; color: var(--text-pri);
    margin: 0 0 4px;
}
.page-subtitle { font-size: 13px; color: var(--text-sec); margin-bottom: 24px; }

/* ── Divider ─────────────────────────────────────────────── */
.hline { border: none; border-top: 1px solid var(--border); margin: 20px 0; }

/* ── Mono font for metrics ───────────────────────────────── */
.mono { font-family: 'JetBrains Mono', monospace !important; }

/* ── Camera placeholder ──────────────────────────────────── */
.cam-placeholder {
    background: var(--bg-card);
    border: 2px dashed var(--border);
    border-radius: var(--radius-lg);
    height: 340px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    color: var(--text-muted); gap: 12px;
}
.cam-placeholder .cam-icon { font-size: 3rem; opacity: .4; }

/* ── Driver monitoring live indicator ───────────────────── */
.live-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: var(--danger);
    animation: blink 1.2s infinite;
    margin-right: 6px;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: .2; }
}

/* ── Responsive ─────────────────────────────────────────── */
@media (max-width: 768px) {
    .block-container { padding: 1rem !important; }
    .kpi-value { font-size: 1.8rem; }
}
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def kpi_card(label: str, value, delta: str = "", variant: str = "accent", icon: str = ""):
    return f"""
    <div class="kpi-card {variant}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta">{delta}</div>
        <div class="kpi-icon">{icon}</div>
    </div>"""


def badge(text: str, variant: str = "normal") -> str:
    return f'<span class="badge badge-{variant}">{text}</span>'


def section_header(title: str):
    import streamlit as st
    st.markdown(f"""
    <div class="section-header">
        <div class="section-dot"></div>
        <h3>{title}</h3>
    </div>""", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    import streamlit as st
    st.markdown(f"""
    <div class="page-title">{title}</div>
    <div class="page-subtitle">{subtitle}</div>
    """, unsafe_allow_html=True)
