import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
@st.cache_resource
def get_driver():
    neo4j_uri = st.secrets.get("NEO4J_URI") or os.getenv("NEO4J_URI")
    neo4j_user = st.secrets.get("NEO4J_USER") or os.getenv("NEO4J_USER")
    neo4j_password = st.secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
    
    return GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def run_query(driver, query):
    """Execute a Cypher query and return results as list of dicts"""
    with driver.session() as session:
        result = session.run(query)
        return [dict(record) for record in result]

# Streamlit config
st.set_page_config(page_title="Factory Graph Dashboard", layout="wide", icon="🏭")
st.title("🏭 Factory Production Knowledge Graph Dashboard")

try:
    driver = get_driver()
    with driver.session() as session:
        session.run("RETURN 1")
    connection_ok = True
except Exception as e:
    st.error(f"❌ Neo4j connection failed: {e}")
    connection_ok = False

if connection_ok:
    # Navigation
    page = st.sidebar.radio(
        "📋 Navigate",
        ["Project Overview", "Station Load", "Capacity Tracker", "Worker Coverage", "Self-Test"],
        key="page_selector"
    )
    
    # Page 1: Project Overview
    if page == "Project Overview":
        st.header("📊 Project Overview")
        st.write("All 8 projects with key performance metrics")
        
        query = """
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH p, r
        RETURN p.name AS project_name,
               p.id AS project_id,
               sum(r.planned_hours) AS total_planned,
               sum(r.actual_hours) AS total_actual
        ORDER BY p.name
        """
        
        results = run_query(driver, query)
        df = pd.DataFrame(results)
        
        df['variance_hours'] = df['total_actual'] - df['total_planned']
        df['variance_pct'] = ((df['variance_hours'] / df['total_planned']) * 100).round(1)
        
        # Get product count per project
        product_query = """
        MATCH (p:Project)-[:PRODUCES]->(prod:Product)
        RETURN p.name AS project_name, count(distinct prod) AS product_count
        """
        product_df = pd.DataFrame(run_query(driver, product_query))
        df = df.merge(product_df, on='project_name', how='left')
        
        # Display
        display_df = df[['project_name', 'total_planned', 'total_actual', 'variance_pct', 'product_count']].copy()
        display_df.columns = ['Project', 'Planned Hours', 'Actual Hours', 'Variance %', 'Products']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Projects", len(df))
        with col2:
            st.metric("Total Planned Hours", int(df['total_planned'].sum()))
        with col3:
            st.metric("Total Actual Hours", int(df['total_actual'].sum()))
        with col4:
            avg_variance = df['variance_pct'].mean()
            st.metric("Avg Variance %", f"{avg_variance:.1f}%")
    
    # Page 2: Station Load
    elif page == "Station Load":
        st.header("⚙️ Station Load Analysis")
        st.write("Hours per station across weeks - Planned vs Actual")
        
        query = """
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.code AS station_code, s.name AS station_name, r.week AS week,
               r.planned_hours AS planned_hours, r.actual_hours AS actual_hours
        ORDER BY s.code, r.week
        """
        
        results = run_query(driver, query)
        df = pd.DataFrame(results)
        
        # Group by station and week
        df_grouped = df.groupby(['week', 'station_code', 'station_name']).agg({
            'planned_hours': 'sum',
            'actual_hours': 'sum'
        }).reset_index()
        
        # Sort by week number
        df_grouped['week_num'] = df_grouped['week'].str.extract(r'(\d+)').astype(int)
        df_grouped = df_grouped.sort_values('week_num')
        
        # Interactive chart
        fig = px.bar(df_grouped, x='week', y=['planned_hours', 'actual_hours'],
                    color_discrete_map={'planned_hours': '#1f77b4', 'actual_hours': '#ff7f0e'},
                    barmode='group',
                    title='Planned vs Actual Hours by Week',
                    labels={'value': 'Hours', 'week': 'Week'},
                    height=500)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Highlight overloaded stations
        st.subheader("⚠️ Overloaded Stations (Actual > Planned)")
        df_overload = df_grouped[df_grouped['actual_hours'] > df_grouped['planned_hours']].copy()
        df_overload['variance'] = (df_overload['actual_hours'] - df_overload['planned_hours']).round(1)
        df_overload = df_overload[['station_code', 'station_name', 'week', 'planned_hours', 'actual_hours', 'variance']].sort_values('variance', ascending=False)
        
        if len(df_overload) > 0:
            st.dataframe(df_overload, use_container_width=True, hide_index=True)
        else:
            st.info("No overloaded stations found")
    
    # Page 3: Capacity Tracker
    elif page == "Capacity Tracker":
        st.header("📈 Weekly Capacity Tracker")
        st.write("Factory capacity vs total planned demand by week")
        
        query = """
        MATCH (w:Week)-[c:HAS_CAPACITY]->(cap:Capacity)
        RETURN w.week AS week, w.week_num AS week_num,
               c.own_staff + c.hired_staff AS basic_staff,
               c.overtime_hours AS overtime,
               c.total_capacity AS total_capacity,
               c.total_planned AS total_planned,
               c.deficit AS deficit
        ORDER BY w.week_num
        """
        
        results = run_query(driver, query)
        df = pd.DataFrame(results)
        
        # Create visualization
        fig = go.Figure()
        
        # Add capacity line
        fig.add_trace(go.Scatter(
            x=df['week'], y=df['total_capacity'],
            mode='lines+markers',
            name='Total Capacity',
            line=dict(color='green', width=3),
            marker=dict(size=10)
        ))
        
        # Add planned demand line
        fig.add_trace(go.Scatter(
            x=df['week'], y=df['total_planned'],
            mode='lines+markers',
            name='Total Planned Demand',
            line=dict(color='blue', width=3),
            marker=dict(size=10)
        ))
        
        # Add deficit fill
        fig.add_trace(go.Scatter(
            x=df['week'], y=df['total_planned'],
            fill='tonexty',
            name='Deficit Area',
            fillcolor='rgba(255,0,0,0.2)',
            line=dict(width=0),
            showlegend=True
        ))
        
        fig.update_layout(
            title='Capacity vs Planned Demand',
            xaxis_title='Week',
            yaxis_title='Hours',
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Deficit summary
        st.subheader("🚨 Deficit Summary")
        deficit_weeks = df[df['deficit'] < 0].copy()
        deficit_weeks['deficit_abs'] = abs(deficit_weeks['deficit'])
        
        if len(deficit_weeks) > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Deficit Weeks", len(deficit_weeks))
            with col2:
                st.metric("Total Deficit Hours", int(deficit_weeks['deficit_abs'].sum()))
            with col3:
                worst_week = deficit_weeks.loc[deficit_weeks['deficit_abs'].idxmax(), 'week']
                st.metric("Worst Week", worst_week)
            
            st.dataframe(deficit_weeks[['week', 'total_capacity', 'total_planned', 'deficit']], 
                        use_container_width=True, hide_index=True)
        else:
            st.success("✅ No deficit weeks - all capacity requirements met!")
    
    # Page 4: Worker Coverage
    elif page == "Worker Coverage":
        st.header("👥 Worker Coverage Matrix")
        st.write("Worker certifications and station coverage")
        
        query = """
        MATCH (w:Worker), (s:Station)
        OPTIONAL MATCH (w)-[:CAN_COVER]->(s)
        RETURN w.name AS worker_name, w.id AS worker_id, w.role AS role,
               s.code AS station_code, s.name AS station_name,
               CASE WHEN w-[:CAN_COVER]->(s) THEN 1 ELSE 0 END AS can_cover
        ORDER BY w.name, s.code
        """
        
        results = run_query(driver, query)
        df = pd.DataFrame(results)
        
        # Create pivot table
        pivot_df = df.pivot_table(
            index='worker_name',
            columns='station_code',
            values='can_cover',
            aggfunc='first',
            fill_value=0
        )
        
        # Display as heatmap
        fig = px.imshow(pivot_df, 
                       color_continuous_scale=['#d73027', '#1a9850'],
                       labels=dict(color="Can Cover"),
                       title='Worker Station Coverage Matrix',
                       aspect='auto',
                       height=400)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # SPOF (Single Point of Failure) analysis
        st.subheader("⚠️ Single Point of Failure Analysis")
        coverage_count = df[df['can_cover'] == 1].groupby('station_code').size()
        spof_stations = coverage_count[coverage_count <= 1]
        
        if len(spof_stations) > 0:
            st.warning(f"⚠️ **{len(spof_stations)} stations have only 1 certified worker!**")
            spof_detail = df[(df['can_cover'] == 1) & (df['station_code'].isin(spof_stations.index))]
            spof_display = spof_detail[['worker_name', 'role', 'station_code', 'station_name']].copy()
            spof_display.columns = ['Worker', 'Role', 'Station Code', 'Station Name']
            st.dataframe(spof_display, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All stations have multiple certified workers")
    
    # Page 5: Self-Test
    elif page == "Self-Test":
        st.header("🧪 Self-Test & Scoring")
        st.write("Automated checks for graph structure and query functionality")
        
        checks = []
        total_score = 0
        
        # Check 1: Connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("✅", "Neo4j connected", 3, True))
            total_score += 3
        except:
            checks.append(("❌", "Neo4j connected", 3, False))
        
        if total_score > 0:  # Only continue if connected
            with driver.session() as s:
                # Check 2: Node count
                result = s.run("MATCH (n) RETURN count(n) AS c").single()
                count = result['c']
                passed = count >= 50
                if passed:
                    checks.append(("✅", f"{count} nodes (min: 50)", 3, True))
                    total_score += 3
                else:
                    checks.append(("❌", f"{count} nodes (min: 50)", 3, False))
                
                # Check 3: Relationship count
                result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
                count = result['c']
                passed = count >= 100
                if passed:
                    checks.append(("✅", f"{count} relationships (min: 100)", 3, True))
                    total_score += 3
                else:
                    checks.append(("❌", f"{count} relationships (min: 100)", 3, False))
                
                # Check 4: Node labels
                result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
                count = result['c']
                passed = count >= 6
                if passed:
                    checks.append(("✅", f"{count} node labels (min: 6)", 3, True))
                    total_score += 3
                else:
                    checks.append(("❌", f"{count} node labels (min: 6)", 3, False))
                
                # Check 5: Relationship types
                result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
                count = result['c']
                passed = count >= 8
                if passed:
                    checks.append(("✅", f"{count} relationship types (min: 8)", 3, True))
                    total_score += 3
                else:
                    checks.append(("❌", f"{count} relationship types (min: 8)", 3, False))
                
                # Check 6: Variance query
                result = s.run("""
                    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                    WHERE r.actual_hours > r.planned_hours * 1.1
                    RETURN count(*) AS c
                """).single()
                count = result['c']
                passed = count > 0
                if passed:
                    checks.append(("✅", f"Variance query: {count} results", 5, True))
                    total_score += 5
                else:
                    checks.append(("❌", f"Variance query: {count} results", 5, False))
        
        # Display checks with color coding
        st.subheader("Test Results")
        for icon, desc, pts, passed in checks:
            if "Connection" in desc or "nodes" in desc or "relationships" in desc or "labels" in desc or "types" in desc:
                points_text = f"{pts}/3 pts"
            else:
                points_text = f"{pts}/5 pts"
            
            color = "✅" if passed else "❌"
            st.write(f"{color} {desc:<50} {points_text}")
        
        st.divider()
        
        # Final score
        score_text = f"{total_score}/20"
        if total_score >= 20:
            st.success(f"🎉 **SELF-TEST SCORE: {score_text}** ✓ ALL CHECKS PASSED")
        elif total_score >= 15:
            st.info(f"📊 **SELF-TEST SCORE: {score_text}** (Mostly good)")
        else:
            st.warning(f"⚠️ **SELF-TEST SCORE: {score_text}** (Some issues to fix)")

else:
    st.error("Unable to connect to Neo4j. Check credentials in .env or Streamlit secrets.")
    st.info("Make sure you have:")
    st.code("""
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
    """)
