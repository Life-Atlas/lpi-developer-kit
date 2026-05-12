"""
app.py — Level 6 Factory Knowledge Graph Dashboard
====================================================
Swedish steel fabrication factory · Neo4j 5.x · Streamlit · Plotly

Pages
-----
1. Project Overview    — project timeline heatmap (variance % by week)
2. Station Load        — planned vs actual hours, overrun highlighting
3. Capacity Tracker    — weekly capacity breakdown + deficit line
4. Worker Coverage     — coverage matrix with cert gaps
5. Self-Test           — full schema validation suite

Connection
----------
Reads credentials from (in priority order):
  1. Streamlit Cloud secrets  → st.secrets["NEO4J_URI"] etc.
  2. Local .env               → NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

Usage
-----
  pip install streamlit neo4j pandas plotly python-dotenv
  streamlit run app.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────────────────────────
import os
import textwrap
import traceback

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from neo4j import GraphDatabase, exceptions as neo4j_exc

# Load .env for local development (no-op if file absent or already set)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not required on Streamlit Cloud

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Factory Graph Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS — clean modern style
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Tighter header spacing */
        h1 { margin-bottom: 0.25rem !important; }
        h2 { margin-top: 1.5rem !important; margin-bottom: 0.25rem !important; }
        h3 { margin-top: 1rem !important; }

        /* Metric card accent */
        [data-testid="metric-container"] {
            background: #1e2130;
            border: 1px solid #2d3250;
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }

        /* Sidebar section headers */
        .sidebar-section {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #888;
            margin: 1rem 0 0.25rem;
        }

        /* Status badges */
        .badge-ok   { color: #22c55e; font-weight: 600; }
        .badge-warn { color: #f59e0b; font-weight: 600; }
        .badge-fail { color: #ef4444; font-weight: 600; }

        /* Divider */
        hr { border-color: #2d3250; margin: 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Neo4j connection helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_credentials() -> tuple[str, str, str]:
    """
    Resolve Neo4j credentials.

    Priority:
      1. Streamlit Cloud secrets  (st.secrets)
      2. Environment variables    (set by .env or shell)
    """
    try:
        uri  = st.secrets["NEO4J_URI"]
        user = st.secrets["NEO4J_USER"]
        pw   = st.secrets["NEO4J_PASSWORD"]
        return uri, user, pw
    except (KeyError, FileNotFoundError):
        pass

    uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pw   = os.getenv("NEO4J_PASSWORD", "")
    return uri, user, pw


@st.cache_resource(show_spinner="Connecting to Neo4j …")
def get_driver():
    """Return a cached Neo4j driver. Raises on auth failure."""
    uri, user, pw = _get_credentials()
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    driver.verify_connectivity()
    return driver


def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    """Execute a Cypher read query and return rows as list-of-dicts."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return [dict(record) for record in result]


