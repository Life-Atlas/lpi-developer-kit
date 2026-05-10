"""Streamlit dashboard for the Level 6 factory Neo4j graph."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Factory Graph Dashboard",
    page_icon="🏭",
    layout="wide",
)


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


def render_connection_help() -> None:
    st.error("Neo4j credentials are not configured.")
    st.markdown(
        """
        Add these values either to a local `.env` file or to Streamlit Cloud
        **Settings → Secrets** before running the dashboard:

        ```toml
        NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "your-password"
        ```
        """
    )


def run_self_test(driver):
    checks = []
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        checks.append(("Neo4j connected", True, 3))
    except Exception as exc:  # noqa: BLE001 - Streamlit should show the failed check instead of crashing.
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


def render_project_overview(driver) -> None:
    st.header("Project Overview")
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
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Projects", len(df))
    col2.metric("Planned hours", f"{total_planned:,.1f}")
    col3.metric("Actual hours", f"{total_actual:,.1f}", f"{variance_pct:+.1f}%")
    col4.metric("Projects >10% variance", int((df["variance_pct"] > 10).sum()))

    display = df.copy()
    display["products"] = display["products"].apply(lambda values: ", ".join(values))
    display["stations"] = display["stations"].apply(lambda values: ", ".join(values))
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

    fig = px.bar(
        df,
        x="project_name",
        y=["planned_hours", "actual_hours"],
        barmode="group",
        title="Planned vs actual hours by project",
    )
    fig.update_layout(xaxis_title="Project", yaxis_title="Hours")
    st.plotly_chart(fig, use_container_width=True)


def render_station_load(driver) -> None:
    st.header("Station Load")
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

    station_options = ["All stations", *df["station_name"].drop_duplicates().tolist()]
    selected = st.selectbox("Station filter", station_options)
    chart_df = df if selected == "All stations" else df[df["station_name"] == selected]

    melted = chart_df.melt(
        id_vars=["station_code", "station_name", "week"],
        value_vars=["planned_hours", "actual_hours"],
        var_name="metric",
        value_name="hours",
    )
    fig = px.bar(
        melted,
        x="week",
        y="hours",
        color="metric",
        facet_col="station_name" if selected == "All stations" else None,
        facet_col_wrap=3,
        barmode="group",
        hover_data=["station_code"],
        title="Weekly planned vs actual station load",
    )
    fig.update_layout(height=760 if selected == "All stations" else 460)
    st.plotly_chart(fig, use_container_width=True)

    overrun_df = df[df["actual_hours"] > df["planned_hours"]].copy()
    st.subheader("Rows where actual hours exceed planned hours")
    st.dataframe(overrun_df, use_container_width=True, hide_index=True)


def render_capacity_tracker(driver) -> None:
    st.header("Capacity Tracker")
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
    col1, col2, col3 = st.columns(3)
    col1.metric("Weeks tracked", len(df))
    col2.metric("Deficit weeks", deficit_weeks)
    col3.metric("Worst deficit", f"{df['deficit'].min():,.0f} hours")

    fig = px.line(
        df,
        x="week",
        y=["total_capacity", "total_planned"],
        markers=True,
        title="Total capacity vs planned demand",
    )
    deficit_points = df[df["deficit"] < 0]
    fig.add_scatter(
        x=deficit_points["week"],
        y=deficit_points["total_planned"],
        mode="markers",
        marker={"color": "red", "size": 13, "symbol": "x"},
        name="Deficit week",
    )
    st.plotly_chart(fig, use_container_width=True)

    styled = df.drop(columns=["sort_order"]).style.apply(
        lambda row: ["background-color: #ffd6d6" if row["deficit"] < 0 else "" for _ in row],
        axis=1,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_worker_coverage(driver) -> None:
    st.header("Worker Coverage")
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
    col1, col2, col3 = st.columns(3)
    col1.metric("Workers", len(matrix))
    col2.metric("Stations", len(coverage))
    col3.metric("Single-point-of-failure stations", len(spof))

    coverage_display = coverage.copy()
    coverage_display["workers"] = coverage_display["workers"].apply(lambda values: ", ".join(values))
    styled = coverage_display.style.apply(
        lambda row: ["background-color: #ffd6d6" if row["certified_workers"] <= 1 else "" for _ in row],
        axis=1,
    )
    st.subheader("Station certification coverage")
    st.dataframe(styled, use_container_width=True, hide_index=True)

    all_stations = sorted(coverage["station_code"].dropna().unique().tolist())
    matrix_rows = []
    for _, row in matrix.iterrows():
        covered = set(row["stations"])
        matrix_rows.append({"worker": row["worker"], **{station: station in covered for station in all_stations}})
    matrix_df = pd.DataFrame(matrix_rows)
    st.subheader("Worker-to-station matrix")
    st.dataframe(matrix_df, use_container_width=True, hide_index=True)


def render_self_test(driver) -> None:
    st.header("Self-Test")
    st.caption("Automated checks required by the Level 6 challenge.")
    checks = run_self_test(driver)
    earned = 0
    possible = sum(points for _, _, points in checks)
    for label, passed, points in checks:
        if passed:
            earned += points
        st.markdown(f"{'✅' if passed else '❌'} **{label}** — `{points if passed else 0}/{points}`")
    st.divider()
    st.subheader(f"SELF-TEST SCORE: {earned}/{possible}")
    st.progress(earned / possible if possible else 0)


def main() -> None:
    st.title("🏭 Factory Graph Dashboard")
    st.caption("Level 6: Neo4j knowledge graph + Streamlit dashboard")
    driver = get_driver()
    if driver is None:
        render_connection_help()
        return

    pages = {
        "Project Overview": render_project_overview,
        "Station Load": render_station_load,
        "Capacity Tracker": render_capacity_tracker,
        "Worker Coverage": render_worker_coverage,
        "Self-Test": render_self_test,
    }
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    st.sidebar.info("All dashboard pages query Neo4j directly; CSV files are used only by seed_graph.py.")
    pages[selected_page](driver)


if __name__ == "__main__":
    main()
