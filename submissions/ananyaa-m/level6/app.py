import streamlit as st
import pandas as pd
import plotly.express as px
from neo4j import GraphDatabase
import os
import numpy as np
from dotenv import load_dotenv

st.set_page_config(page_title="Factory Flow Graph", layout="wide")

load_dotenv()

try:
    URI = st.secrets["NEO4J_URI"]
    USER = st.secrets["NEO4J_USER"]
    PWD = st.secrets["NEO4J_PASSWORD"]
except Exception:
    URI = os.getenv("NEO4J_URI")
    USER = os.getenv("NEO4J_USER")
    PWD = os.getenv("NEO4J_PASSWORD")

# Caching the connection so Streamlit doesn't reconnect on every click
@st.cache_resource
def get_driver():
    return GraphDatabase.driver(URI, auth=(USER, PWD))

driver = get_driver()

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [dict(record) for record in result]

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    label="Navigation",
    options=["Project Overview", "Station Load", "Capacity Tracker", "Worker Coverage", "Week 9 Forecast", "Self-Test"],
    index=0,
    label_visibility="collapsed" # This hides the second "Navigation" text
)

# --- PAGE 1: Project Overview ---
if page == "Project Overview":
    st.title("Project Overview")
    st.markdown("Overview of all current projects, their total hours, and overall variance.")
    
    query = """
    MATCH (p:Project)-[r:PROCESSED_AT]->()
    MATCH (p)-[:USES_PRODUCT]->(pr:Product)
    RETURN p.name AS Project, 
           collect(DISTINCT pr.type) AS Products,
           sum(r.planned_hours) AS PlannedHours, 
           sum(r.actual_hours) AS ActualHours
    ORDER BY ActualHours DESC
    """
    data = run_query(query)
    df = pd.DataFrame(data)
    
    if not df.empty:
        df['Variance %'] = ((df['ActualHours'] - df['PlannedHours']) / df['PlannedHours'] * 100).round(2)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found. Did you run seed_graph.py?")

# --- PAGE 2: Station Load ---
elif page == "Station Load":
    st.title("Station Load & Bottlenecks")
    
    query = """
    MATCH (s:Station)<-[r:PROCESSED_AT]-()
    RETURN s.name AS Station, 
           sum(r.planned_hours) AS Planned, 
           sum(r.actual_hours) AS Actual
    """
    data = run_query(query)
    df = pd.DataFrame(data)
    
    if not df.empty:
        # Melt dataframe for grouped bar chart
        df_melt = df.melt(id_vars='Station', value_vars=['Planned', 'Actual'], 
                          var_name='Hours Type', value_name='Hours')
        
        fig = px.bar(df_melt, x="Station", y="Hours", color="Hours Type", barmode="group",
                     title="Planned vs Actual Hours per Station",
                     color_discrete_map={"Planned": "#38BDF8", "Actual": "#EF4444"})
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE 3: Capacity Tracker ---
elif page == "Capacity Tracker":
    st.title("Weekly Capacity Tracker")
    
    query = """
    MATCH (wk:Week)
    RETURN wk.id AS Week, 
           wk.total_capacity AS Capacity, 
           wk.total_planned AS Demand, 
           wk.deficit AS Deficit
    ORDER BY Week
    """
    data = run_query(query)
    df = pd.DataFrame(data)
    
    if not df.empty:
        # Create a combined chart
        fig = px.bar(df, x="Week", y=["Capacity", "Demand"], barmode="group",
                     title="Factory Capacity vs Demand per Week")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Deficit Alert Weeks")
        def highlights(val):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        st.dataframe(df.style.map(highlights, subset=['Deficit']), use_container_width=True)

# --- PAGE 4: Worker Coverage ---
elif page == "Worker Coverage":
    st.title("Worker Coverage & Risk Matrix")
    
    # UPDATED QUERY: Looks for BOTH Primary and Backup relationships
    query = """
    MATCH (s:Station)
    OPTIONAL MATCH (w:Worker)-[:CAN_COVER|PRIMARY_STATION]->(s)
    RETURN s.code AS StationCode,
           s.name AS StationName, 
           count(DISTINCT w) AS AvailableWorkers, 
           collect(DISTINCT w.name) AS WorkerNames
    ORDER BY AvailableWorkers ASC
    """
    data = run_query(query)
    df = pd.DataFrame(data)
    
    if not df.empty:
        st.markdown("**Stations with 0 or 1 available worker are Single Points of Failure (Red).**")
        df['WorkerNames'] = df['WorkerNames'].apply(lambda x: ", ".join(x) if x else "No Workers Assigned")
        
        def highlight_risk(row):
            if row['AvailableWorkers'] <= 1:
                return ['background-color: #ffcccc; color: #000000'] * len(row)
            return [''] * len(row)
            
        st.dataframe(df.style.apply(highlight_risk, axis=1), use_container_width=True)

