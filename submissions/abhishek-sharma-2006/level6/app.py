import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.title("Factory Graph Dashboard")

page = st.sidebar.selectbox(
    "Choose Page",
    ["Project Overview", "Station Load", "Worker Coverage", "Self-Test"]
)

# PROJECT PAGE
if page == "Project Overview":

    st.header("Project Overview")

    query = """
    MATCH (p:Project)
    RETURN p.id AS id, p.name AS name
    """

    with driver.session() as session:
        result = session.run(query)

        data = []
        for r in result:
            data.append(dict(r))

        df = pd.DataFrame(data)

    st.dataframe(df)

# STATION PAGE
elif page == "Station Load":

    st.header("Station Load")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS station,
           r.planned_hours AS planned,
           r.actual_hours AS actual
    """

    with driver.session() as session:
        result = session.run(query)

        data = []
        for r in result:
            data.append(dict(r))

        df = pd.DataFrame(data)

    st.dataframe(df)

# WORKER PAGE
elif page == "Worker Coverage":

    st.header("Worker Coverage")

    query = """
    MATCH (w:Worker)
    RETURN w.name AS worker
    """

    with driver.session() as session:
        result = session.run(query)

        data = []
        for r in result:
            data.append(dict(r))

        df = pd.DataFrame(data)

    st.dataframe(df)

# SELF TEST
elif page == "Self-Test":

    st.header("Self-Test")

    checks = []

    try:
        with driver.session() as s:
            s.run("RETURN 1")

        checks.append(("Neo4j Connected", True))

    except:
        checks.append(("Neo4j Connected", False))

    with driver.session() as s:

        result = s.run("MATCH (n) RETURN count(n) AS c").single()
        node_count = result["c"]

        result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
        rel_count = result["c"]

    st.write(f"Nodes: {node_count}")
    st.write(f"Relationships: {rel_count}")

    for c in checks:
        if c[1]:
            st.success(c[0])
        else:
            st.error(c[0])

driver.close()