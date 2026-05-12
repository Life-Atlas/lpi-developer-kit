import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy import stats
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Factory Intelligence Dashboard", layout="wide")


st.markdown("""
    <style>
    /* Metric Card Styling */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        color: #58A6FF !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Table & Dataframe Styling */
    .stDataFrame, .stTable {
        border-radius: 4px;
    }

    /* Info/Warning Box Styling */
    .stAlert {
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Database Connection Logic
load_dotenv(override=True)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI:
    try:
        NEO4J_URI = st.secrets["NEO4J_URI"]
        NEO4J_USER = st.secrets["NEO4J_USER"]
        NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]
    except:
        pass

if not NEO4J_PASSWORD or not NEO4J_URI:
    st.error("CRITICAL ERROR: Could not read credentials. Check your .env file or Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

driver = get_driver()

def run_query(query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return pd.DataFrame([r.data() for r in result])

# ---------------------------------------------------------
# NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Self-Test", 
    "1. Project Overview", 
    "2. Station Load", 
    "3. Capacity Tracker", 
    "4. Worker Coverage",
    "5. Predictive Forecast"
])


def apply_chart_theme(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        colorway=["#58A6FF", "#3FB950", "#D29922", "#F85149", "#BC8CFF"],
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig

# ---------------------------------------------------------
# PAGE LOGIC
# ---------------------------------------------------------

if page == "Self-Test":
    st.title("Level 6 Self-Test")
    st.markdown("Automated grading checks to verify Graph architecture.")
    
    def run_self_test_internal(driver):
        checks = []
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except:
            checks.append(("Neo4j connection failed", False, 3))
            return checks
        with driver.session() as s:
            res = s.run("MATCH (n) RETURN count(n) AS c").single()
            checks.append((f"{res['c']} nodes (min: 50)", res['c'] >= 50, 3))
            res = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            checks.append((f"{res['c']} relationships (min: 100)", res['c'] >= 100, 3))
            res = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            checks.append((f"{res['c']} node labels (min: 6)", res['c'] >= 6, 3))
            res = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
            checks.append((f"{res['c']} relationship types (min: 8)", res['c'] >= 8, 3))
            res = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in res]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
        return checks

    with st.spinner("Running tests..."):
        results = run_self_test_internal(driver)
    
    total_score = sum([score for _, passed, score in results if passed])
    max_score = sum([score for _, _, score in results])
    
    for text, passed, score in results:
        if passed:
            st.success(f"PASSED: {text} ({score}/{score})")
        else:
            st.error(f"FAILED: {text} (0/{score})")
            
    st.markdown("---")
    st.subheader(f"SELF-TEST SCORE: {total_score}/{max_score}")

elif page == "1. Project Overview":
    st.title("Project Overview")
    st.info("""
    Manager's Guide: This page tracks the overall health of your active projects. Pay close attention to Variance %. 
    * Positive Variance (e.g., +15%): The project took longer than estimated, costing the company extra money. 
    * Zero or Negative Variance: The project is on-time or finishing faster than budgeted.
    """)
    query = """
    MATCH (p:Project)
    OPTIONAL MATCH (p)-[r:SCHEDULED_AT]->(:Station)
    OPTIONAL MATCH (p)-[:PRODUCES]->(pr:Product)
    RETURN p.name AS Project, 
           sum(r.planned_hours) AS Planned_Hours, 
           sum(r.actual_hours) AS Actual_Hours,
           collect(DISTINCT pr.type) AS Products
    """
    df = run_query(query)
    
    if not df.empty:
        df['Variance %'] = ((df['Actual_Hours'] - df['Planned_Hours']) / df['Planned_Hours'] * 100).round(2)
        df['Products'] = df['Products'].apply(lambda x: ", ".join(x))
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Active Projects", len(df))
        col2.metric("Total Planned Hours", f"{df['Planned_Hours'].sum():,.0f}h")
        col3.metric("Average Variance", f"{df['Variance %'].mean():.1f}%")
        st.markdown("---")
        st.dataframe(df, use_container_width=True)

elif page == "2. Station Load":
    st.title("Station Load (Weekly Timeline)")
    st.info("""
    Manager's Guide: This timeline helps spot physical bottlenecks on the factory floor. Compare the Planned (estimated) vs Actual (realized) hours. If a station consistently logs higher actual hours, it indicates machine wear, underestimation by the planning team, or a need for operator training.
    """)
    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS Station, r.week AS Week, 
           sum(r.planned_hours) AS Planned, sum(r.actual_hours) AS Actual
    ORDER BY Week
    """
    df = run_query(query)
    
    if not df.empty:
        station_list = df['Station'].unique().tolist()
        selected_station = st.selectbox("Filter by Station:", ["All Stations"] + station_list)
        plot_df = df if selected_station == "All Stations" else df[df['Station'] == selected_station]
        df_melt = plot_df.melt(id_vars=["Station", "Week"], value_vars=["Planned", "Actual"], 
                          var_name="Type", value_name="Hours")
        
        fig = px.bar(df_melt, x="Week", y="Hours", color="Type", barmode="group",
                     title=f"Planned vs Actual Hours: {selected_station}")
        st.plotly_chart(apply_chart_theme(fig), use_container_width=True)
        
        over_budget = df[df['Actual'] > df['Planned']]
        if not over_budget.empty:
            st.warning("Alert: Stations exceeding planned hours (Actual > Planned):")
            st.dataframe(over_budget, use_container_width=True)

elif page == "3. Capacity Tracker":
    st.title("Factory Capacity vs Demand")
    st.info("""
    Manager's Guide: This is your workforce scheduling tool. It calculates if you have enough human-hours to complete the planned work. 
    Watch the Deficit column: Any number highlighted in Red means the factory is understaffed for that week. You must authorize overtime or hire contractors to prevent project delays.
    """)
    query = """
    MATCH (wk:Week)-[c:HAS_CAPACITY]->()
    RETURN wk.name AS Week, 
           c.own AS Own_Hours, c.hired AS Hired, 
           c.overtime AS Overtime, c.deficit AS Deficit
    ORDER BY Week
    """
    df = run_query(query)
    if not df.empty:
        df['Total_Capacity'] = df['Own_Hours'] + df['Hired'] + df['Overtime']
        df['Total_Demand'] = df['Total_Capacity'] - df['Deficit']
        cols = ['Week', 'Own_Hours', 'Hired', 'Overtime', 'Total_Capacity', 'Total_Demand', 'Deficit']
        df = df[cols]
        def highlight_deficit(val):
            return 'background-color: #4a1515; color: #ff6b6b; font-weight: bold;' if val < 0 else ''
        st.dataframe(df.style.map(highlight_deficit, subset=['Deficit']), use_container_width=True)

elif page == "4. Worker Coverage":
    st.title("Worker Coverage Matrix")
    query = """
    MATCH (w:Worker), (s:Station)
    WHERE s.name IS NOT NULL
    OPTIONAL MATCH (w)-[r:CAN_COVER|WORKS_AT]->(s)
    RETURN w.name AS Worker, s.name AS Station, count(r) > 0 AS Can_Cover
    """
    df = run_query(query)
    if not df.empty:
        covered_df = df[df['Can_Cover'] == True]
        station_counts = covered_df['Station'].value_counts()
        spof_stations = station_counts[station_counts == 1].index.tolist()
        if spof_stations:
            st.error(f"SINGLE POINT OF FAILURE DETECTED: Only 1 worker is available to cover: {', '.join(spof_stations)}")
            for station in spof_stations:
                spof_worker = covered_df[covered_df['Station'] == station]['Worker'].values[0]
                st.warning(f"Business Impact Risk: {spof_worker} is the only person certified to operate the {station}. If worker is unavailable, this machine shuts down and halts production. Immediate cross-training is required.")
        else:
            st.success("Factory is secure. No single points of failure detected.")
        st.markdown("### Cross-Training Matrix")
        # 1. Create the matrix
        matrix = pd.crosstab(index=df['Worker'], columns=df['Station'], values=df['Can_Cover'], aggfunc='max').fillna(False)
        visual_matrix = matrix.replace({True: "OK", False: "--"})

        # 2. Define the highlighting function
        def highlight_spof_cols(col):
            # Check if this station name is in your list of SPOF stations
            if col.name in spof_stations:
                return ['background-color: rgba(255, 75, 75, 0.2); border: 1px solid #ff4b4b;'] * len(col)
            return [''] * len(col)

        # 3. Display the styled matrix
        st.dataframe(visual_matrix.style.apply(highlight_spof_cols), use_container_width=True)

elif page == "5. Predictive Forecast":
    st.title("Week 9 Manufacturing Risk Forecast")
    st.markdown("Analysis of production trends utilizing linear regression to identify upcoming bottlenecks.")
    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS Station, r.week AS Week, 
           r.planned_hours AS Planned, r.actual_hours AS Actual
    ORDER BY Station, Week
    """
    df = run_query(query)
    if not df.empty:
        df['Week_Num'] = df['Week'].str.extract('(\d+)').astype(int)
        stations = sorted(df['Station'].unique())
        sel_station = st.selectbox("Select station for analysis:", stations)
        s_df = df[df['Station'] == sel_station].groupby('Week_Num').agg({'Actual': 'sum', 'Planned': 'mean'}).reset_index()
        x, y = s_df['Week_Num'].values, s_df['Actual'].values
        slope, intercept, r, p, std_err = stats.linregress(x, y)
        weeks_ext = np.array(range(1, 10))
        y_pred = slope * weeks_ext + intercept
        w9_forecast = y_pred[-1]
        ci = (1.96 * std_err) if std_err > 10.0 else 25.0
        upper_bound = y_pred + ci
        lower_bound = y_pred - ci
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.concatenate([weeks_ext, weeks_ext[::-1]]), y=np.concatenate([upper_bound, lower_bound[::-1]]), fill='toself', fillcolor='rgba(88, 166, 255, 0.1)', line=dict(color='rgba(255,255,255,0)'), hoverinfo="skip", name='95% Confidence Interval'))
        fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines', name='Historical Actual', marker=dict(color='#3FB950', size=8)))
        fig.add_trace(go.Scatter(x=weeks_ext, y=y_pred, mode='lines', name='Trajectory', line=dict(dash='dash', color='#58A6FF', width=2)))
        st.plotly_chart(apply_chart_theme(fig), use_container_width=True)
        avg_planned = s_df['Planned'].mean()
        st.info(f"Executive Summary for {sel_station}: Workload is {'increasing' if slope > 0 else 'decreasing'} at {abs(slope):.1f} hours/week. Week 9 prediction: {w9_forecast:.1f} hours.")
        st.markdown("---")
        st.subheader("Week 9 Executive Risk Report")
        st.write("Summary of all stations projected for Week 9 based on growth trends:")
        risk_data = []
        for s in stations:
            temp_df = df[df['Station'] == s].groupby('Week_Num')['Actual'].sum().reset_index()
            tx, ty = temp_df['Week_Num'].values, temp_df['Actual'].values
            m, b, _, _, _ = stats.linregress(tx, ty)
            w9 = m * 9 + b
            avg_hist = ty.mean()
            status = "HIGH RISK" if m > 0 and w9 > (avg_hist * 1.15) else "MONITOR" if m > 0 else "STABLE"
            risk_data.append({"Station": s, "W9 Forecast": f"{w9:.1f}h", "Trend": "Rising" if m > 0 else "Falling", "Status": status})
        risk_df = pd.DataFrame(risk_data)
        def color_risk_internal(val):
            if "HIGH" in val: return 'color: #ff6b6b; font-weight: bold'
            if "STABLE" in val: return 'color: #3FB950;'
            return 'color: #D29922;'
        st.table(risk_df.style.map(color_risk_internal, subset=['Status']))