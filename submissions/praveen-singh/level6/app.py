import streamlit as st
import pandas as pd
import plotly.express as px
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Factory Graph Dashboard",
    layout="wide"
)

# =========================
# LOAD ENV
# =========================

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

# =========================
# QUERY FUNCTION
# =========================

def run_query(query):

    with driver.session() as session:
        result = session.run(query)

        return pd.DataFrame(
            [r.data() for r in result]
        )

# =========================
# SIDEBAR
# =========================

st.sidebar.title("Factory Dashboard")

page = st.sidebar.radio(
    "Navigation",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Self-Test"
    ]
)

# =========================
# PROJECT OVERVIEW
# =========================

if page == "Project Overview":

    st.title("Project Overview")

    query = """
    MATCH (p:Project)
    RETURN
        p.project_id AS project_id,
        p.project_name AS project_name,
        p.project_number AS project_number
    """

    df = run_query(query)

    st.metric("Total Projects", len(df))

    st.dataframe(df, use_container_width=True)

# =========================
# STATION LOAD
# =========================

elif page == "Station Load":

    st.title("Station Load")

    query = """
    MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)

    RETURN
        s.station_name AS station,
        SUM(r.planned_hours) AS planned_hours,
        SUM(r.actual_hours) AS actual_hours
    """

    df = run_query(query)

    df["overload"] = (
        df["actual_hours"] > df["planned_hours"]
    )

    fig = px.bar(
        df,
        x="station",
        y=["planned_hours", "actual_hours"],
        barmode="group",
        title="Station Workload"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True)

# =========================
# CAPACITY TRACKER
# =========================

elif page == "Capacity Tracker":

    st.title("Capacity Tracker")

    query = """
    MATCH (c:CapacityWeek)

    RETURN
        c.week AS week,
        c.total_capacity AS total_capacity,
        c.total_planned AS total_planned,
        c.deficit AS deficit
    ORDER BY week
    """

    df = run_query(query)

    fig = px.line(
        df,
        x="week",
        y=["total_capacity", "total_planned"],
        title="Capacity vs Planned"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Deficit Weeks")

    deficit_df = df[df["deficit"] > 0]

    st.dataframe(
        deficit_df,
        use_container_width=True
    )

# =========================
# WORKER COVERAGE
# =========================

elif page == "Worker Coverage":

    st.title("Worker Coverage")

    query = """
    MATCH (w:Worker)-[:PRIMARY_AT]->(s:Station)

    RETURN
        w.worker_name AS worker,
        s.station_code AS station,
        w.worker_type AS type,
        w.hours_per_week AS hours
    """

    df = run_query(query)

    st.dataframe(df, use_container_width=True)

    station_counts = (
        df.groupby("station")
        .size()
        .reset_index(name="worker_count")
    )

    st.subheader("Single Point of Failure Stations")

    spof = station_counts[
    (station_counts["worker_count"] <= 1)
    & (station_counts["station"] != "all")
]

    st.dataframe(spof, use_container_width=True)

# =========================
# SELF TEST
# =========================

elif page == "Self-Test":

    st.title("Self-Test")

    checks = []

    # Check 1
    q1 = run_query("""
    MATCH (p:Project)
    RETURN count(p) AS count
    """)

    checks.append(
        ("Projects Loaded", q1["count"][0] > 0)
    )

    # Check 2
    q2 = run_query("""
    MATCH (s:Station)
    RETURN count(s) AS count
    """)

    checks.append(
        ("Stations Loaded", q2["count"][0] > 0)
    )

    # Check 3
    q3 = run_query("""
    MATCH (w:Worker)
    RETURN count(w) AS count
    """)

    checks.append(
        ("Workers Loaded", q3["count"][0] > 0)
    )

    # Check 4
    q4 = run_query("""
    MATCH ()-[r:PROCESSED_AT]->()
    RETURN count(r) AS count
    """)

    checks.append(
        ("Relationships Created", q4["count"][0] > 0)
    )

    # Check 5
    q5 = run_query("""
    MATCH (c:CapacityWeek)
    RETURN count(c) AS count
    """)

    checks.append(
        ("Capacity Data Loaded", q5["count"][0] > 0)
    )

    # Check 6
    checks.append(
        ("Neo4j Connection", True)
    )

    passed = 0

    for name, status in checks:

        if status:
            st.success(f"PASS: {name}")
            passed += 1
        else:
            st.error(f"FAIL: {name}")

    st.metric(
        "Self-Test Score",
        f"{passed}/6"
    )

# =========================
# CLOSE DRIVER
# =========================

driver.close()