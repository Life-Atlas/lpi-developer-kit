import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.set_page_config(page_title="Factory Graph Dashboard", layout="wide")

st.title("Factory Production Knowledge Graph Dashboard")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Self-Test"
    ]
)


def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return pd.DataFrame([dict(record) for record in result])


if page == "Project Overview":

    st.header("Project Overview")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN p.name AS project,
           sum(r.planned_hours) AS planned,
           sum(r.actual_hours) AS actual,
           ((sum(r.actual_hours)-sum(r.planned_hours))/sum(r.planned_hours))*100 AS variance
    """

    df = run_query(query)

    st.dataframe(df)


elif page == "Station Load":

    st.header("Station Load")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS station,
           sum(r.actual_hours) AS hours
    """

    df = run_query(query)

    fig = px.bar(
        df,
        x="station",
        y="hours",
        title="Station Workload"
    )

    st.plotly_chart(fig, use_container_width=True)


elif page == "Capacity Tracker":

    st.header("Capacity Tracker")

    query = """
    MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
    RETURN w.name AS week,
           c.total_capacity AS capacity,
           c.total_planned AS planned,
           c.deficit AS deficit
    """

    df = run_query(query)

    st.dataframe(df)

    fig = px.line(
        df,
        x="week",
        y=["capacity", "planned"],
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)


elif page == "Worker Coverage":

    st.header("Worker Coverage")

    query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
    RETURN w.name AS worker,
           s.code AS station
    """

    df = run_query(query)

    st.dataframe(df)


elif page == "Self-Test":

    st.header("Self-Test")

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

            checks.append((f"{count} nodes (min:50)", count >= 50, 3))

            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()

            count = result["c"]

            checks.append((f"{count} relationships (min:100)", count >= 100, 3))

            result = s.run(
                "CALL db.labels() YIELD label RETURN count(label) AS c"
            ).single()

            count = result["c"]

            checks.append((f"{count} labels (min:6)", count >= 6, 3))

            result = s.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"
            ).single()

            count = result["c"]

            checks.append((f"{count} relationship types (min:8)", count >= 8, 3))

            result = s.run("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.name AS project
            LIMIT 10
            """)

            rows = [dict(r) for r in result]

            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))

        return checks


    checks = run_self_test(driver)

    total = 0

    for text, passed, score in checks:

        if passed:
            st.success(f"✅ {text}   {score}/{score}")
            total += score

        else:
            st.error(f"❌ {text}")

    st.markdown("---")

    st.subheader(f"SELF TEST SCORE: {total}/20")