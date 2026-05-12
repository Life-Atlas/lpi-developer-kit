import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.set_page_config(
    page_title="Factory Knowledge Graph Dashboard",
    layout="wide"
)

# ---------------- CUSTOM STYLING ----------------

st.markdown("""
<style>

.stApp {
    background: linear-gradient(to right, #0f172a, #111827);
    color: white;
}

h1, h2, h3 {
    color: #f8fafc;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

[data-testid="stMetricValue"] {
    color: #38bdf8;
}

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------

st.title("🏭 Factory Knowledge Graph Dashboard")
st.caption("Neo4j + Streamlit Production Intelligence System")

# ---------------- SIDEBAR ----------------

st.sidebar.title("📊 Navigation")

page = st.sidebar.selectbox(
    "Select Page",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Self-Test"
    ]
)

# =========================================================
# PROJECT OVERVIEW
# =========================================================

if page == "Project Overview":

    st.header("📁 Project Overview")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN p.name AS project,
           sum(r.planned_hours) AS planned,
           sum(r.actual_hours) AS actual
    """

    with driver.session() as session:
        result = session.run(query)
        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    df["variance_pct"] = (
        (df["actual"] - df["planned"]) / df["planned"]
    ) * 100

    total_projects = len(df)
    total_planned = round(df["planned"].sum(), 1)
    total_actual = round(df["actual"].sum(), 1)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Projects", total_projects)
    col2.metric("Planned Hours", total_planned)
    col3.metric("Actual Hours", total_actual)

    st.markdown("---")

    fig = px.bar(
        df,
        x="project",
        y=["planned", "actual"],
        barmode="group",
        title="Project Planned vs Actual Hours"
    )

    fig.update_layout(
        template="plotly_dark",
        height=550
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df)

# =========================================================
# STATION LOAD
# =========================================================

elif page == "Station Load":

    st.header("🏗 Station Load Analysis")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS station,
           sum(r.planned_hours) AS planned,
           sum(r.actual_hours) AS actual
    """

    with driver.session() as session:
        result = session.run(query)
        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    df["overloaded"] = df["actual"] > df["planned"]

    fig = px.bar(
        df,
        x="station",
        y=["planned", "actual"],
        barmode="group",
        title="Planned vs Actual Hours by Station"
    )

    fig.update_layout(
        template="plotly_dark",
        height=550
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df)

# =========================================================
# CAPACITY TRACKER
# =========================================================

elif page == "Capacity Tracker":

    st.header("📈 Capacity Tracker")

    query = """
    MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
    RETURN w.name AS week,
           c.total_capacity AS capacity,
           c.total_planned AS planned,
           c.deficit AS deficit
    ORDER BY week
    """

    with driver.session() as session:
        result = session.run(query)
        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    deficit_weeks = len(df[df["deficit"] < 0])

    col1, col2 = st.columns(2)

    col1.metric("Total Weeks", len(df))
    col2.metric("Deficit Weeks", deficit_weeks)

    fig = px.line(
        df,
        x="week",
        y=["capacity", "planned"],
        markers=True,
        title="Capacity vs Planned Demand"
    )

    fig.update_layout(
        template="plotly_dark",
        height=550
    )

    st.plotly_chart(fig, use_container_width=True)

    def color_deficit(val):
        color = "red" if val < 0 else "lightgreen"
        return f"color: {color}"

    st.dataframe(
        df.style.map(color_deficit, subset=["deficit"])
    )

# =========================================================
# WORKER COVERAGE
# =========================================================

elif page == "Worker Coverage":

    st.header("👷 Worker Coverage Matrix")

    query = """
    MATCH (w:Worker)-[:WORKS_AT]->(s:Station)
    RETURN w.name AS worker,
           w.role AS role,
           s.code AS station
    """

    with driver.session() as session:
        result = session.run(query)
        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    total_workers = len(df)

    st.metric("Total Workers", total_workers)

    st.markdown("---")

    st.dataframe(df)

# =========================================================
# SELF TEST
# =========================================================

elif page == "Self-Test":

    st.header("🧪 Self-Test")

    def run_self_test(driver):

        checks = []

        try:
            with driver.session() as s:
                s.run("RETURN 1")

            checks.append(("Neo4j connected", True, 3))

        except:
            checks.append(("Neo4j connected", False, 3))
            return checks

        with driver.session() as s:

            result = s.run("MATCH (n) RETURN count(n) AS c").single()
            count = result["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))

            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))

            result = s.run(
                "CALL db.labels() YIELD label RETURN count(label) AS c"
            ).single()

            count = result["c"]

            checks.append(
                (f"{count} node labels (min: 6)", count >= 6, 3)
            )

            result = s.run(
                """
                CALL db.relationshipTypes()
                YIELD relationshipType
                RETURN count(relationshipType) AS c
                """
            ).single()

            count = result["c"]

            checks.append(
                (f"{count} relationship types (min: 8)", count >= 8, 3)
            )

            result = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project
                LIMIT 10
            """)

            rows = [dict(r) for r in result]

            checks.append(
                (f"Variance query: {len(rows)} results", len(rows) > 0, 5)
            )

        return checks

    checks = run_self_test(driver)

    total = 0

    for label, passed, points in checks:

        if passed:
            st.success(f"✅ {label}   {points}/{points}")
            total += points

        else:
            st.error(f"❌ {label}   0/{points}")

    st.markdown("---")

    st.subheader(f"🎯 SELF-TEST SCORE: {total}/20")

driver.close()