# ─────────────────────────────────────────────────────────────────────────────
# Cached data loaders  (TTL = 5 min — avoid hammering DB on every widget tick)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_project_overview() -> pd.DataFrame:
    """
    Project × Week variance heatmap data.
    variance_pct = round(100*(actual-planned)/planned, 1)
    """
    cypher = """
    MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
    MATCH (entry)-[:SCHEDULED_IN]->(w:Week)
    WITH proj, w,
         sum(r.planned_hours) AS planned,
         sum(r.actual_hours)  AS actual
    RETURN
        proj.project_id                                       AS project_id,
        proj.project_name                                     AS project,
        proj.project_number                                   AS project_number,
        w.week_id                                             AS week,
        round(planned, 1)                                     AS planned_hours,
        round(actual,  1)                                     AS actual_hours,
        round(100.0 * (actual - planned) / planned, 1)        AS variance_pct
    ORDER BY proj.project_id, w.week_id
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_project_summary() -> pd.DataFrame:
    """Per-project total planned vs actual hours and entry count."""
    cypher = """
    MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
    WITH proj,
         count(DISTINCT entry) AS runs,
         round(sum(r.planned_hours), 1) AS total_planned,
         round(sum(r.actual_hours),  1) AS total_actual
    RETURN
        proj.project_number AS project_number,
        proj.project_name   AS project_name,
        proj.etapp          AS etapp,
        runs,
        total_planned,
        total_actual,
        round(100.0 * (total_actual - total_planned) / total_planned, 1) AS variance_pct
    ORDER BY proj.project_id
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_station_load() -> pd.DataFrame:
    """Station × Week: planned vs actual hours with delta."""
    cypher = """
    MATCH (entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
    MATCH (entry)-[:SCHEDULED_IN]->(w:Week)
    RETURN
        s.station_code                                           AS station_code,
        s.station_name                                           AS station_name,
        w.week_id                                                AS week,
        round(sum(r.planned_hours), 1)                           AS planned_hours,
        round(sum(r.actual_hours),  1)                           AS actual_hours,
        round(sum(r.actual_hours) - sum(r.planned_hours), 1)     AS delta,
        sum(r.completed_units)                                   AS completed_units
    ORDER BY w.week_id, s.station_code
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_overrun_entries() -> pd.DataFrame:
    """All entries where actual > planned * 1.10 (>10% overrun)."""
    cypher = """
    MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
    MATCH (entry)-[:SCHEDULED_IN]->(w:Week)
    WHERE r.actual_hours > r.planned_hours * 1.10
    WITH s, proj, entry, r, w,
         round(100.0 * (r.actual_hours - r.planned_hours) / r.planned_hours, 1) AS variance_pct
    RETURN
        s.station_code  AS station_code,
        s.station_name  AS station_name,
        proj.project_name AS project,
        w.week_id       AS week,
        r.planned_hours AS planned_hours,
        r.actual_hours  AS actual_hours,
        variance_pct
    ORDER BY variance_pct DESC
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_capacity() -> pd.DataFrame:
    """Weekly capacity snapshots."""
    cypher = """
    MATCH (w:Week)-[:HAS_SNAPSHOT]->(cs:CapacitySnapshot)
    RETURN
        w.week_id          AS week,
        cs.own_hours       AS own_hours,
        cs.hired_hours     AS hired_hours,
        cs.overtime_hours  AS overtime_hours,
        cs.total_capacity  AS total_capacity,
        cs.total_planned   AS total_planned,
        cs.deficit         AS deficit
    ORDER BY w.week_id
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_worker_coverage() -> pd.DataFrame:
    """Per-station primary workers, backup workers, and coverage depth."""
    cypher = """
    MATCH (s:Station)
    OPTIONAL MATCH (primary:Worker)-[:PRIMARILY_AT]->(s)
    OPTIONAL MATCH (backup:Worker)-[:CAN_COVER]->(s)
    WHERE backup IS NULL OR backup.worker_id <> primary.worker_id
    RETURN
        s.station_code                        AS station_code,
        s.station_name                        AS station_name,
        collect(DISTINCT primary.name)        AS primary_workers,
        collect(DISTINCT backup.name)         AS backup_workers
    ORDER BY s.station_code
    """
    rows = run_query(cypher)
    df = pd.DataFrame(rows)
    if not df.empty:
        # Remove nulls from list columns, compute coverage depth
        df["primary_workers"] = df["primary_workers"].apply(
            lambda lst: [x for x in lst if x] if isinstance(lst, list) else []
        )
        df["backup_workers"] = df["backup_workers"].apply(
            lambda lst: [x for x in lst if x] if isinstance(lst, list) else []
        )
        df["coverage_depth"] = df["backup_workers"].apply(len)
        df["primary_str"]    = df["primary_workers"].apply(", ".join)
        df["backup_str"]     = df["backup_workers"].apply(", ".join)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_worker_cert_gap() -> pd.DataFrame:
    """
    Stations that REQUIRE_CERT a certification for which NO worker
    currently HOLDS that cert via CAN_COVER.  These are coverage gaps.
    """
    cypher = """
    MATCH (s:Station)-[:REQUIRES_CERT]->(c:Certification)
    WHERE NOT EXISTS {
        MATCH (w:Worker)-[:CAN_COVER]->(s)
        MATCH (w)-[:HOLDS]->(c)
    }
    RETURN
        s.station_code AS station_code,
        s.station_name AS station_name,
        c.name         AS missing_cert,
        c.cert_id      AS cert_id
    ORDER BY s.station_code
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_worker_list() -> pd.DataFrame:
    """All workers with their primary station and cert count."""
    cypher = """
    MATCH (w:Worker)
    OPTIONAL MATCH (w)-[:PRIMARILY_AT]->(s:Station)
    OPTIONAL MATCH (w)-[:HOLDS]->(c:Certification)
    RETURN
        w.worker_id       AS worker_id,
        w.name            AS name,
        w.role            AS role,
        w.type            AS type,
        w.hours_per_week  AS hours_per_week,
        s.station_code    AS primary_station,
        s.station_name    AS primary_station_name,
        count(DISTINCT c) AS cert_count
    ORDER BY w.worker_id
    """
    rows = run_query(cypher)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ─────────────────────────────────────────────────────────────────────────────

