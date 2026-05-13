import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Factory Production Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
def get_neo4j_connection():
    """Get Neo4j database connection"""
    try:
        return GraphDatabase.driver(
            st.secrets.get("neo4j_uri", "bolt://localhost:7687"),
            auth=(st.secrets.get("neo4j_user", "neo4j"), 
                  st.secrets.get("neo4j_password", "password"))
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Execute Neo4j query safely
def execute_query(query, params=None):
    """Execute Neo4j query with error handling"""
    driver = get_neo4j_connection()
    if not driver:
        return None
    
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        return None
    finally:
        driver.close()

# Sidebar navigation
st.sidebar.title("🏭 Factory Production")
page = st.sidebar.selectbox("Navigate", [
    "Project Overview", 
    "Station Load", 
    "Capacity Tracker",
    "Worker Coverage",
    "Forecast",
    "Self-Test"
])

# Project Overview Page
if page == "Project Overview":
    st.title("📊 Project Overview")
    
    # Get project data
    project_query = """
    MATCH (p:Project)
    RETURN p.project_id as project_id, p.project_name as project_name,
           p.product_type as product_type, p.quantity as quantity,
           p.planned_hours as planned_hours, p.actual_hours as actual_hours,
           p.completed_units as completed_units, p.variance_percent as variance_percent,
           p.week as week
    ORDER BY p.project_id, p.week
    """
    
    projects_data = execute_query(project_query)
    
    if projects_data:
        df = pd.DataFrame(projects_data)
        
        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_projects = df['project_id'].nunique()
            st.metric("Total Projects", total_projects)
        
        with col2:
            avg_variance = df['variance_percent'].mean()
            st.metric("Avg Variance", f"{avg_variance:.1f}%")
        
        with col3:
            total_hours = df['actual_hours'].sum()
            st.metric("Total Hours", f"{total_hours:.0f}")
        
        with col4:
            total_units = df['completed_units'].sum()
            st.metric("Total Units", total_units)
        
        # Project variance chart
        st.subheader("Project Performance Variance")
        fig = px.bar(
            df.groupby('project_id')['variance_percent'].mean().reset_index(),
            x='project_id', 
            y='variance_percent',
            title='Planned vs Actual Hours Variance (%)',
            color='variance_percent',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed project table
        st.subheader("Project Details")
        project_summary = df.groupby('project_id').agg({
            'project_name': 'first',
            'product_type': 'first',
            'quantity': 'first',
            'planned_hours': 'sum',
            'actual_hours': 'sum',
            'completed_units': 'sum',
            'variance_percent': 'mean'
        }).reset_index()
        
        st.dataframe(project_summary, use_container_width=True)
    else:
        st.error("No project data available")

# Station Load Page
elif page == "Station Load":
    st.title("⚙️ Station Load Analysis")
    
    # Get station performance data
    station_query = """
    MATCH (s:Station)<-[:AT_STATION]-(p:Project)
    RETURN s.station_code as station_code, s.station_name as station_name,
           SUM(p.planned_hours) as total_planned,
           SUM(p.actual_hours) as total_actual,
           COUNT(p) as project_count,
           AVG(p.variance_percent) as avg_variance
    ORDER BY station_code
    """
    
    station_data = execute_query(station_query)
    
    if station_data:
        df = pd.DataFrame(station_data)
        df['load_variance'] = ((df['total_actual'] - df['total_planned']) / df['total_planned']) * 100
        
        # Station load chart
        fig = px.bar(
            df, 
            x='station_code', 
            y=['total_planned', 'total_actual'],
            title='Station Planned vs Actual Hours',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Variance analysis
        st.subheader("Station Variance Analysis")
        fig2 = px.scatter(
            df,
            x='total_planned',
            y='load_variance',
            size='project_count',
            color='avg_variance',
            title='Station Load Variance',
            hover_data=['station_name']
        )
        fig2.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="10% variance threshold")
        st.plotly_chart(fig2, use_container_width=True)
        
        # Overloaded stations
        overloaded = df[df['load_variance'] > 10]
        if not overloaded.empty:
            st.warning(f"⚠️ {len(overloaded)} stations with >10% variance")
            st.dataframe(overloaded[['station_code', 'station_name', 'load_variance', 'project_count']])
    else:
        st.error("No station data available")

# Capacity Tracker Page
elif page == "Capacity Tracker":
    st.title("📈 Capacity Tracker")
    
    # Get capacity data
    capacity_query = """
    MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
    OPTIONAL MATCH (c)-[:HAS_BOTTLENECK]->(b:Bottleneck)
    RETURN w.week_id as week, c.total_capacity as capacity,
           c.total_planned as planned, c.deficit as deficit,
           c.utilization_percent as utilization,
           COUNT(b) as bottleneck_count
    ORDER BY w.week_id
    """
    
    capacity_data = execute_query(capacity_query)
    
    if capacity_data:
        df = pd.DataFrame(capacity_data)
        
        # Capacity utilization chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['week'],
            y=df['capacity'],
            name='Available Capacity',
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            x=df['week'],
            y=df['planned'],
            name='Planned Hours',
            marker_color='orange'
        ))
        fig.update_layout(
            title='Weekly Capacity vs Planned Hours',
            barmode='group',
            xaxis_title='Week',
            yaxis_title='Hours'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Deficit analysis
        st.subheader("Capacity Deficit Analysis")
        deficit_fig = px.bar(
            df,
            x='week',
            y='deficit',
            title='Weekly Capacity Deficit',
            color='deficit',
            color_continuous_scale=['green', 'yellow', 'red']
        )
        deficit_fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(deficit_fig, use_container_width=True)
        
        # Critical weeks
        critical_weeks = df[df['deficit'] < -50]
        if not critical_weeks.empty:
            st.error(f"⚠️ Critical capacity deficit in weeks: {', '.join(critical_weeks['week'])}")
            st.dataframe(critical_weeks[['week', 'deficit', 'utilization', 'bottleneck_count']])
    else:
        st.error("No capacity data available")

# Worker Coverage Page
elif page == "Worker Coverage":
    st.title("👥 Worker Coverage Analysis")
    
    # Get worker coverage data
    worker_query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
    OPTIONAL MATCH (w)-[:PRIMARY_STATION]->(ps:Station)
    RETURN w.worker_id as worker_id, w.name as name, w.role as role,
           w.primary_station as primary_station, ps.station_name as primary_station_name,
           w.can_cover_stations as can_cover,
           COUNT(s) as coverable_stations
    ORDER BY w.worker_id
    """
    
    worker_data = execute_query(worker_query)
    
    if worker_data:
        df = pd.DataFrame(worker_data)
        
        # Worker coverage chart
        fig = px.bar(
            df,
            x='worker_id',
            y='coverable_stations',
            color='role',
            title='Worker Station Coverage',
            hover_data=['name', 'primary_station']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Single point of failure analysis
        st.subheader("Single Point of Failure Analysis")
        
        # Find stations with minimal coverage
        spof_query = """
        MATCH (s:Station)<-[:CAN_COVER]-(w:Worker)
        WITH s, COUNT(w) as coverage_count
        WHERE coverage_count <= 2
        RETURN s.station_code as station_code, s.station_name as station_name,
               coverage_count
        ORDER BY coverage_count
        """
        
        spof_data = execute_query(spof_query)
        
        if spof_data:
            spof_df = pd.DataFrame(spof_data)
            st.warning(f"⚠️ {len(spof_df)} stations with limited worker coverage")
            st.dataframe(spof_df)
        else:
            st.success("✅ All stations have adequate worker coverage")
        
        # Worker details table
        st.subheader("Worker Details")
        st.dataframe(df[['worker_id', 'name', 'role', 'primary_station_name', 'coverable_stations']])
    else:
        st.error("No worker data available")

# Forecast Page
elif page == "Forecast":
    st.title("🔮 Week 9 Forecast")
    
    # Get historical data for trend analysis
    trend_query = """
    MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
    RETURN w.week_id as week, c.total_planned as planned,
           c.total_capacity as capacity, c.deficit as deficit
    ORDER BY w.week_id
    """
    
    trend_data = execute_query(trend_query)
    
    if trend_data:
        df = pd.DataFrame(trend_data)
        
        # Simple linear trend forecast
        weeks = np.arange(1, len(df) + 1)
        planned_trend = np.polyfit(weeks, df['planned'], 1)
        capacity_trend = np.polyfit(weeks, df['capacity'], 1)
        
        # Forecast week 9
        week9_planned = np.polyval(planned_trend, 9)
        week9_capacity = np.polyval(capacity_trend, 9)
        week9_deficit = week9_planned - week9_capacity
        
        # Display forecast
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Week 9 Planned", f"{week9_planned:.0f} hours")
        
        with col2:
            st.metric("Week 9 Capacity", f"{week9_capacity:.0f} hours")
        
        with col3:
            deficit_color = "normal" if week9_deficit < 0 else "inverse"
            st.metric("Week 9 Deficit", f"{week9_deficit:.0f} hours", delta=f"{week9_deficit:.0f}")
        
        # Trend visualization
        st.subheader("Historical Trend & Forecast")
        
        # Extend dataframe with forecast
        forecast_row = {'week': 'w9', 'planned': week9_planned, 'capacity': week9_capacity}
        df_extended = pd.concat([df, pd.DataFrame([forecast_row])], ignore_index=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['week'],
            y=df['planned'],
            mode='lines+markers',
            name='Historical Planned',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=df['week'],
            y=df['capacity'],
            mode='lines+markers',
            name='Historical Capacity',
            line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=['w9'],
            y=[week9_planned],
            mode='markers',
            name='Forecast Planned',
            marker=dict(color='blue', size=10, symbol='diamond')
        ))
        fig.add_trace(go.Scatter(
            x=['w9'],
            y=[week9_capacity],
            mode='markers',
            name='Forecast Capacity',
            marker=dict(color='green', size=10, symbol='diamond')
        ))
        fig.update_layout(title='Capacity Planning Forecast')
        st.plotly_chart(fig, use_container_width=True)
        
        # Alert if predicted overload
        if week9_deficit > 0:
            st.error(f"⚠️ Week 9 predicted overload: {week9_deficit:.0f} hours deficit")
            st.write("Recommendation: Consider adding overtime or hiring temporary staff")
        else:
            st.success("✅ Week 9 capacity appears sufficient")
    else:
        st.error("No historical data available for forecasting")

# Self-Test Page
elif page == "Self-Test":
    st.title("🧪 System Self-Test")
    
    st.subheader("Database Connectivity")
    
    # Test database connection
    connection_test = execute_query("RETURN 1 as test")
    if connection_test:
        st.success("✅ Database connection successful")
    else:
        st.error("❌ Database connection failed")
    
    # Node count test
    st.subheader("Node Count Tests")
    node_query = """
    MATCH (n) 
    WITH labels(n)[0] as label, count(n) as count
    RETURN label, count
    ORDER BY label
    """
    
    node_data = execute_query(node_query)
    if node_data:
        df_nodes = pd.DataFrame(node_data)
        total_nodes = df_nodes['count'].sum()
        
        # Test minimum node count
        if total_nodes >= 50:
            st.success(f"✅ Total nodes: {total_nodes} (≥50 required)")
        else:
            st.error(f"❌ Total nodes: {total_nodes} (<50 required)")
        
        # Test label count
        label_count = len(df_nodes)
        if label_count >= 6:
            st.success(f"✅ Node labels: {label_count} (≥6 required)")
        else:
            st.error(f"❌ Node labels: {label_count} (<6 required)")
        
        st.dataframe(df_nodes)
    
    # Relationship count test
    st.subheader("Relationship Count Test")
    rel_query = """
    MATCH ()-[r]->()
    RETURN count(r) as relationship_count
    """
    
    rel_data = execute_query(rel_query)
    if rel_data:
        rel_count = rel_data[0]['relationship_count']
        if rel_count >= 100:
            st.success(f"✅ Total relationships: {rel_count} (≥100 required)")
        else:
            st.error(f"❌ Total relationships: {rel_count} (<100 required)")
    
    # Relationship type test
    rel_type_query = """
    MATCH ()-[r]->()
    RETURN DISTINCT type(r) as relationship_type, count(r) as count
    ORDER BY relationship_type
    """
    
    rel_type_data = execute_query(rel_type_query)
    if rel_type_data:
        df_rel_types = pd.DataFrame(rel_type_data)
        rel_type_count = len(df_rel_types)
        
        if rel_type_count >= 8:
            st.success(f"✅ Relationship types: {rel_type_count} (≥8 required)")
        else:
            st.error(f"❌ Relationship types: {rel_type_count} (<8 required)")
        
        st.dataframe(df_rel_types)
    
    # Variance query test
    st.subheader("Variance Query Test")
    variance_test = execute_query("""
        MATCH (p:Project)
        RETURN AVG(p.variance_percent) as avg_variance
    """)
    
    if variance_test:
        avg_variance = variance_test[0]['avg_variance']
        st.success(f"✅ Variance query working: {avg_variance:.2f}% average variance")
    
    # Overall score
    st.subheader("🏆 Overall System Health")
    
    score = 0
    max_score = 6
    
    if connection_test:
        score += 1
    if node_data and sum(row['count'] for row in node_data) >= 50:
        score += 1
    if node_data and len(node_data) >= 6:
        score += 1
    if rel_data and rel_data[0]['relationship_count'] >= 100:
        score += 1
    if rel_type_data and len(rel_type_data) >= 8:
        score += 1
    if variance_test:
        score += 1
    
    percentage = (score / max_score) * 100
    
    if percentage >= 90:
        st.success(f"🎉 System Health: {percentage:.0f}% - Excellent")
    elif percentage >= 70:
        st.warning(f"⚠️ System Health: {percentage:.0f}% - Good")
    else:
        st.error(f"❌ System Health: {percentage:.0f}% - Needs Attention")
    
    st.write(f"Score: {score}/{max_score}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏭 Factory Production Dashboard")
st.sidebar.markdown("Built with Neo4j + Streamlit")
