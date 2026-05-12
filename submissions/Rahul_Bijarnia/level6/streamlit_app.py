import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Neo4j connection details
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Neo4j Driver
driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# Load CSV files
workers_df = pd.read_csv("data/factory_workers (1).csv")

# Page title
st.title("Level 6 Neo4j Factory Dashboard")

st.header("Factory Analytics Dashboard")

# Metrics
col1, col2 = st.columns(2)

with col1:
    st.metric("Total Workers", len(workers_df))

with col2:
    st.metric(
        "Average Weekly Hours",
        round(workers_df["hours_per_week"].mean(), 2)
    )

# Workers Dataset
st.subheader("Workers Dataset")
st.dataframe(workers_df)

# Role Distribution
st.subheader("Role Distribution")

role_counts = workers_df["role"].value_counts()

st.bar_chart(role_counts)

# Workers Per Station
st.subheader("Workers Per Station")

station_counts = workers_df["primary_station"].value_counts()

st.bar_chart(station_counts)

# Neo4j Query Results
st.subheader("Neo4j Graph Data")

query = """
MATCH (w:Worker)-[:WORKS_AT]->(s:Station)
RETURN w.name AS Worker,
       s.station_id AS Station
LIMIT 20
"""

with driver.session() as session:
    result = session.run(query)

    records = []

    for record in result:
        records.append({
            "Worker": record["Worker"],
            "Station": record["Station"]
        })

graph_df = pd.DataFrame(records)

st.dataframe(graph_df)

st.success("Neo4j Dashboard Connected Successfully!")

driver.close()