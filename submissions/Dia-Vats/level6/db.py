"""db.py — shared Neo4j driver for the Streamlit dashboard."""
import os
import streamlit as st
from neo4j import GraphDatabase

@st.cache_resource(show_spinner=False)
def get_driver():
    try:
        uri  = st.secrets["NEO4J_URI"]
        user = st.secrets["NEO4J_USER"]
        pw   = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        uri  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER",     "neo4j")
        pw   = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, pw))


def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    driver = get_driver()
    with driver.session() as s:
        result = s.run(cypher, params or {})
        return [dict(r) for r in result]
