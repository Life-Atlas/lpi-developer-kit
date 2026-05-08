import streamlit as st
import pandas as pd
import plotly.express as px
from neo4j import GraphDatabase

# Using your local Neo4j Desktop credentials
URI = st.secrets["NEO4J_URI"]
USERNAME = st.secrets["NEO4J_USERNAME"]
PASSWORD = st.secrets["NEO4J_PASSWORD"] # <--- PUT YOUR NEO4J DESKTOP PASSWORD HERE

# Connect to Neo4j
@st.cache_resource
def get_db_driver():
    return GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

driver = get_db_driver()

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        # Handle empty results gracefully
        if not result.peek():
            return pd.DataFrame()
        return pd.DataFrame([r.values() for r in result], columns=result.keys())

# --- Sidebar Navigation ---
st.sidebar.title("Factory Dashboard")
page = st.sidebar.radio("Go to", ["Project Overview", "Station Load", "Capacity Tracker", "Worker Coverage", "Self-Test"])

# --- Page 1: Project Overview ---
if page == "Project Overview":
    st.title("Project Overview")
    query = """
    MATCH (p:Project)-[sched:SCHEDULED_AT]->(s:Station)
    OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
    RETURN p.name AS Project, 
           sum(sched.planned_hours) AS Total_Planned, 
           sum(sched.actual_hours) AS Total_Actual,
           collect(DISTINCT prod.type) AS Products
    """
    df = run_query(query)
    if not df.empty:
        df['Variance %'] = ((df['Total_Actual'] - df['Total_Planned']) / df['Total_Planned'] * 100).round(2)
        st.dataframe(df)
    else:
        st.write("No data found.")

# --- Page 2: Station Load ---
elif page == "Station Load":
    st.title("Station Load")
    query = """
    MATCH (p:Project)-[sched:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS Station, sched.week AS Week, 
           sum(sched.planned_hours) AS Planned, 
           sum(sched.actual_hours) AS Actual
    """
    df = run_query(query)
    if not df.empty:
        # Highlight where actual > planned
        df['Overloaded'] = df['Actual'] > df['Planned']
        
        # Interactive Plotly Chart
        fig = px.bar(df, x="Station", y=["Planned", "Actual"], barmode="group", 
                     color="Overloaded", color_discrete_map={True: 'red', False: 'green'},
                     title="Planned vs Actual Hours per Station")
        st.plotly_chart(fig)

# --- Page 3: Capacity Tracker ---
elif page == "Capacity Tracker":
    st.title("Capacity Tracker")
    query = """
    MATCH (wk:Week)-[hc:HAS_CAPACITY]->(c:Capacity)
    RETURN wk.id AS Week, 
           (hc.own + hc.hired + hc.overtime) AS Total_Capacity, 
           hc.deficit AS Deficit
    ORDER BY Week
    """
    df = run_query(query)
    if not df.empty:
        # Display deficit weeks in red using Streamlit styling
        def color_deficit(val):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        st.dataframe(df.style.map(color_deficit, subset=['Deficit']))

# --- Page 4: Worker Coverage ---
elif page == "Worker Coverage":
    st.title("Worker Coverage")
    query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
    WITH s, count(w) as Worker_Count, collect(w.name) as Workers
    RETURN s.name AS Station, Worker_Count, Workers
    ORDER BY Worker_Count ASC
    """
    df = run_query(query)
    if not df.empty:
        # Highlight Single Point of Failure (Worker_Count == 1)
        def highlight_spof(val):
            color = 'red' if val == 1 else ''
            return f'background-color: {color}'
        st.markdown("**Stations in RED have only 1 certified worker (Single Point of Failure)!**")
        st.dataframe(df.style.map(highlight_spof, subset=['Worker_Count']))

# --- Page 5: Self-Test (Mandatory) ---
elif page == "Self-Test":
    st.title("Self-Test")
    st.markdown("Running automated checks...")
    
    # Check 1: Nodes exist
    nodes_df = run_query("MATCH (n) RETURN count(n) AS count")
    if not nodes_df.empty and nodes_df['count'].sum() > 0:
        st.success("✅ Graph is populated with nodes")
    else:
        st.error("❌ Graph is empty")
        
    # Check 2: Relationships exist
    rels_df = run_query("MATCH ()-[r]->() RETURN count(r) AS count")
    if not rels_df.empty and rels_df['count'].sum() > 100:
        st.success("✅ Graph has correct number of relationships")
    else:
        st.error("❌ Missing relationships")
        
    st.balloons()
