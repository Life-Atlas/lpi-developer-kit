"""
app.py — Swedish Steel Factory Dashboard
Author: Dia Vats
7-page Streamlit + Neo4j dashboard.
"""
import streamlit as st

st.set_page_config(
    page_title="Steel Factory Dashboard",
    page_icon="[SF]",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

h1 { font-family: 'Inter', sans-serif; font-weight: 600; color: #1a1a2e; letter-spacing: -0.5px; }
h2 { font-family: 'Inter', sans-serif; font-weight: 500; color: #2d2d44; }
.section-divider { border: none; border-top: 1px solid #e0e0e0; margin: 1rem 0; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0f1117 0%,#1a1d2e 100%);
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

.metric-card {
    background: linear-gradient(135deg,#1e2235,#252a3f);
    border: 1px solid #2d3454;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 8px;
}
.metric-card .label { color:#94a3b8; font-size:0.78rem; text-transform:uppercase; letter-spacing:1px; }
.metric-card .value { color:#f1f5f9; font-size:2rem; font-weight:700; }

.spof-badge {
    color: #E53935; font-weight: 700; font-size: 0.82rem;
    border: 1px solid #E53935; border-radius: 4px;
    padding: 1px 7px; letter-spacing: 0.5px;
}
.ok-badge {
    color: #43A047; font-weight: 700; font-size: 0.82rem;
    border: 1px solid #43A047; border-radius: 4px;
    padding: 1px 7px; letter-spacing: 0.5px;
}
.footer-bar {
    text-align:center; color:#64748b; font-size:0.75rem;
    margin-top:40px; padding-top:16px;
    border-top:1px solid #1e2235;
}
.page-title {
    border-left: 4px solid #4A90D9;
    padding-left: 12px;
    margin-bottom: 0.25rem;
    font-size: 1.6rem;
    font-weight: 600;
    color: #1a1a2e;
}
</style>
""", unsafe_allow_html=True)

PAGES = [
    "Project Overview",
    "Station Load",
    "Capacity Tracker",
    "Worker Coverage",
    "Factory Floor",
    "Forecast",
    "Self-Test",
]

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/factory.png", width=56)
    st.markdown("## Steel Factory")
    st.markdown("*Neo4j Production Dashboard*")
    st.markdown("---")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.markdown("---")
    st.caption("Made by **Dia Vats**")

# ── Footer helper ─────────────────────────────────────────────────────────────
def footer():
    st.caption("Made by Dia Vats")

# ── Route to page ─────────────────────────────────────────────────────────────
if page == PAGES[0]:
    from pages_impl.page1_overview   import render; render(); footer()
elif page == PAGES[1]:
    from pages_impl.page2_station    import render; render(); footer()
elif page == PAGES[2]:
    from pages_impl.page3_capacity   import render; render(); footer()
elif page == PAGES[3]:
    from pages_impl.page4_workers    import render; render(); footer()
elif page == PAGES[4]:
    from pages_impl.page5_floor      import render; render(); footer()
elif page == PAGES[5]:
    from pages_impl.page6_forecast   import render; render(); footer()
elif page == PAGES[6]:
    from pages_impl.page7_selftest   import render; render(); footer()
