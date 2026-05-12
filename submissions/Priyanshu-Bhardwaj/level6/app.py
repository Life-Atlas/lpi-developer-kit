import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

# Set page layout to wide
st.set_page_config(page_title="Factory Graph Dashboard", layout="wide")

# Connect to Neo4j 
@st.cache_resource
def get_driver():
    try:
        # Try Streamlit Secrets first (for when deployed to the cloud)
        uri = st.secrets["NEO4J_URI"]
        user = st.secrets["NEO4J_USERNAME"]
        pwd = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        # Fall back to local .env variables if no secrets.toml exists
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        pwd = os.getenv("NEO4J_PASSWORD")
        
    return GraphDatabase.driver(uri, auth=(user, pwd))

driver = get_driver()

def run_cypher(query, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return pd.DataFrame([dict(r) for r in result])

st.title("🏭 Factory Production Knowledge Graph")

# Navigation via Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Project Overview", 
    "⚙️ Station Load", 
    "📈 Capacity Tracker", 
    "👷 Worker Coverage", 
    "✅ Self-Test"
])

# --- PAGE 1: Project Overview ---
with tab1:
    st.header("Project Overview")
    query = """
    MATCH (p:Project)
    OPTIONAL MATCH (p)-[e:EXECUTED_AT]->()
    WITH p, sum(e.planned_hours) AS planned, sum(e.actual_hours) AS actual
    OPTIONAL MATCH (p)-[:INCLUDES]->(prod:Product)
    RETURN p.id AS Project_ID, p.name AS Name, 
           round(planned, 1) AS Planned_Hours, 
           round(actual, 1) AS Actual_Hours,
           CASE WHEN planned > 0 THEN round(((actual - planned) / planned) * 100, 1) ELSE 0 END AS Variance_Pct,
           collect(DISTINCT prod.type) AS Products
    ORDER BY Project_ID
    """
    df = run_cypher(query)
    
    # Stylize variance
    def style_variance(val):
        color = 'red' if val > 0 else 'green'
        return f'color: {color}'
    
    st.dataframe(df.style.map(style_variance, subset=['Variance_Pct']), use_container_width=True)

# --- PAGE 2: Station Load ---
with tab2:
    st.header("Station Load Across Weeks")
    query = """
    MATCH (p:Project)-[e:EXECUTED_AT]->(s:Station)
    RETURN s.name AS Station, e.week AS Week, 
           sum(e.planned_hours) AS Planned, sum(e.actual_hours) AS Actual
    ORDER BY Week, Station
    """
    df = run_cypher(query)
    if not df.empty:
        # Calculate overload boolean for highlighting
        df['Is Overloaded'] = df['Actual'] > df['Planned']
        
        fig = px.bar(df, x="Week", y=["Planned", "Actual"], barmode="group",
                     facet_col="Station", facet_col_wrap=3,
                     title="Planned vs Actual Hours per Station",
                     color_discrete_map={"Planned": "#1f77b4", "Actual": "#ff7f0e"})
        st.plotly_chart(fig, use_container_width=True)
        
        # Highlight overloaded stations explicitly
        st.subheader("⚠️ Overloaded Stations Warning")
        overloaded = df[df['Is Overloaded']][['Week', 'Station', 'Planned', 'Actual']]
        st.dataframe(overloaded, use_container_width=True)

# --- PAGE 3: Capacity Tracker ---
with tab3:
    st.header("Weekly Factory Capacity vs Demand")
    query = """
    MATCH (w:Week)-[c:HAS_CAPACITY]->(:Factory)
    RETURN w.id AS Week, c.total_capacity AS Capacity, 
           c.total_planned AS Planned_Demand, c.deficit AS Deficit
    ORDER BY Week
    """
    df = run_cypher(query)
    if not df.empty:
        fig = px.line(df, x="Week", y=["Capacity", "Planned_Demand"], markers=True,
                      title="Capacity vs Planned Demand Tracker")
        fig.add_bar(x=df["Week"], y=df["Deficit"], name="Deficit (Red if < 0)")
        
        st.plotly_chart(fig, use_container_width=True)
        
        def highlight_deficit(val):
            return 'background-color: #ffcccc' if val < 0 else ''
        st.dataframe(df.style.map(highlight_deficit, subset=['Deficit']), use_container_width=True)

# --- PAGE 4: Worker Coverage ---
with tab4:
    st.header("Worker Station Coverage Matrix")
    query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
    RETURN w.name AS Worker, s.name AS Station
    """
    df = run_cypher(query)
    if not df.empty:
        # Create a Pivot Table (Matrix)
        matrix = pd.crosstab(df['Worker'], df['Station']).replace({0: '-', 1: '✅'})
        st.dataframe(matrix, use_container_width=True)
        
        st.subheader("🚨 Single-Point-of-Failure Stations")
        spof_query = """
        MATCH (s:Station)<-[:CAN_COVER]-(w:Worker)
        WITH s, count(w) AS coverage_count
        WHERE coverage_count = 1
        RETURN s.name AS Station, coverage_count AS Workers_Certified
        """
        spof_df = run_cypher(spof_query)
        st.error("The following stations only have ONE certified worker who can cover them:")
        st.table(spof_df)

# --- PAGE 5: Self-Test ---
with tab5:
    st.header("Mission Validation: Self-Test")
    
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
            checks.append((f"{result['c']} nodes (min: 50)", result['c'] >= 50, 3))
            
            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            checks.append((f"{result['c']} relationships (min: 100)", result['c'] >= 100, 3))
            
            result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            checks.append((f"{result['c']} node labels (min: 6)", result['c'] >= 6, 3))
            
            result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
            checks.append((f"{result['c']} relationship types (min: 8)", result['c'] >= 8, 3))
            
            # Adjusted Variance Query based on our EXECUTED_AT schema mapping
            result = s.run("""
                MATCH (p:Project)-[r:EXECUTED_AT]->(s:Station)
                WHERE r.actual_hours > (r.planned_hours * 1.1)
                RETURN p.name AS project, s.name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
        
        return checks

    results = run_self_test(driver)
    
    total_score = 0
    for text, passed, pts in results:
        status = "✅" if passed else "❌"
        earned = pts if passed else 0
        total_score += earned
        st.markdown(f"**{status} {text}** — *{earned}/{pts} pts*")
    
    st.divider()
    st.subheader(f"SELF-TEST SCORE: {total_score}/20")
    if total_score == 20:
        st.success("All checks passed! You are ready to deploy.")
    else:
        st.error("Some checks failed. Review your graph schema or queries.")
