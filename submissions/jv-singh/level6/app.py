"""Streamlit dashboard for the Level 6 factory Neo4j graph."""

# -----------------------------------------------------------------------------
# FACTORY GRAPH DASHBOARD - Level 6 Neo4j & Streamlit
# UI/UX OVERHAUL - Horizontal tab navigation
# -----------------------------------------------------------------------------

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase


BASE_DIR = Path(__file__).resolve().parent

# Page config - wide layout, no emoji, clean favicon
st.set_page_config(
    page_title="Factory Graph Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",  # Sidebar collapsed — nav is now top tabs
)

# Global CSS injection - dark industrial premium theme + horizontal tab overrides
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

:root {
    --bg:          #0D0F14;
    --surface:     #13161E;
    --card:        #1A1E2A;
    --card-hover:  #1F2435;
    --border:      #272C3D;
    --accent:      #F59E0B;
    --accent-dim:  rgba(245,158,11,0.12);
    --accent-glow: rgba(245,158,11,0.25);
    --green:       #10B981;
    --red:         #EF4444;
    --text:        #E2E8F0;
    --text-muted:  #64748B;
    --text-dim:    #94A3B8;
    --radius:      12px;
    --radius-sm:   8px;
    --shadow:      0 4px 24px rgba(0,0,0,0.45);
    --shadow-hover:0 8px 40px rgba(0,0,0,0.65);
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'Sora', sans-serif !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    font-family: 'Sora', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

h1 {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    color: var(--text) !important;
}
h2 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 0.5rem !important;
    margin-bottom: 1.25rem !important;
}
h3 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: var(--text-dim) !important;
}
p, li, label, span {
    color: var(--text-dim) !important;
}

[data-testid="stMetric"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.1rem 1.3rem !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease !important;
    cursor: default;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: var(--shadow-hover) !important;
    border-color: var(--accent) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Sora', sans-serif !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-family: 'DM Mono', monospace !important;
}

[data-testid="stButton"] button {
    background: var(--card) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    padding: 0.5rem 1.2rem !important;
    transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.15s ease !important;
}
[data-testid="stButton"] button:hover {
    background: var(--accent-dim) !important;
    box-shadow: 0 0 16px var(--accent-glow) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stSelectbox"] > div > div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stSelectbox"] > div > div:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px var(--accent-glow) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stDataFrame"] iframe {
    background: var(--card) !important;
}

.js-plotly-plot, .plotly {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background: var(--card) !important;
    box-shadow: var(--shadow) !important;
    overflow: hidden !important;
    transition: box-shadow 0.2s ease !important;
}
.js-plotly-plot:hover {
    box-shadow: var(--shadow-hover) !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border-width: 1px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--accent), #FBBF24) !important;
    border-radius: 99px !important;
}
[data-testid="stProgressBar"] {
    background: var(--border) !important;
    border-radius: 99px !important;
    height: 10px !important;
}

hr {
    border-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}

[data-testid="stCaptionContainer"] p {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.05em !important;
    color: var(--text-muted) !important;
}

[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: var(--accent-dim) !important;
    border-color: var(--accent) !important;
    color: var(--text-dim) !important;
}

/* =========================================================
   HORIZONTAL TABS - Full custom override
   ========================================================= */

/* Tab strip container */
[data-testid="stTabs"] {
    background: transparent !important;
    margin-bottom: 1.75rem !important;
}

/* The scrollable tab list wrapper */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 0.35rem 0.45rem !important;
    gap: 0.2rem !important;
    box-shadow: var(--shadow) !important;
    overflow-x: auto !important;
    scrollbar-width: none !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none !important;
}

/* Individual tab button */
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.55rem 1.2rem !important;
    white-space: nowrap !important;
    transition: background 0.18s ease, color 0.18s ease,
                border-color 0.18s ease, box-shadow 0.18s ease !important;
    outline: none !important;
}

/* Tab hover */
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background: var(--accent-dim) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* Active / selected tab */
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--accent-dim) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
    font-weight: 600 !important;
}

/* Kill the default underline indicator that Streamlit renders */
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none !important;
    background: transparent !important;
    height: 0 !important;
}

/* Tab content panel */
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding: 0 !important;
}

/* =========================================================
   CARD / UTILITY CLASSES
   ========================================================= */

