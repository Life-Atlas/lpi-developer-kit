import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Factory Intelligence Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
def get_neo4j_connection():
    return GraphDatabase.driver(
        st.secrets.get("neo4j_uri", "bolt://localhost:7687"),
        auth=(st.secrets.get("neo4j_user", "neo4j"), st.secrets.get("neo4j_password", "password"))
    )

# Load data
@st.cache_data
def load_data():
    projects = pd.read_csv('projects.csv')
    stations = pd.read_csv('stations.csv')
    workers = pd.read_csv('workers.csv')
    return projects, stations, workers

projects_df, stations_df, workers_df = load_data()

# Risk prediction model
def predict_risk(project_data, station_data, worker_data):
    """Rule-based risk prediction"""
    risk_score = 0
    
    # Station overload risk
    overloaded_stations = station_data[station_data['currentLoad'] > 85]
    risk_score += len(overloaded_stations) * 0.3
    
    # Worker availability risk
    unavailable_workers = worker_data[worker_data['availability'] == False]
    risk_score += len(unavailable_workers) * 0.2
    
    # Project complexity risk
    high_complexity = project_data[project_data['complexity'] >= 4]
    risk_score += len(high_complexity) * 0.2
    
    # Deadline risk
    upcoming_deadlines = project_data[project_data['daysToDeadline'] < 7]
    risk_score += len(upcoming_deadlines) * 0.3
    
    return min(risk_score, 1.0)

# Sidebar navigation
st.sidebar.title("🏭 Factory Intelligence")
page = st.sidebar.selectbox("Navigate", [
    "Project Overview", 
    "Station Load Analysis", 
    "Worker Coverage",
    "Capacity Planning",
    "Risk Prediction",
    "Self-Test"
])

# Project Overview Page
if page == "Project Overview":
    st.title("📊 Project Overview")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Projects", len(projects_df[projects_df['status'] == 'ACTIVE']))
    
    with col2:
        delayed = len(projects_df[projects_df['status'] == 'DELAYED'])
        st.metric("Delayed Projects", delayed, delta=f"{delayed} delayed")
    
    with col3:
        avg_progress = projects_df['progress'].mean()
        st.metric("Avg Progress", f"{avg_progress:.1f}%")
    
    with col4:
        high_priority = len(projects_df[projects_df['priority'] >= 4])
        st.metric("High Priority", high_priority)
    
    # Project status chart
    fig = px.pie(projects_df, names='status', title='Project Status Distribution')
    st.plotly_chart(fig, use_container_width=True)
    
    # Project timeline
    timeline_fig = px.timeline(
        projects_df, 
        x_start="startDate", 
        x_end="deadline", 
        y="name", 
        color="priority",
        title="Project Timeline"
    )
    st.plotly_chart(timeline_fig, use_container_width=True)

# Station Load Analysis Page
elif page == "Station Load Analysis":
    st.title("⚙️ Station Load Analysis")
    
    # Load heatmap
    load_fig = px.bar(
        stations_df, 
        x='name', 
        y='currentLoad',
        color='status',
        title='Station Current Load (%)'
    )
    load_fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Critical Load")
    st.plotly_chart(load_fig, use_container_width=True)
    
    # Station efficiency
    eff_fig = px.scatter(
        stations_df,
        x='currentLoad',
        y='efficiency',
        size='capacity',
        color='type',
        title='Station Load vs Efficiency'
    )
    st.plotly_chart(eff_fig, use_container_width=True)
    
    # Overloaded stations alert
    overloaded = stations_df[stations_df['currentLoad'] > 85]
    if not overloaded.empty:
        st.error(f"⚠️ {len(overloaded)} stations are overloaded!")
        st.dataframe(overloaded[['name', 'currentLoad', 'efficiency', 'type']])

# Worker Coverage Page
elif page == "Worker Coverage":
    st.title("👥 Worker Coverage Analysis")
    
    # Worker availability
    avail_fig = px.pie(workers_df, names='availability', title='Worker Availability')
    st.plotly_chart(avail_fig, use_container_width=True)
    
    # Skill distribution
    skill_fig = px.histogram(workers_df, x='skillLevel', color='specialization', title='Skill Level Distribution')
    st.plotly_chart(skill_fig, use_container_width=True)
    
    # Worker load analysis
    load_fig = px.bar(
        workers_df,
        x='name',
        y='currentLoad',
        color='skillLevel',
        title='Worker Current Load (%)'
    )
    st.plotly_chart(load_fig, use_container_width=True)
    
    # Overloaded workers
    overloaded_workers = workers_df[workers_df['currentLoad'] > 85]
    if not overloaded_workers.empty:
        st.warning(f"⚠️ {len(overloaded_workers)} workers are overloaded")
        st.dataframe(overloaded_workers[['name', 'currentLoad', 'skillLevel', 'specialization']])

# Capacity Planning Page
elif page == "Capacity Planning":
    st.title("📈 Capacity Planning")
    
    # Capacity utilization
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Station Capacity")
        station_capacity = stations_df.groupby('type')['capacity'].sum().reset_index()
        fig = px.bar(station_capacity, x='type', y='capacity', title='Capacity by Station Type')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Worker Skills Coverage")
        skill_coverage = workers_df.groupby('specialization')['skillLevel'].mean().reset_index()
        fig = px.bar(skill_coverage, x='specialization', y='skillLevel', title='Avg Skill Level by Specialization')
        st.plotly_chart(fig, use_container_width=True)
    
    # Optimization recommendations
    st.subheader("🎯 Optimization Recommendations")
    
    # Find bottlenecks
    bottlenecks = stations_df[stations_df['currentLoad'] > 85]
    if not bottlenecks.empty:
        st.write("**Bottleneck Stations:**")
        for _, station in bottlenecks.iterrows():
            st.write(f"- {station['name']}: {station['currentLoad']:.1f}% load")
    
    # Find available workers
    available_workers = workers_df[workers_df['availability'] == True]
    st.write(f"**Available Workers:** {len(available_workers)}")
    
    # Capacity gap analysis
    total_capacity = stations_df['capacity'].sum()
    current_load = (stations_df['currentLoad'] * stations_df['capacity'] / 100).sum()
    utilization = (current_load / total_capacity) * 100
    
    st.metric("Overall Utilization", f"{utilization:.1f}%")
    
    if utilization > 85:
        st.error("⚠️ High utilization - consider capacity expansion")
    elif utilization < 60:
        st.info("ℹ️ Low utilization - optimize resource allocation")

