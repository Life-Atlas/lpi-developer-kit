import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import os

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Factory Knowledge Graph Dashboard",
    layout="wide"
)

# =====================================================
# LOAD ENV VARIABLES
# =====================================================

load_dotenv(".env")

try:
    URI = st.secrets["NEO4J_URI"]
    USERNAME = st.secrets["NEO4J_USERNAME"]
    PASSWORD = st.secrets["NEO4J_PASSWORD"]

except:
    URI = os.getenv("NEO4J_URI")
    USERNAME = os.getenv("NEO4J_USERNAME")
    PASSWORD = os.getenv("NEO4J_PASSWORD")

URI = URI.replace("neo4j+s://", "neo4j+ssc://")

# =====================================================
# CONNECT TO NEO4J
# =====================================================

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("Factory Dashboard")

page = st.sidebar.radio(
    "Navigate",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Self-Test"
    ]
)

# =====================================================
# PROJECT OVERVIEW
# =====================================================

if page == "Project Overview":

    st.title("📦 Project Overview")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)

    RETURN
        p.project_name AS project,
        SUM(r.planned_hours) AS planned_hours,
        SUM(r.actual_hours) AS actual_hours,
        ROUND(
            ((SUM(r.actual_hours) - SUM(r.planned_hours))
            / SUM(r.planned_hours)) * 100,
            2
        ) AS variance_percent
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(record) for record in result]

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

# =====================================================
# STATION LOAD
# =====================================================

elif page == "Station Load":

    st.title("🏭 Station Load")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)

    RETURN
        s.station_name AS station,
        r.week AS week,
        SUM(r.planned_hours) AS planned_hours,
        SUM(r.actual_hours) AS actual_hours
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(record) for record in result]

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="station",
        y="actual_hours",
        color="week",
        barmode="group",
        hover_data=["planned_hours"]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True)

# =====================================================
# CAPACITY TRACKER
# =====================================================

elif page == "Capacity Tracker":

    st.title("📈 Capacity Tracker")

    query = """
    MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)

    RETURN
        w.week AS week,
        c.total_capacity AS total_capacity,
        c.total_planned AS total_planned,
        c.deficit AS deficit
    ORDER BY w.week
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(record) for record in result]

    df = pd.DataFrame(data)

    fig = px.line(
        df,
        x="week",
        y=["total_capacity", "total_planned"],
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True)

# =====================================================
# WORKER COVERAGE
# =====================================================

elif page == "Worker Coverage":

    st.title("👷 Worker Coverage")

    query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)

    RETURN
        w.name AS worker,
        collect(s.station_name) AS stations
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(record) for record in result]

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

# =====================================================
# SELF TEST
# =====================================================

elif page == "Self-Test":

    st.title("✅ Self-Test")
    
    def run_self_test(driver):
        checks = []
        
        # Check 1: Connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except:
            checks.append(("Neo4j connected", False, 3))
            return checks  # Can't continue
        
        with driver.session() as s:
            # Check 2: Node count
            result = s.run("MATCH (n) RETURN count(n) AS c").single()
            count = result["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))
            
            # Check 3: Relationship count
            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))
            
            # Check 4: Node labels
            result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            count = result["c"]
            checks.append((f"{count} node labels (min: 6)", count >= 6, 3))
            
            # Check 5: Relationship types
            result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))
            
            # Check 6: Variance query
            result = s.run("""
                MATCH (p:Project)-[r]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                    r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
        
        return checks
    
    checks = run_self_test(driver)

    total_score = 0

    for check, passed, points in checks:

        if passed:

            st.success(f"{check} ✅ (+{points} pts)")

            total_score += points

        else:

            st.error(f"{check} ❌ (+0 pts)")

    st.header(f"🎯 Final Score: {total_score} / 20")

driver.close()