PAGES = {
    "🗂️  Project Overview": "project_overview",
    "🏭  Station Load":     "station_load",
    "📊  Capacity Tracker": "capacity_tracker",
    "👷  Worker Coverage":  "worker_coverage",
    "🧪  Self-Test":        "self_test",
}

with st.sidebar:
    st.markdown("## 🏗️ Factory Dashboard")
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
    selection = st.radio(
        label="Page",
        options=list(PAGES.keys()),
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown('<div class="sidebar-section">Connection</div>', unsafe_allow_html=True)

    # Show live connection status in sidebar
    try:
        drv = get_driver()
        st.markdown('<span class="badge-ok">● Connected</span>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown('<span class="badge-fail">● Disconnected</span>', unsafe_allow_html=True)
        st.caption(str(e)[:120])

    st.markdown("---")
    st.caption("Neo4j 5.x · Streamlit · Plotly")

page = PAGES[selection]


# ─────────────────────────────────────────────────────────────────────────────
# Helper: connection error banner
# ─────────────────────────────────────────────────────────────────────────────

def show_connection_error(err: Exception):
    st.error(
        f"**Cannot reach Neo4j.**  \n"
        f"`{type(err).__name__}: {err}`  \n\n"
        "Check your `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in `.env` or Streamlit secrets."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — Project Overview
# ─────────────────────────────────────────────────────────────────────────────

if page == "project_overview":
    st.title("🗂️ Project Overview")
    st.caption("Variance heatmap across all projects and weeks · Data sourced from Neo4j only")

    try:
        df_summary = load_project_summary()
        df_heat    = load_project_overview()

        # ── KPI row ──────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projects", len(df_summary))
        c2.metric("Total Planned h", f"{df_summary['total_planned'].sum():,.0f}")
        c3.metric("Total Actual h",  f"{df_summary['total_actual'].sum():,.0f}")
        overall_var = (
            100.0
            * (df_summary["total_actual"].sum() - df_summary["total_planned"].sum())
            / df_summary["total_planned"].sum()
        )
        c4.metric("Overall Variance", f"{overall_var:+.1f}%")

        st.markdown("---")

        # ── Variance Heatmap ──────────────────────────────────────────────────
        st.subheader("Variance % · Project × Week")
        st.caption(
            "Red = over plan · Green = under plan · "
            "Cell value = (actual − planned) / planned × 100"
        )

        if not df_heat.empty:
            pivot = df_heat.pivot_table(
                index="project", columns="week", values="variance_pct", aggfunc="mean"
            )
            # Sort weeks naturally (w1 < w2 … w8)
            pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: int(x[1:])), axis=1)

            fig_heat = go.Figure(
                go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    colorscale=[
                        [0.0,  "#16a34a"],   # dark green  (most under)
                        [0.45, "#dcfce7"],   # light green
                        [0.5,  "#ffffff"],   # white        (on target)
                        [0.55, "#fee2e2"],   # light red
                        [1.0,  "#dc2626"],   # dark red    (most over)
                    ],
                    zmid=0,
                    text=[[f"{v:+.1f}%" if v == v else "" for v in row] for row in pivot.values],
                    texttemplate="%{text}",
                    hovertemplate="<b>%{y}</b><br>Week: %{x}<br>Variance: %{z:+.1f}%<extra></extra>",
                    colorbar=dict(title="Variance %"),
                )
            )
            fig_heat.update_layout(
                height=420,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="Week",
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("---")

        # ── Project summary table ─────────────────────────────────────────────
        st.subheader("Project Summary")

        def _colour_variance(val):
            if isinstance(val, float):
                if val > 10:
                    return "color: #ef4444; font-weight:600"
                if val > 0:
                    return "color: #f59e0b"
                return "color: #22c55e"
            return ""

        styled = (
            df_summary.rename(columns={
                "project_number": "Number",
                "project_name":   "Name",
                "etapp":          "Etapp",
                "runs":           "Runs",
                "total_planned":  "Planned h",
                "total_actual":   "Actual h",
                "variance_pct":   "Variance %",
            })
            .style
            .map(_colour_variance, subset=["Variance %"])
            .format({"Planned h": "{:.1f}", "Actual h": "{:.1f}", "Variance %": "{:+.1f}"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Planned vs Actual bar per project ────────────────────────────────
        st.subheader("Planned vs Actual Hours per Project")
        fig_bar = go.Figure()
        fig_bar.add_bar(
            name="Planned",
            x=df_summary["project_name"],
            y=df_summary["total_planned"],
            marker_color="#3b82f6",
        )
        fig_bar.add_bar(
            name="Actual",
            x=df_summary["project_name"],
            y=df_summary["total_actual"],
            marker_color="#f97316",
        )
        fig_bar.update_layout(
            barmode="group",
            height=380,
            margin=dict(l=20, r=20, t=30, b=80),
            legend=dict(orientation="h", y=1.05),
            xaxis_tickangle=-30,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            yaxis_title="Hours",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as err:
        show_connection_error(err)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — Station Load
# ─────────────────────────────────────────────────────────────────────────────

elif page == "station_load":
    st.title("🏭 Station Load")
    st.caption("Planned vs actual hours per station · Overruns highlighted")

    try:
        df_load    = load_station_load()
        df_overrun = load_overrun_entries()

        if df_load.empty:
            st.info("No station load data found.")
        else:
            # ── Filters ──────────────────────────────────────────────────────
            col_f1, col_f2 = st.columns(2)
            weeks    = sorted(df_load["week"].unique(), key=lambda x: int(x[1:]))
            stations = sorted(df_load["station_code"].unique())

            sel_weeks = col_f1.multiselect("Filter Weeks", weeks, default=weeks)
            sel_sta   = col_f2.multiselect("Filter Stations", stations, default=stations)

            mask = df_load["week"].isin(sel_weeks) & df_load["station_code"].isin(sel_sta)
            df_f = df_load[mask].copy()

            # ── KPI row ───────────────────────────────────────────────────────
            overloaded = df_f[df_f["delta"] > 0]["station_code"].nunique()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Stations (filtered)", df_f["station_code"].nunique())
            c2.metric("Overloaded Stations", overloaded,
                      delta_color="inverse", delta=f"{overloaded} overloaded")
            c3.metric("Total Planned h",  f"{df_f['planned_hours'].sum():,.0f}")
            c4.metric("Total Actual h",   f"{df_f['actual_hours'].sum():,.0f}")

            st.markdown("---")

            # ── Grouped bar chart: planned vs actual ─────────────────────────
            st.subheader("Planned vs Actual by Station & Week")

            fig_load = go.Figure()
            color_map_planned = "#3b82f6"
            color_map_actual  = "#f97316"

            for week in sorted(sel_weeks, key=lambda x: int(x[1:])):
                wdf = df_f[df_f["week"] == week]
                fig_load.add_bar(
                    name=f"{week} Planned",
                    x=wdf["station_code"] + " " + wdf["station_name"].str[:12],
                    y=wdf["planned_hours"],
                    marker_color=color_map_planned,
                    opacity=0.7,
                    legendgroup=week,
                    legendgrouptitle_text=week if week == sorted(sel_weeks, key=lambda x: int(x[1:]))[0] else None,
                )
                # Colour actual bars: red if delta > 0 else green
                bar_colours = [
                    "#ef4444" if d > 0 else "#22c55e"
                    for d in wdf["delta"].tolist()
                ]
                fig_load.add_bar(
                    name=f"{week} Actual",
                    x=wdf["station_code"] + " " + wdf["station_name"].str[:12],
                    y=wdf["actual_hours"],
                    marker_color=bar_colours,
                    legendgroup=week,
                )

            fig_load.update_layout(
                barmode="group",
                height=430,
                margin=dict(l=20, r=20, t=30, b=90),
                xaxis_tickangle=-35,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                yaxis_title="Hours",
                legend=dict(orientation="h", y=1.05, font_size=10),
            )
            st.plotly_chart(fig_load, use_container_width=True)

            # ── Delta heatmap: station × week ─────────────────────────────────
            st.subheader("Delta Hours Heatmap  (actual − planned)")
            pivot_delta = df_f.pivot_table(
                index="station_name", columns="week", values="delta", aggfunc="sum"
            )
            pivot_delta = pivot_delta.reindex(
                sorted(pivot_delta.columns, key=lambda x: int(x[1:])), axis=1
            )
            fig_dh = go.Figure(
                go.Heatmap(
                    z=pivot_delta.values,
                    x=pivot_delta.columns.tolist(),
                    y=pivot_delta.index.tolist(),
                    colorscale=[[0, "#16a34a"], [0.5, "#ffffff"], [1, "#dc2626"]],
                    zmid=0,
                    text=[[f"{v:+.1f}" if v == v else "" for v in row] for row in pivot_delta.values],
                    texttemplate="%{text}",
                    hovertemplate="<b>%{y}</b><br>%{x}<br>Δ = %{z:+.1f} h<extra></extra>",
                    colorbar=dict(title="Δ Hours"),
                )
            )
            fig_dh.update_layout(
                height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
            )
            st.plotly_chart(fig_dh, use_container_width=True)

            st.markdown("---")

            # ── Overrun detail table ───────────────────────────────────────────
            st.subheader("⚠️ Entries >10% Over Plan")
            if df_overrun.empty:
                st.success("No entries exceed 10% overrun threshold.")
            else:
                def _red(val):
                    if isinstance(val, float) and val > 20:
                        return "color:#ef4444;font-weight:600"
                    if isinstance(val, float) and val > 10:
                        return "color:#f59e0b"
                    return ""

                styled_ov = (
                    df_overrun.rename(columns={
                        "station_code": "Station",
                        "station_name": "Station Name",
                        "project":      "Project",
                        "week":         "Week",
                        "planned_hours": "Planned h",
                        "actual_hours":  "Actual h",
                        "variance_pct":  "Variance %",
                    })
                    .style
                    .map(_red, subset=["Variance %"])
                    .format({"Planned h": "{:.1f}", "Actual h": "{:.1f}", "Variance %": "{:+.1f}"})
                )
                st.dataframe(styled_ov, use_container_width=True, hide_index=True)

    except Exception as err:
        show_connection_error(err)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3 — Capacity Tracker
# ─────────────────────────────────────────────────────────────────────────────

elif page == "capacity_tracker":
    st.title("📊 Capacity Tracker")
    st.caption("Weekly factory capacity vs planned demand · Deficit weeks highlighted")

    try:
        df_cap = load_capacity()

        if df_cap.empty:
            st.info("No capacity data found.")
        else:
            # ── KPI row ────────────────────────────────────────────────────────
            deficit_weeks = df_cap[df_cap["deficit"] < 0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Weeks Tracked",   len(df_cap))
            c2.metric("Deficit Weeks",   len(deficit_weeks))
            c3.metric("Avg Capacity h",  f"{df_cap['total_capacity'].mean():,.0f}")
            c4.metric("Avg Planned h",   f"{df_cap['total_planned'].mean():,.0f}")

            st.markdown("---")

            # ── Stacked bar + planned line ────────────────────────────────────
            st.subheader("Capacity Breakdown vs Demand")

            fig_cap = go.Figure()

            # Stacked bars: own / hired / overtime
            fig_cap.add_bar(
                name="Own Hours",
                x=df_cap["week"],
                y=df_cap["own_hours"],
                marker_color="#3b82f6",
            )
            fig_cap.add_bar(
                name="Hired Hours",
                x=df_cap["week"],
                y=df_cap["hired_hours"],
                marker_color="#8b5cf6",
            )
            fig_cap.add_bar(
                name="Overtime Hours",
                x=df_cap["week"],
                y=df_cap["overtime_hours"],
                marker_color="#f59e0b",
            )

            # Planned demand line
            fig_cap.add_scatter(
                name="Planned Demand",
                x=df_cap["week"],
                y=df_cap["total_planned"],
                mode="lines+markers",
                line=dict(color="#f97316", width=3, dash="dot"),
                marker=dict(size=8),
            )

            # Shade deficit weeks with a vertical rectangle
            for _, row in deficit_weeks.iterrows():
                fig_cap.add_vrect(
                    x0=row["week"], x1=row["week"],
                    fillcolor="rgba(239,68,68,0.12)",
                    layer="below",
                    line_width=0,
                )

            fig_cap.update_layout(
                barmode="stack",
                height=430,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", y=1.05),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                yaxis_title="Hours",
                xaxis_title="Week",
            )
            st.plotly_chart(fig_cap, use_container_width=True)

            # ── Deficit bar ───────────────────────────────────────────────────
            st.subheader("Deficit / Surplus per Week")
            bar_cols = ["#ef4444" if d < 0 else "#22c55e" for d in df_cap["deficit"]]
            fig_def = go.Figure(
                go.Bar(
                    x=df_cap["week"],
                    y=df_cap["deficit"],
                    marker_color=bar_cols,
                    hovertemplate="Week: %{x}<br>Deficit: %{y:+.0f} h<extra></extra>",
                )
            )
            fig_def.add_hline(y=0, line_color="#888", line_dash="dash")
            fig_def.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                yaxis_title="Surplus / Deficit (h)",
            )
            st.plotly_chart(fig_def, use_container_width=True)

            st.markdown("---")

            # ── Raw capacity table ────────────────────────────────────────────
            st.subheader("Raw Capacity Data")

            def _cap_colour(val):
                if isinstance(val, (int, float)) and val < 0:
                    return "color:#ef4444;font-weight:600"
                return ""

            styled_cap = (
                df_cap.rename(columns={
                    "week":           "Week",
                    "own_hours":      "Own h",
                    "hired_hours":    "Hired h",
                    "overtime_hours": "Overtime h",
                    "total_capacity": "Capacity h",
                    "total_planned":  "Planned h",
                    "deficit":        "Deficit h",
                })
                .style
                .map(_cap_colour, subset=["Deficit h"])
            )
            st.dataframe(styled_cap, use_container_width=True, hide_index=True)

    except Exception as err:
        show_connection_error(err)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4 — Worker Coverage
# ─────────────────────────────────────────────────────────────────────────────

elif page == "worker_coverage":
    st.title("👷 Worker Coverage")
    st.caption("Station coverage matrix · Certification gaps · Worker roster")

    try:
        df_cov     = load_worker_coverage()
        df_gap     = load_worker_cert_gap()
        df_workers = load_worker_list()

        # ── KPI row ────────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stations", len(df_cov))
        zero_cov = (df_cov["coverage_depth"] == 0).sum() if not df_cov.empty else 0
        c2.metric("Stations with No Backup", int(zero_cov))
        c3.metric("Workers", len(df_workers))
        c4.metric("Cert Gaps", len(df_gap))

        st.markdown("---")

        # ── Coverage depth bar ─────────────────────────────────────────────────
        st.subheader("Backup Coverage Depth per Station")
        if not df_cov.empty:
            col_depth = [
                "#ef4444" if d == 0 else "#f59e0b" if d <= 2 else "#22c55e"
                for d in df_cov["coverage_depth"]
            ]
            fig_cov = go.Figure(
                go.Bar(
                    x=df_cov["station_code"] + " · " + df_cov["station_name"],
                    y=df_cov["coverage_depth"],
                    marker_color=col_depth,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Backup workers: %{y}<extra></extra>"
                    ),
                )
            )
            fig_cov.add_hline(y=2, line_color="#888", line_dash="dash",
                              annotation_text="Min 2 backups", annotation_position="top right")
            fig_cov.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=30, b=90),
                xaxis_tickangle=-35,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                yaxis_title="Backup Count",
            )
            st.plotly_chart(fig_cov, use_container_width=True)

        # ── Coverage matrix table ──────────────────────────────────────────────
        st.subheader("Station Coverage Matrix")
        if not df_cov.empty:
            def _cov_depth(val):
                if isinstance(val, int):
                    if val == 0:
                        return "color:#ef4444;font-weight:600"
                    if val <= 2:
                        return "color:#f59e0b"
                    return "color:#22c55e"
                return ""

            styled_cov = (
                df_cov[["station_code", "station_name", "primary_str", "backup_str", "coverage_depth"]]
                .rename(columns={
                    "station_code":    "Code",
                    "station_name":    "Station",
                    "primary_str":     "Primary Workers",
                    "backup_str":      "Backup Workers",
                    "coverage_depth":  "Depth",
                })
                .style
                .map(_cov_depth, subset=["Depth"])
            )
            st.dataframe(styled_cov, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Certification gap table ────────────────────────────────────────────
        st.subheader("⚠️ Certification Gaps")
        st.caption("Stations that require a cert for which no covering worker is currently qualified.")
        if df_gap.empty:
            st.success("No certification gaps detected.")
        else:
            st.dataframe(
                df_gap.rename(columns={
                    "station_code": "Station Code",
                    "station_name": "Station",
                    "missing_cert": "Missing Certification",
                    "cert_id":      "Cert ID",
                }),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")

        # ── Worker roster ──────────────────────────────────────────────────────
        st.subheader("Worker Roster")
        if not df_workers.empty:
            st.dataframe(
                df_workers.rename(columns={
                    "worker_id":             "ID",
                    "name":                  "Name",
                    "role":                  "Role",
                    "type":                  "Type",
                    "hours_per_week":         "h/week",
                    "primary_station":        "Station Code",
                    "primary_station_name":   "Station Name",
                    "cert_count":             "Certs",
                }),
                use_container_width=True,
                hide_index=True,
            )

    except Exception as err:
        show_connection_error(err)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5 — Self-Test
# ─────────────────────────────────────────────────────────────────────────────

elif page == "self_test":
    st.title("🧪 Self-Test")
    st.caption(
        "Full schema validation suite · "
        "Checks connection, node counts, relationship counts, labels, types, and variance query."
    )

    # Expected schema constants (must match schema.md / seed_graph.py exactly)
    EXPECTED_LABELS = {
        "Project", "ProductionEntry", "Station", "Product",
        "Worker", "Week", "CapacitySnapshot", "Certification", "BOP",
    }

    EXPECTED_REL_TYPES = {
        "HAS_RUN", "USES_PRODUCT", "PROCESSED_AT", "SCHEDULED_IN",
        "REQUIRES_STATION", "STRUCTURED_BY", "PRIMARILY_AT", "CAN_COVER",
        "WORKED_ON", "HOLDS", "REQUIRES_CERT", "HAS_SNAPSHOT",
    }

    MIN_NODES = 50
    MIN_RELS  = 100

    def badge(ok: bool, ok_text: str = "PASS", fail_text: str = "FAIL") -> str:
        cls  = "badge-ok" if ok else "badge-fail"
        text = ok_text   if ok else fail_text
        return f'<span class="{cls}">{text}</span>'

    if st.button("▶ Run All Tests", type="primary"):
        results = []

        # ── Test 1: Neo4j connection ─────────────────────────────────────────
        with st.spinner("1/6 · Testing connection …"):
            try:
                drv = get_driver()
                conn_ok = True
                conn_msg = "Connected successfully"
            except Exception as e:
                conn_ok = False
                conn_msg = str(e)
            results.append(("Neo4j Connection", conn_ok, conn_msg))

        if conn_ok:

            # ── Test 2: Node labels ──────────────────────────────────────────
            with st.spinner("2/6 · Checking node labels …"):
                try:
                    rows = run_query("CALL db.labels() YIELD label RETURN label")
                    actual_labels = {r["label"] for r in rows}
                    missing = EXPECTED_LABELS - actual_labels
                    extra   = actual_labels - EXPECTED_LABELS
                    labels_ok = len(missing) == 0
                    label_msg = (
                        f"Found {len(actual_labels)} labels. "
                        + (f"Missing: {missing}" if missing else "All 9 expected labels present.")
                        + (f" Extra: {extra}" if extra else "")
                    )
                except Exception as e:
                    labels_ok = False
                    label_msg = str(e)
                results.append(("Node Labels (9 expected)", labels_ok, label_msg))

            # ── Test 3: Relationship types ───────────────────────────────────
            with st.spinner("3/6 · Checking relationship types …"):
                try:
                    rows = run_query("CALL db.relationshipTypes() YIELD relationshipType AS rel RETURN rel")
                    actual_rels = {r["rel"] for r in rows}
                    missing_r = EXPECTED_REL_TYPES - actual_rels
                    extra_r   = actual_rels - EXPECTED_REL_TYPES
                    rels_ok = len(missing_r) == 0
                    rel_msg = (
                        f"Found {len(actual_rels)} relationship types. "
                        + (f"Missing: {missing_r}" if missing_r else "All 12 expected types present.")
                        + (f" Extra: {extra_r}" if extra_r else "")
                    )
                except Exception as e:
                    rels_ok = False
                    rel_msg = str(e)
                results.append(("Relationship Types (12 expected)", rels_ok, rel_msg))

            # ── Test 4: Node count ───────────────────────────────────────────
            with st.spinner("4/6 · Counting nodes …"):
                node_counts = {}
                try:
                    for label in sorted(EXPECTED_LABELS):
                        rows = run_query(f"MATCH (n:{label}) RETURN count(n) AS c")
                        node_counts[label] = rows[0]["c"] if rows else 0
                    total_nodes = sum(node_counts.values())
                    count_ok = total_nodes >= MIN_NODES
                    count_msg_parts = [f"{lbl}: {cnt}" for lbl, cnt in sorted(node_counts.items())]
                    count_msg = f"Total: {total_nodes}  ({' · '.join(count_msg_parts)})"
                except Exception as e:
                    count_ok = False
                    count_msg = str(e)
                results.append((f"Node Count (≥ {MIN_NODES})", count_ok, count_msg))

            # ── Test 5: Relationship count ───────────────────────────────────
            with st.spinner("5/6 · Counting relationships …"):
                rel_counts = {}
                try:
                    for rel_type in sorted(EXPECTED_REL_TYPES):
                        rows = run_query(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c")
                        rel_counts[rel_type] = rows[0]["c"] if rows else 0
                    total_rels = sum(rel_counts.values())
                    rel_count_ok = total_rels >= MIN_RELS
                    rc_parts = [f"{t}: {c}" for t, c in sorted(rel_counts.items())]
                    rel_count_msg = f"Total: {total_rels}  ({' · '.join(rc_parts)})"
                except Exception as e:
                    rel_count_ok = False
                    rel_count_msg = str(e)
                results.append((f"Relationship Count (≥ {MIN_RELS})", rel_count_ok, rel_count_msg))

            # ── Test 6: Variance query (edge properties on PROCESSED_AT) ─────
            with st.spinner("6/6 · Running variance query …"):
                variance_cypher = textwrap.dedent("""
                    MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
                    WHERE r.actual_hours > r.planned_hours * 1.10
                    WITH s, proj, entry, r,
                         round(100.0 * (r.actual_hours - r.planned_hours) / r.planned_hours, 1) AS variance_pct
                    RETURN
                        s.station_code    AS station,
                        s.station_name    AS station_name,
                        count(*)          AS overrun_count
                    ORDER BY overrun_count DESC
                    LIMIT 5
                """).strip()
                try:
                    var_rows = run_query(variance_cypher)
                    var_ok  = len(var_rows) > 0
                    var_msg = (
                        f"Returned {len(var_rows)} stations with >10% overruns. "
                        "Top: " + (
                            ", ".join(
                                f"{r['station']} ({r['overrun_count']} entries)"
                                for r in var_rows[:3]
                            )
                        ) if var_rows else "No overrun entries found (graph may have perfect plan adherence)."
                    )
                except Exception as e:
                    var_ok  = False
                    var_msg = str(e)
                results.append(("Variance Query (PROCESSED_AT edge props)", var_ok, var_msg))

        # ── Render results ────────────────────────────────────────────────────
        st.markdown("---")
        passed = sum(1 for _, ok, _ in results if ok)
        total  = len(results)

        summary_cls = "badge-ok" if passed == total else "badge-warn" if passed >= total // 2 else "badge-fail"
        st.markdown(
            f'<h3>Results: <span class="{summary_cls}">{passed} / {total} passed</span></h3>',
            unsafe_allow_html=True,
        )

        for name, ok, msg in results:
            icon = "✅" if ok else "❌"
            with st.expander(f"{icon}  {name}", expanded=not ok):
                st.markdown(
                    badge(ok) + f"  {msg}",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # ── Node count breakdown chart ─────────────────────────────────────────
        if node_counts:
            st.subheader("Node Count Breakdown")
            nc_df = pd.DataFrame(
                [{"Label": k, "Count": v} for k, v in sorted(node_counts.items())]
            )
            fig_nc = px.bar(
                nc_df, x="Label", y="Count",
                color="Count",
                color_continuous_scale=["#3b82f6", "#22c55e"],
                text="Count",
            )
            fig_nc.update_traces(textposition="outside")
            fig_nc.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                showlegend=False,
                xaxis_tickangle=-30,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_nc, use_container_width=True)

        # ── Relationship count breakdown ───────────────────────────────────────
        if rel_counts:
            st.subheader("Relationship Count Breakdown")
            rc_df = pd.DataFrame(
                [{"Type": k, "Count": v} for k, v in sorted(rel_counts.items())]
            ).sort_values("Count", ascending=True)
            fig_rc = px.bar(
                rc_df, x="Count", y="Type",
                orientation="h",
                color="Count",
                color_continuous_scale=["#8b5cf6", "#f59e0b"],
                text="Count",
            )
            fig_rc.update_traces(textposition="outside")
            fig_rc.update_layout(
                height=360,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                showlegend=False,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_rc, use_container_width=True)

        # ── Raw variance query output ──────────────────────────────────────────
        if "var_rows" in dir() and var_rows:
            st.subheader("Variance Query Output (top stations by overrun count)")
            st.dataframe(
                pd.DataFrame(var_rows).rename(columns={
                    "station":       "Station Code",
                    "station_name":  "Station Name",
                    "overrun_count": "Overrun Entries",
                }),
                use_container_width=True,
                hide_index=True,
            )

    else:
        st.info("Click **▶ Run All Tests** to validate the graph schema against schema.md.")

        st.markdown("### Test Suite")
        tests = [
            ("1", "Neo4j Connection",
             "Verifies the driver can reach the database and authenticate."),
            ("2", "Node Labels",
             "Checks all 9 expected labels are present: Project, ProductionEntry, Station, "
             "Product, Worker, Week, CapacitySnapshot, Certification, BOP."),
            ("3", "Relationship Types",
             "Checks all 12 expected types: HAS_RUN, USES_PRODUCT, PROCESSED_AT, SCHEDULED_IN, "
             "REQUIRES_STATION, STRUCTURED_BY, PRIMARILY_AT, CAN_COVER, WORKED_ON, HOLDS, "
             "REQUIRES_CERT, HAS_SNAPSHOT."),
            ("4", f"Node Count (≥ {MIN_NODES})",
             "Per-label counts, total must reach 50+ nodes."),
            ("5", f"Relationship Count (≥ {MIN_RELS})",
             "Per-type counts, total must reach 100+ relationships."),
            ("6", "Variance Query",
             "Runs the full overrun detection query against PROCESSED_AT edge properties "
             "(planned_hours, actual_hours). Confirms edge data is hydrated."),
        ]
        for num, name, desc in tests:
            with st.expander(f"Test {num} — {name}"):
                st.write(desc)