# Risk Prediction Page
elif page == "Risk Prediction":
    st.title("🔮 Risk Prediction")
    
    # Calculate risk scores
    risk_scores = []
    for _, project in projects_df.iterrows():
        risk = predict_risk(projects_df, stations_df, workers_df)
        risk_scores.append(risk)
    
    projects_df['riskScore'] = risk_scores
    
    # Risk distribution
    risk_fig = px.histogram(projects_df, x='riskScore', nbins=10, title='Risk Score Distribution')
    st.plotly_chart(risk_fig, use_container_width=True)
    
    # High risk projects
    high_risk = projects_df[projects_df['riskScore'] > 0.7]
    if not high_risk.empty:
        st.error(f"⚠️ {len(high_risk)} high-risk projects detected!")
        st.dataframe(high_risk[['name', 'riskScore', 'priority', 'status']])
    
    # Risk factors analysis
    st.subheader("📊 Risk Factors Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Station overload impact
        overloaded_count = len(stations_df[stations_df['currentLoad'] > 85])
        st.metric("Overloaded Stations", overloaded_count)
        
        # Worker availability impact
        unavailable_count = len(workers_df[workers_df['availability'] == False])
        st.metric("Unavailable Workers", unavailable_count)
    
    with col2:
        # Deadline pressure
        deadline_pressure = len(projects_df[projects_df['daysToDeadline'] < 7])
        st.metric("Projects Near Deadline", deadline_pressure)
        
        # Complexity impact
        complex_projects = len(projects_df[projects_df['complexity'] >= 4])
        st.metric("Complex Projects", complex_projects)
    
    # Risk mitigation suggestions
    st.subheader("💡 Risk Mitigation Suggestions")
    
    if overloaded_count > 0:
        st.write("- **Station Overload**: Reallocate tasks or add capacity")
    
    if unavailable_count > 0:
        st.write("- **Worker Shortage**: Cross-train workers or adjust schedules")
    
    if deadline_pressure > 0:
        st.write("- **Deadline Pressure**: Prioritize tasks and extend deadlines if possible")
    
    if complex_projects > 0:
        st.write("- **Complex Projects**: Assign experienced workers and monitor closely")

# Self-Test Page
elif page == "Self-Test":
    st.title("🧪 System Self-Test")
    
    st.subheader("Data Quality Tests")
    
    # Test data completeness
    col1, col2, col3 = st.columns(3)
    
    with col1:
        projects_complete = projects_df.notnull().all().all()
        st.metric("Projects Data", "✅ Complete" if projects_complete else "❌ Issues")
    
    with col2:
        stations_complete = stations_df.notnull().all().all()
        st.metric("Stations Data", "✅ Complete" if stations_complete else "❌ Issues")
    
    with col3:
        workers_complete = workers_df.notnull().all().all()
        st.metric("Workers Data", "✅ Complete" if workers_complete else "❌ Issues")
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Projects", len(projects_df))
        st.metric("Total Stations", len(stations_df))
        st.metric("Total Workers", len(workers_df))
    
    with col2:
        avg_station_load = stations_df['currentLoad'].mean()
        st.metric("Avg Station Load", f"{avg_station_load:.1f}%")
        
        avg_worker_load = workers_df['currentLoad'].mean()
        st.metric("Avg Worker Load", f"{avg_worker_load:.1f}%")
        
        active_projects = len(projects_df[projects_df['status'] == 'ACTIVE'])
        st.metric("Active Projects", active_projects)
    
    # System health check
    st.subheader("🏥 System Health")
    
    health_score = 100
    
    # Check for critical issues
    if len(stations_df[stations_df['currentLoad'] > 95]) > 0:
        health_score -= 20
        st.error("Critical station overload detected")
    
    if len(workers_df[workers_df['currentLoad'] > 95]) > 0:
        health_score -= 15
        st.error("Critical worker overload detected")
    
    if len(projects_df[projects_df['status'] == 'DELAYED']) > len(projects_df) * 0.2:
        health_score -= 10
        st.warning("High project delay rate")
    
    # Display health score
    if health_score >= 80:
        st.success(f"System Health: {health_score}% - Optimal")
    elif health_score >= 60:
        st.warning(f"System Health: {health_score}% - Needs Attention")
    else:
        st.error(f"System Health: {health_score}% - Critical Issues")
    
    # Test results summary
    st.subheader("📋 Test Summary")
    
    test_results = {
        "Data Quality": "PASS" if projects_complete and stations_complete and workers_complete else "FAIL",
        "Performance": "PASS" if avg_station_load < 90 and avg_worker_load < 90 else "WARN",
        "Risk Level": "LOW" if len(projects_df[projects_df['riskScore'] > 0.7]) == 0 else "HIGH"
    }
    
    for test, result in test_results.items():
        status = "✅" if result == "PASS" else "⚠️" if result == "WARN" else "❌"
        st.write(f"{status} {test}: {result}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏭 Factory Intelligence Dashboard v1.0")
st.sidebar.markdown("Built with Streamlit + Neo4j")