# --- PAGE 5: Week 9 Forecast (Bonus C) ---
elif page == "Week 9 Forecast":
    st.title("Week 9 Risk Forecast (Bonus C)")
    st.markdown("Predicting station workload for Week 9 based on linear trends from previous weeks.")

    # Query historical load per station per week
    query = """
    MATCH (s:Station)-[r:UTILIZED_IN_WEEK]->(w:Week)
    RETURN s.code AS Station, w.id AS Week, r.actual_hours AS Hours
    """
    data = run_query(query)
    df = pd.DataFrame(data)

    if not df.empty:
        # Fix SyntaxWarning with raw string r'(\d+)'
        df['WeekNum'] = df['Week'].str.extract(r'(\d+)').astype(int)
        df = df.sort_values(['Station', 'WeekNum'])
        
        stations = df['Station'].unique()
        forecast_results = []

        for station in stations:
            s_data = df[df['Station'] == station]
            # Need at least 2 points to draw a trend line
            if len(s_data) >= 2: 
                x = s_data['WeekNum'].values
                y = s_data['Hours'].values
                
                # Perform Linear Regression (y = mx + c)
                m, c = np.polyfit(x, y, 1)
                week9_pred = (m * 9) + c
                
                # Calculate confidence (Standard Deviation of residuals)
                std_dev = np.std(y - (m * x + c)) if len(y) > 1 else 0
                
                forecast_results.append({
                    "Station": station,
                    "History": f"{len(s_data)} weeks",
                    "Week 9 Forecast": round(max(0, week9_pred), 1), # Prevent negative hours
                    "Trend": "Increasing 📈" if m > 0 else "Decreasing 📉",
                    "m": m, "c": c, "std": std_dev
                })

        if forecast_results:
            forecast_df = pd.DataFrame(forecast_results)
            
            # Identify the biggest risk
            top_risk = forecast_df.sort_values(by="Week 9 Forecast", ascending=False).iloc[0]
            st.error(f"⚠️ **Risk Alert:** Station **{top_risk['Station']}** is projected to have the highest load in Week 9.")

            # Summary Table
            st.subheader("Predictive Analysis Table")
            st.dataframe(forecast_df[['Station', 'History', 'Week 9 Forecast', 'Trend']], use_container_width=True)

            # Chart Selection
            selected_s = st.selectbox("Select Station to View Trajectory", forecast_df['Station'].unique())
            
            # Fix IndexError: Check if selection exists in results
            s_matches = forecast_df[forecast_df['Station'] == selected_s]
            if not s_matches.empty:
                s_info = s_matches.iloc[0]
                s_plot_data = df[df['Station'] == selected_s]
                
                # Generate trend line for Weeks 1 through 9
                x_range = np.array(range(1, 10))
                y_trend = (s_info['m'] * x_range) + s_info['c']
                
                fig = px.scatter(s_plot_data, x='WeekNum', y='Hours', 
                                 title=f"Load Trajectory for Station {selected_s}",
                                 labels={'WeekNum': 'Week', 'Hours': 'Actual Hours'},
                                 range_x=[0.5, 9.5])
                
                # Add the Red Trend Line
                fig.add_scatter(x=x_range, y=y_trend, mode='lines', name='Forecast Trend', 
                                line=dict(color='red', dash='dash'))
                
                # Add the Confidence Band (Shaded area)
                fig.add_scatter(x=x_range, y=y_trend + s_info['std'], mode='lines', line=dict(width=0), showlegend=False)
                fig.add_scatter(x=x_range, y=y_trend - s_info['std'], mode='lines', line=dict(width=0), 
                                fill='tonexty', fillcolor='rgba(255, 0, 0, 0.4)', name='Confidence Interval')
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient historical data to generate forecasts.")

# --- PAGE 6: Self-Test (Grader Page) ---
elif page == "Self-Test":
    st.title("Auto-Grader Self-Test")
    
    def run_self_test(driver_instance):
        checks = []
        try:
            with driver_instance.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except:
            checks.append(("Neo4j connected", False, 3))
            return checks
        
        with driver_instance.session() as s:
            count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))
            
            count = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))
            
            count = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
            checks.append((f"{count} node labels (min: 6)", count >= 6, 3))
            
            count = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))
            
            # Exact variance query using our schema's relationships
            result = s.run("""
                MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station, r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
        
        return checks

    results = run_self_test(driver)
    total_score = 0
    
    for text, passed, points in results:
        icon = "✅" if passed else "❌"
        earned = points if passed else 0
        total_score += earned
        st.markdown(f"**{icon} {text}** — *{earned}/{points} pts*")
        
    st.divider()
    st.subheader(f"SELF-TEST SCORE: {total_score}/20")