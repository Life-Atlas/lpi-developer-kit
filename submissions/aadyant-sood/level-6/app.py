import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
from dotenv import load_dotenv

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(
    page_title="Factory Knowledge Graph Dashboard",
    layout="wide"
)

load_dotenv()

# ==========================================================
# CONNECTION
# ==========================================================

@st.cache_resource
def get_driver():
    try:
        uri = st.secrets["NEO4J_URI"]
        username = st.secrets["NEO4J_USERNAME"]
        password = st.secrets["NEO4J_PASSWORD"]
    except:
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

    return GraphDatabase.driver(uri, auth=(username, password))


def run_query(cypher):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher)
        return [dict(r) for r in result]


# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.title("Factory Dashboard")

page = st.sidebar.radio(
    "Navigate",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Production Forecast",
        "Self-Test"
    ]
)

# ==========================================================
# PROJECT OVERVIEW
# ==========================================================

if page == "Project Overview":

    st.title("📦 Project Overview")
    st.caption("Project performance across production workflow.")

    rows = run_query("""
    MATCH (p:Project)-[r:SCHEDULED_AT]->()
    RETURN
        p.project_name AS project,
        SUM(r.planned_hours) AS planned,
        SUM(r.actual_hours) AS actual
    ORDER BY project
    """)

    df = pd.DataFrame(rows)

    df["variance"] = (
        ((df["actual"] - df["planned"]) / df["planned"]) * 100
    ).round(2)

    c1, c2, c3 = st.columns(3)

    c1.metric("Projects", len(df))
    c2.metric("Total Planned Hours", int(df["planned"].sum()))
    c3.metric("Total Actual Hours", int(df["actual"].sum()))

    fig = px.bar(
        df,
        x="project",
        y=["planned", "actual"],
        barmode="group",
        title="Planned vs Actual Hours by Project"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True)

# ==========================================================
# STATION LOAD
# ==========================================================

elif page == "Station Load":

    st.title("🏭 Station Load")
    st.caption("Detect overloaded stations.")

    rows = run_query("""
    MATCH (:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN
        s.station_name AS station,
        r.week AS week,
        SUM(r.planned_hours) AS planned,
        SUM(r.actual_hours) AS actual
    """)

    df = pd.DataFrame(rows)

    df["status"] = np.where(
        df["actual"] > df["planned"],
        "Overloaded",
        "Normal"
    )

    fig = px.bar(
        df,
        x="station",
        y="actual",
        color="status",
        hover_data=["planned", "week"],
        title="Station Load Analysis"
    )

    st.plotly_chart(fig, use_container_width=True)

    overloaded = df[df["status"] == "Overloaded"]

    if not overloaded.empty:
        st.warning("Overloaded stations detected")
        st.dataframe(overloaded, use_container_width=True)

# ==========================================================
# CAPACITY TRACKER
# ==========================================================

elif page == "Capacity Tracker":

    st.title("📈 Capacity Tracker")
    st.caption("Weekly workforce capacity vs production demand.")

    rows = run_query("""
    MATCH (w:Week)-[r:HAS_CAPACITY]->()
    RETURN
        w.week AS week,
        r.total_capacity AS capacity,
        r.total_planned AS planned,
        r.deficit AS deficit
    ORDER BY week
    """)

    df = pd.DataFrame(rows)

    fig1 = px.line(
        df,
        x="week",
        y=["capacity", "planned"],
        markers=True,
        title="Capacity vs Planned Work"
    )

    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(
        df,
        x="week",
        y="deficit",
        color="deficit",
        title="Weekly Deficit / Surplus"
    )

    st.plotly_chart(fig2, use_container_width=True)

    risk = df[df["deficit"] < 0]

    if not risk.empty:
        st.error("Capacity deficit weeks found")
        st.dataframe(risk, use_container_width=True)

# ==========================================================
# WORKER COVERAGE
# ==========================================================