.ui-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.1rem;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.ui-card:hover {
    box-shadow: var(--shadow-hover);
    border-color: rgba(245,158,11,0.35);
}

.section-badge {
    display: inline-block;
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 6px;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    margin-bottom: 0.6rem;
}

.check-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 1rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    margin-bottom: 0.45rem;
    background: var(--card);
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: var(--text-dim);
    transition: background 0.15s ease, border-color 0.15s ease;
}
.check-row:hover {
    background: var(--card-hover);
    border-color: rgba(245,158,11,0.3);
}
.check-row.pass { border-left: 3px solid var(--green); }
.check-row.fail { border-left: 3px solid var(--red); }
.dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.dot.pass { background: var(--green); box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.dot.fail { background: var(--red);   box-shadow: 0 0 6px rgba(239,68,68,0.6); }
.badge-pts {
    margin-left: auto;
    font-size: 0.7rem;
    color: var(--text-muted);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-up {
    animation: fadeUp 0.4s ease both;
}

code {
    font-family: 'DM Mono', monospace !important;
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    color: var(--accent) !important;
    font-size: 0.82rem !important;
}
pre code {
    display: block;
    padding: 0.75rem 1rem !important;
}
</style>
"""

# Shared Plotly theme dict
PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(26,30,42,1)",
    plot_bgcolor="rgba(26,30,42,1)",
    font=dict(family="DM Mono, monospace", color="#94A3B8", size=11),
    colorway=["#F59E0B", "#3B82F6", "#10B981", "#8B5CF6", "#EF4444", "#06B6D4"],
    margin=dict(l=16, r=16, t=44, b=16),
)

HOVER_STYLE = dict(
    bgcolor="#13161E",
    bordercolor="#F59E0B",
    font=dict(family="DM Mono", size=11, color="#E2E8F0"),
)

AXIS_STYLE = dict(
    xaxis_gridcolor="#1F2435",
    xaxis_linecolor="#272C3D",
    xaxis_tickfont_family="DM Mono",
    xaxis_tickfont_size=10,
    yaxis_gridcolor="#1F2435",
    yaxis_linecolor="#272C3D",
    yaxis_tickfont_family="DM Mono",
    yaxis_tickfont_size=10,
)

LEGEND_STYLE = dict(
    legend_bgcolor="rgba(19,22,30,0.9)",
    legend_bordercolor="#272C3D",
    legend_borderwidth=1,
    legend_font_family="DM Mono",
    legend_font_size=10,
    legend_font_color="#94A3B8",
)


def card_start() -> None:
    st.markdown('<div class="ui-card fade-up">', unsafe_allow_html=True)


def card_end() -> None:
    st.markdown('</div>', unsafe_allow_html=True)


def _badge(text: str) -> None:
    st.markdown(f'<div class="section-badge">{text}</div>', unsafe_allow_html=True)


def _page_rule() -> None:
    st.markdown(
        '<div style="height:2px;background:linear-gradient(90deg,#F59E0B,transparent);'
        'border-radius:2px;margin-bottom:1.5rem;"></div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# CORE LOGIC
# -----------------------------------------------------------------------------

def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


@st.cache_resource(show_spinner=False)
def get_driver():
    load_dotenv(BASE_DIR / ".env")
    uri = get_secret("NEO4J_URI")
    user = get_secret("NEO4J_USER", "neo4j")
    password = get_secret("NEO4J_PASSWORD")
    if not uri or not password:
        return None
    return GraphDatabase.driver(uri, auth=(user, password))


def query_df(driver, cypher: str, **params) -> pd.DataFrame:
    with driver.session() as session:
        rows = [dict(record) for record in session.run(cypher, **params)]
    return pd.DataFrame(rows)


def run_self_test(driver):
    checks = []
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        checks.append(("Neo4j connected", True, 3))
    except Exception as exc:
        checks.append((f"Neo4j connected ({exc.__class__.__name__})", False, 3))
        return checks

    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS c").single()
        count = result["c"]
        checks.append((f"{count} nodes (min: 50)", count >= 50, 3))

        result = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
        count = result["c"]
        checks.append((f"{count} relationships (min: 100)", count >= 100, 3))

        result = session.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
        count = result["c"]
        checks.append((f"{count} node labels (min: 6)", count >= 6, 3))

        result = session.run(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"
        ).single()
        count = result["c"]
        checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))

        result = session.run(
            """
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.name AS project,
                   s.name AS station,
                   r.planned_hours AS planned,
                   r.actual_hours AS actual
            LIMIT 10
            """
        )
        rows = [dict(record) for record in result]
        checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
    return checks


# -----------------------------------------------------------------------------
# RENDER FUNCTIONS  (all logic unchanged)
# -----------------------------------------------------------------------------

def render_connection_help() -> None:
    st.markdown(
        """
        <div class="ui-card fade-up" style="border-color:#EF4444;border-left:3px solid #EF4444;">
            <div class="section-badge" style="background:rgba(239,68,68,0.12);
                 color:#EF4444;border-color:#EF4444;">Configuration Required</div>
            <h2 style="border:none!important;color:#EF4444!important;margin-top:0.5rem;">
                Neo4j credentials not configured
            </h2>
            <p style="margin-bottom:0;">
                Add the values below to a local <code>.env</code> file or to Streamlit Cloud
                <strong>Settings -> Secrets</strong> before running the dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        'NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"\n'
        'NEO4J_USER = "neo4j"\n'
        'NEO4J_PASSWORD = "your-password"',
        language="toml",
    )


def render_project_overview(driver) -> None:
    _badge("Module 01")
    st.header("Project Overview")
    _page_rule()

    df = query_df(
        driver,
        """
        MATCH (p:Project)-[work:SCHEDULED_AT]->(s:Station)
        OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
        WITH p,
             collect(DISTINCT prod.product_type) AS products,
             collect(DISTINCT s.name) AS stations,
             sum(work.planned_hours) AS planned_hours,
             sum(work.actual_hours) AS actual_hours
        RETURN p.project_id AS project_id,
               p.project_number AS project_number,
               p.name AS project_name,
               products,
               stations,
               round(planned_hours, 2) AS planned_hours,
               round(actual_hours, 2) AS actual_hours,
               round(actual_hours - planned_hours, 2) AS variance_hours,
               round(10000.0 * (actual_hours - planned_hours) / planned_hours) / 100.0 AS variance_pct
        ORDER BY project_id
        """,
    )
    if df.empty:
        st.warning("No project data found. Run `python seed_graph.py` first.")
        return

    total_planned = df["planned_hours"].sum()
    total_actual = df["actual_hours"].sum()
    variance_pct = ((total_actual - total_planned) / total_planned) * 100 if total_planned else 0

    card_start()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Projects", len(df))
    col2.metric("Planned hours", f"{total_planned:,.1f}")
    col3.metric("Actual hours", f"{total_actual:,.1f}", f"{variance_pct:+.1f}%")
    col4.metric("Projects >10% variance", int((df["variance_pct"] > 10).sum()))
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    display = df.copy()
    display["products"] = display["products"].apply(lambda values: ", ".join(values))
    display["stations"] = display["stations"].apply(lambda values: ", ".join(values))

    card_start()
    _badge("Data Table")
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "variance_pct": st.column_config.NumberColumn("variance_pct", format="%.2f%%"),
            "planned_hours": st.column_config.NumberColumn("planned_hours", format="%.1f"),
            "actual_hours": st.column_config.NumberColumn("actual_hours", format="%.1f"),
        },
    )
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Visualization")
    fig = px.bar(
        df,
        x="project_name",
        y=["planned_hours", "actual_hours"],
        barmode="group",
        title="Planned vs Actual Hours by Project",
        color_discrete_sequence=["#3B82F6", "#F59E0B"],
    )
    fig.update_layout(
        **PLOTLY_THEME,
        **AXIS_STYLE,
        **LEGEND_STYLE,
        xaxis_title="Project",
        yaxis_title="Hours",
        hoverlabel=HOVER_STYLE,
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
    card_end()


def render_station_load(driver) -> None:
    _badge("Module 02")
    st.header("Station Load")
    _page_rule()

    df = query_df(
        driver,
        """
        MATCH (p:Project)-[work:SCHEDULED_AT]->(s:Station)
        RETURN s.station_code AS station_code,
               s.name AS station_name,
               work.week AS week,
               sum(work.planned_hours) AS planned_hours,
               sum(work.actual_hours) AS actual_hours,
               round(sum(work.actual_hours - work.planned_hours), 2) AS variance_hours
        ORDER BY station_code, week
        """,
    )
    if df.empty:
        st.warning("No station load data found.")
        return

    card_start()
    _badge("Filter")
    station_options = ["All stations", *df["station_name"].drop_duplicates().tolist()]
    selected = st.selectbox("Station filter", station_options)
    card_end()

    chart_df = df if selected == "All stations" else df[df["station_name"] == selected]

    melted = chart_df.melt(
        id_vars=["station_code", "station_name", "week"],
        value_vars=["planned_hours", "actual_hours"],
        var_name="metric",
        value_name="hours",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Visualization")
    fig = px.bar(
        melted,
        x="week",
        y="hours",
        color="metric",
        facet_col="station_name" if selected == "All stations" else None,
        facet_col_wrap=3,
        barmode="group",
        hover_data=["station_code"],
        title="Weekly Planned vs Actual Station Load",
        color_discrete_sequence=["#3B82F6", "#F59E0B"],
    )
    fig.update_layout(
        **PLOTLY_THEME,
        **AXIS_STYLE,
        **LEGEND_STYLE,
        height=760 if selected == "All stations" else 460,
        hoverlabel=HOVER_STYLE,
    )
    st.plotly_chart(fig, use_container_width=True)
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Overruns")
    overrun_df = df[df["actual_hours"] > df["planned_hours"]].copy()
    st.markdown(
        f'<p style="color:#EF4444;font-family:\'DM Mono\',monospace;font-size:0.8rem;">'
        f'Overrun: {len(overrun_df)} row(s) where actual hours exceed planned</p>',
        unsafe_allow_html=True,
    )
    st.dataframe(overrun_df, use_container_width=True, hide_index=True)
    card_end()


def render_capacity_tracker(driver) -> None:
    _badge("Module 03")
    st.header("Capacity Tracker")
    _page_rule()

    df = query_df(
        driver,
        """
        MATCH (week:Week)-[:HAS_CAPACITY]->(plan:CapacityPlan)
        RETURN week.week AS week,
               week.sort_order AS sort_order,
               plan.own_hours AS own_hours,
               plan.hired_hours AS hired_hours,
               plan.overtime_hours AS overtime_hours,
               plan.total_capacity AS total_capacity,
               plan.total_planned AS total_planned,
               plan.deficit AS deficit,
               plan.is_deficit AS is_deficit
        ORDER BY sort_order
        """,
    )
    if df.empty:
        st.warning("No capacity data found.")
        return

    deficit_weeks = int(df["is_deficit"].sum())

    card_start()
    col1, col2, col3 = st.columns(3)
    col1.metric("Weeks tracked", len(df))
    col2.metric("Deficit weeks", deficit_weeks)
    col3.metric("Worst deficit", f"{df['deficit'].min():,.0f} hours")
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Visualization")
    fig = px.line(
        df,
        x="week",
        y=["total_capacity", "total_planned"],
        markers=True,
        title="Total Capacity vs Planned Demand",
        color_discrete_sequence=["#10B981", "#F59E0B"],
    )
    deficit_points = df[df["deficit"] < 0]
    fig.add_scatter(
        x=deficit_points["week"],
        y=deficit_points["total_planned"],
        mode="markers",
        marker={"color": "#EF4444", "size": 13, "symbol": "x"},
        name="Deficit week",
    )
    fig.update_layout(
        **PLOTLY_THEME,
        **AXIS_STYLE,
        **LEGEND_STYLE,
        hoverlabel=HOVER_STYLE,
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Weekly Detail")
    styled = df.drop(columns=["sort_order"]).style.apply(
        lambda row: ["background-color: rgba(239,68,68,0.15)" if row["deficit"] < 0 else "" for _ in row],
        axis=1,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)
    card_end()


def render_worker_coverage(driver) -> None:
    _badge("Module 04")
    st.header("Worker Coverage")
    _page_rule()

    coverage = query_df(
        driver,
        """
        MATCH (s:Station)
        OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
        WITH s, collect(DISTINCT w.name) AS workers
        RETURN s.station_code AS station_code,
               s.name AS station_name,
               size([worker IN workers WHERE worker IS NOT NULL]) AS certified_workers,
               [worker IN workers WHERE worker IS NOT NULL] AS workers
        ORDER BY station_code
        """,
    )
    matrix = query_df(
        driver,
        """
        MATCH (w:Worker)
        OPTIONAL MATCH (w)-[:CAN_COVER]->(s:Station)
        RETURN w.name AS worker, collect(DISTINCT s.station_code) AS stations
        ORDER BY worker
        """,
    )
    if coverage.empty:
        st.warning("No worker coverage data found.")
        return

    spof = coverage[coverage["certified_workers"] <= 1]

    card_start()
    col1, col2, col3 = st.columns(3)
    col1.metric("Workers", len(matrix))
    col2.metric("Stations", len(coverage))
    col3.metric(
        "Single-point-of-failure stations",
        len(spof),
        "Risk" if len(spof) > 0 else None,
        delta_color="inverse",
    )
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Certification Coverage")
    coverage_display = coverage.copy()
    coverage_display["workers"] = coverage_display["workers"].apply(lambda values: ", ".join(values))
    styled = coverage_display.style.apply(
        lambda row: [
            "background-color: rgba(239,68,68,0.15)" if row["certified_workers"] <= 1 else ""
            for _ in row
        ],
        axis=1,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    card_start()
    _badge("Worker <-> Station Matrix")
    all_stations = sorted(coverage["station_code"].dropna().unique().tolist())
    matrix_rows = []
    for _, row in matrix.iterrows():
        covered = set(row["stations"])
        matrix_rows.append({"worker": row["worker"], **{station: station in covered for station in all_stations}})
    matrix_df = pd.DataFrame(matrix_rows)
    st.dataframe(matrix_df, use_container_width=True, hide_index=True)
    card_end()


def render_self_test(driver) -> None:
    _badge("Module 05")
    st.header("Self-Test")
    _page_rule()
    st.caption("Automated checks required by the Level 6 challenge.")

    checks = run_self_test(driver)
    earned = 0
    possible = sum(points for _, _, points in checks)

    card_start()
    for label, passed, points in checks:
        if passed:
            earned += points
        status = "pass" if passed else "fail"
        pts_label = f"{points if passed else 0}/{points} pts"
        st.markdown(
            f"""
            <div class="check-row {status}">
                <span class="dot {status}"></span>
                <span>{label}</span>
                <span class="badge-pts">{pts_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    score_color = "#10B981" if earned == possible else ("#F59E0B" if earned >= possible * 0.6 else "#EF4444")
    st.markdown(
        f"""
        <div style="text-align:center;padding:1.2rem 0;">
            <span style="font-family:'DM Mono',monospace;font-size:0.75rem;
                         letter-spacing:0.12em;color:#64748B;text-transform:uppercase;">
                Self-Test Score
            </span><br>
            <span style="font-family:'Sora',sans-serif;font-size:2.8rem;
                         font-weight:700;color:{score_color};">
                {earned}<span style="color:#272C3D;font-size:1.8rem;">/{possible}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(earned / possible if possible else 0)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # ── Top header (unchanged visual) ────────────────────────────────────────
    st.markdown(
        """
        <div class="fade-up" style="margin-bottom:0.25rem;">
            <div>
                <h1 style="margin:0;padding:0;">Factory Graph Dashboard</h1>
                <p style="margin:0;font-family:'DM Mono',monospace;font-size:0.72rem;
                            letter-spacing:0.08em;color:#64748B;">
                    LEVEL 6 - NEO4J KNOWLEDGE GRAPH - STREAMLIT
                </p>
            </div>
        </div>
        <div style="height:2px;background:linear-gradient(90deg,#F59E0B 0%,#3B82F6 60%,transparent 100%);
                    border-radius:2px;margin:0.75rem 0 1.5rem 0;"></div>
        """,
        unsafe_allow_html=True,
    )

    driver = get_driver()
    if driver is None:
        render_connection_help()
        return

    # ── Horizontal tab navigation ─────────────────────────────────────────────
    tab_labels = [
        "01  Project Overview",
        "02  Station Load",
        "03  Capacity Tracker",
        "04  Worker Coverage",
        "05  Self-Test",
    ]
    tab_renderers = [
        render_project_overview,
        render_station_load,
        render_capacity_tracker,
        render_worker_coverage,
        render_self_test,
    ]

    tabs = st.tabs(tab_labels)
    for tab, renderer in zip(tabs, tab_renderers):
        with tab:
            renderer(driver)


if __name__ == "__main__":
    main()