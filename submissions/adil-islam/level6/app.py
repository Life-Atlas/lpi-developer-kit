import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import plotly.express as px
import os

URI = st.secrets["NEO4J_URI"]
USER = st.secrets["NEO4J_USER"]
PASSWORD = st.secrets["NEO4J_PASSWORD"]


driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.set_page_config(page_title="Factory Dashboard", layout="wide")

st.title("Factory Knowledge Graph Dashboard")

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

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return pd.DataFrame([dict(r) for r in result])

# PAGE 1
if page == "Project Overview":

    st.header("Project Overview")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->()
    RETURN p.name AS project,
           sum(r.planned_hours) AS planned,
           sum(r.actual_hours) AS actual
    """

    df = run_query(query)

    df["variance"] = (
        (df["actual"] - df["planned"])
        / df["planned"]
    ) * 100

    st.dataframe(df)

    fig = px.bar(
        df,
        x="project",
        y=["planned", "actual"],
        barmode="group"
    )

    st.plotly_chart(fig, use_container_width=True)

# PAGE 2
elif page == "Station Load":

    st.header("Station Load")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS station,
           sum(r.planned_hours) AS planned,
           sum(r.actual_hours) AS actual
    """

    df = run_query(query)

    fig = px.bar(
        df,
        x="station",
        y=["planned", "actual"],
        barmode="group"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df)

# PAGE 3
elif page == "Capacity Tracker":

    st.header("Capacity Tracker")

    query = """
    MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
    RETURN w.name AS week,
           c.own AS own,
           c.hired AS hired,
           c.overtime AS overtime,
           c.demand AS demand,
           c.deficit AS deficit
    ORDER BY week
    """

    df = run_query(query)

    st.dataframe(df)

    fig = px.bar(
        df,
        x="week",
        y=["own", "hired", "overtime"]
    )

    st.plotly_chart(fig, use_container_width=True)

# PAGE 4
elif page == "Worker Coverage":

    st.header("Worker Coverage")

    query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
    RETURN s.code AS station,
           collect(w.name) AS workers,
           count(w) AS worker_count
    """

    df = run_query(query)

    st.dataframe(df)

    st.subheader("Single Point of Failure Stations")

    spof = df[df["worker_count"] == 1]

    st.dataframe(spof)

# PAGE 5
elif page == "Self-Test":

    st.header("Self-Test")

    checks = []

    try:
        with driver.session() as s:
            s.run("RETURN 1")

        checks.append(("Neo4j connected", True, 3))

    except:
        checks.append(("Neo4j connected", False, 3))

    with driver.session() as s:

        result = s.run(
            "MATCH (n) RETURN count(n) AS c"
        ).single()

        node_count = result["c"]

        checks.append(
            (
                f"{node_count} nodes (min: 50)",
                node_count >= 50,
                3
            )
        )

        result = s.run(
            "MATCH ()-[r]->() RETURN count(r) AS c"
        ).single()

        rel_count = result["c"]

        checks.append(
            (
                f"{rel_count} relationships (min: 100)",
                rel_count >= 100,
                3
            )
        )

        result = s.run(
            "CALL db.labels() YIELD label RETURN count(label) AS c"
        ).single()

        label_count = result["c"]

        checks.append(
            (
                f"{label_count} labels (min: 6)",
                label_count >= 6,
                3
            )
        )

        result = s.run(
            """
            CALL db.relationshipTypes()
            YIELD relationshipType
            RETURN count(relationshipType) AS c
            """
        ).single()

        rel_types = result["c"]

        checks.append(
            (
                f"{rel_types} relationship types (min: 8)",
                rel_types >= 8,
                3
            )
        )

        result = s.run("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WHERE r.actual_hours > r.planned_hours * 1.1
        RETURN p.name, s.name
        LIMIT 10
        """)

        rows = [dict(r) for r in result]

        checks.append(
            (
                f"Variance query: {len(rows)} results",
                len(rows) > 0,
                5
            )
        )

    total = 0

    for text, passed, points in checks:

        if passed:
            st.success(f"✅ {text} ({points}/{points})")
            total += points
        else:
            st.error(f"❌ {text} (0/{points})")

    st.subheader(f"SELF-TEST SCORE: {total}/20")