elif page == "Worker Coverage":

    st.title("👷 Worker Coverage")
    st.caption("Backup staffing analysis.")

    rows = run_query("""
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
    RETURN
        s.station_name AS station,
        collect(w.name) AS workers,
        count(w) AS coverage
    ORDER BY coverage ASC
    """)

    df = pd.DataFrame(rows)

    df["risk"] = np.where(
        df["coverage"] == 1,
        "Single Point of Failure",
        "Healthy"
    )

    fig = px.bar(
        df,
        x="station",
        y="coverage",
        color="risk",
        title="Coverage by Station"
    )

    st.plotly_chart(fig, use_container_width=True)

    spof = df[df["coverage"] == 1]

    if not spof.empty:
        st.warning("Single Point of Failure detected")
        st.dataframe(spof, use_container_width=True)

    st.dataframe(df, use_container_width=True)

# ==========================================================
# BONUS FORECAST
# ==========================================================

elif page == "Production Forecast":

    st.title("🔮 Production Forecast")
    st.caption("Trend-based production load forecast.")

    rows = run_query("""
    MATCH (:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN
        s.station_name AS station,
        r.week AS week,
        SUM(r.actual_hours) AS actual
    """)

    df = pd.DataFrame(rows)

    df["week_num"] = df["week"].str.replace("w", "").astype(int)

    forecast_rows = []

    for station in df["station"].unique():

        temp = df[df["station"] == station].sort_values("week_num")

        if len(temp) < 2:
            continue

        x = temp["week_num"].values
        y = temp["actual"].values

        slope, intercept = np.polyfit(x, y, 1)

        predicted = slope * 9 + intercept

        residuals = y - (slope * x + intercept)
        uncertainty = np.std(residuals)

        forecast_rows.append({
            "station": station,
            "forecast": round(predicted, 2),
            "upper": round(predicted + uncertainty, 2),
            "lower": round(predicted - uncertainty, 2)
        })

    forecast_df = pd.DataFrame(forecast_rows)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=forecast_df["station"],
        y=forecast_df["forecast"],
        name="Forecast"
    ))

    fig.add_trace(go.Scatter(
        x=forecast_df["station"],
        y=forecast_df["upper"],
        mode="lines",
        name="Upper Bound"
    ))

    fig.add_trace(go.Scatter(
        x=forecast_df["station"],
        y=forecast_df["lower"],
        mode="lines",
        fill="tonexty",
        name="Confidence Band"
    ))

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(forecast_df, use_container_width=True)

# ==========================================================
# SELF TEST
# ==========================================================

elif page == "Self-Test":

    st.title("✅ Self-Test")
    st.caption("Automated graph validation.")

    def self_test():

        score = 0
        checks = []

        driver = get_driver()

        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connection", True, 3))
            score += 3
        except:
            checks.append(("Neo4j connection", False, 3))
            return checks, score

        with driver.session() as s:

            node_count = s.run(
                "MATCH (n) RETURN count(n) AS c"
            ).single()["c"]

            checks.append(("Node count", node_count >= 50, 3))
            if node_count >= 50:
                score += 3

            rel_count = s.run(
                "MATCH ()-[r]->() RETURN count(r) AS c"
            ).single()["c"]

            checks.append(("Relationship count", rel_count >= 100, 3))
            if rel_count >= 100:
                score += 3

            labels = s.run(
                "CALL db.labels() YIELD label RETURN count(label) AS c"
            ).single()["c"]

            checks.append(("Node labels", labels >= 6, 3))
            if labels >= 6:
                score += 3

            rel_types = s.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"
            ).single()["c"]

            checks.append(("Relationship types", rel_types >= 8, 3))
            if rel_types >= 8:
                score += 3

            variance = list(s.run("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.project_name, s.station_name
            LIMIT 10
            """))

            checks.append(("Variance query", len(variance) > 0, 5))
            if len(variance) > 0:
                score += 5

        return checks, score

    checks, total = self_test()

    for label, passed, pts in checks:
        if passed:
            st.success(f"{label} ✅ ({pts}/{pts})")
        else:
            st.error(f"{label} ❌ (0/{pts})")

    st.divider()
    st.subheader(f"SELF-TEST SCORE: {total}/20")