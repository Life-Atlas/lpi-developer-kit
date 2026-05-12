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

### --- Page 5: Self-Test (Mandatory) ---
elif page == "Self-Test": 
    st.title("Self-Test") 
    st.markdown("Running automated checks...")

    # 1. Check Projects (Min 8)
    df_proj = run_query("MATCH (n:Project) RETURN count(n) as count")
    proj_count = df_proj['count'].iloc if not df_proj.empty else 0
    if proj_count >= 8:
        st.success(f"✅ Projects: {proj_count} (Min 8)")
    else:
        st.error(f"❌ Projects: {proj_count} (Min 8)")

    # 2. Check Products (Min 7)
    df_prod = run_query("MATCH (n:Product) RETURN count(n) as count")
    prod_count = df_prod['count'].iloc if not df_prod.empty else 0
    if prod_count >= 7:
        st.success(f"✅ Products: {prod_count} (Min 7)")
    else:
        st.error(f"❌ Products: {prod_count} (Min 7)")

    # 3. Check Stations (Min 9)
    df_stat = run_query("MATCH (n:Station) RETURN count(n) as count")
    stat_count = df_stat['count'].iloc if not df_stat.empty else 0
    if stat_count >= 9:
        st.success(f"✅ Stations: {stat_count} (Min 9)")
    else:
        st.error(f"❌ Stations: {stat_count} (Min 9)")

    # 4. Check Workers (Min 13)
    df_work = run_query("MATCH (n:Worker) RETURN count(n) as count")
    work_count = df_work['count'].iloc if not df_work.empty else 0
    if work_count >= 13:
        st.success(f"✅ Workers: {work_count} (Min 13)")
    else:
        st.error(f"❌ Workers: {work_count} (Min 13)")

    # 5. Check Weeks (Min 8)
    df_week = run_query("MATCH (n:Week) RETURN count(n) as count")
    week_count = df_week['count'].iloc if not df_week.empty else 0
    if week_count >= 8:
        st.success(f"✅ Weeks: {week_count} (Min 8)")
    else:
        st.error(f"❌ Weeks: {week_count} (Min 8)")

    # 6. Check Etapps (Min 2)
    df_etapp = run_query("MATCH (n:Etapp) RETURN count(n) as count")
    etapp_count = df_etapp['count'].iloc if not df_etapp.empty else 0
    if etapp_count >= 2:
        st.success(f"✅ Etapps: {etapp_count} (Min 2)")
    else:
        st.error(f"❌ Etapps: {etapp_count} (Min 2)")