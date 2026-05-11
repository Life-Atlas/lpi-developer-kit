import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ────────────────────────────────────────────────────────
st.set_page_config(page_title="Factory Graph Insights", layout="wide", page_icon="🏭")

# ── Sidebar Navigation ────────────────────────────────────────────────
st.sidebar.title("🏭 Factory Graph")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["📋 Project Overview", "📊 Station Load", "🔋 Capacity Tracker", "👷 Worker Coverage", "✅ Self-Test"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.caption("Level 6 — Factory Graph Dashboard")


# ── Neo4j Connection ──────────────────────────────────────────────────
@st.cache_resource
def get_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )

driver = get_driver()


def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([dict(record) for record in result])


# ═══════════════════════════════════════════════════════════════════════
# PAGE 1: PROJECT OVERVIEW
# ═══════════════════════════════════════════════════════════════════════
if page == "📋 Project Overview":
    st.title("📋 Project Overview")
    st.caption("All 8 projects with total planned vs actual hours, variance, and product breakdown.")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    WITH p, 
         sum(r.planned_hours) AS Total_Planned,
         sum(r.actual_hours) AS Total_Actual,
         collect(DISTINCT r.product_type) AS Products,
         count(DISTINCT s) AS Station_Count
    RETURN p.name AS Project, p.number AS Number,
           Total_Planned, Total_Actual,
           round((Total_Actual - Total_Planned) / Total_Planned * 100, 1) AS Variance_Pct,
           Products, Station_Count
    ORDER BY p.id
    """
    df = run_query(query)

    if not df.empty:
        # KPI row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Projects", len(df))
        col2.metric("Total Planned Hours", f"{df['Total_Planned'].sum():,.0f}")
        col3.metric("Total Actual Hours", f"{df['Total_Actual'].sum():,.0f}")
        avg_var = ((df['Total_Actual'].sum() - df['Total_Planned'].sum()) / df['Total_Planned'].sum() * 100)
        col4.metric("Avg Variance", f"{avg_var:+.1f}%")

        st.markdown("---")

        # Variance chart
        fig = px.bar(
            df, x="Project", y="Variance_Pct",
            color="Variance_Pct",
            color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
            title="Variance % by Project (Actual vs Planned)",
            labels={"Variance_Pct": "Variance %"}
        )
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.dataframe(
            df.style.map(
                lambda v: 'color: #e74c3c' if isinstance(v, (int, float)) and v > 5 else
                          'color: #2ecc71' if isinstance(v, (int, float)) and v <= 0 else '',
                subset=['Variance_Pct']
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No project data found. Have you run seed_graph.py?")


# ═══════════════════════════════════════════════════════════════════════
# PAGE 2: STATION LOAD
# ═══════════════════════════════════════════════════════════════════════
elif page == "📊 Station Load":
    st.title("📊 Station Load Analysis")
    st.caption("Actual hours per station across weeks. Overloaded stations are highlighted.")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.name AS Station, s.code AS Code, r.week AS Week,
           sum(r.planned_hours) AS Planned,
           sum(r.actual_hours) AS Actual
    ORDER BY Code, Week
    """
    df = run_query(query)

    if not df.empty:
        # Interactive bar chart
        fig = px.bar(
            df, x="Week", y="Actual", color="Station", barmode="group",
            title="Actual Hours per Station by Week",
            labels={"Actual": "Hours"}
        )
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Heatmap: Overrun ratio
        df['Overrun_Pct'] = ((df['Actual'] - df['Planned']) / df['Planned'] * 100).round(1)
        pivot = df.pivot_table(index='Station', columns='Week', values='Overrun_Pct', aggfunc='mean')
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)

        fig2 = px.imshow(
            pivot, text_auto=".1f",
            color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"],
            title="Overrun % Heatmap (Station × Week)",
            labels={"color": "Overrun %"},
            aspect="auto"
        )
        fig2.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig2, use_container_width=True)

        # Overload table
        overload = df[df['Actual'] > df['Planned']].sort_values('Overrun_Pct', ascending=False)
        if not overload.empty:
            st.warning(f"⚠️ {len(overload)} station-week combinations exceeded planned hours:")
            st.dataframe(overload[['Station', 'Week', 'Planned', 'Actual', 'Overrun_Pct']],
                         use_container_width=True, hide_index=True)
    else:
        st.warning("No station data found. Have you run seed_graph.py?")


# ═══════════════════════════════════════════════════════════════════════
# PAGE 3: CAPACITY TRACKER
# ═══════════════════════════════════════════════════════════════════════
elif page == "🔋 Capacity Tracker":
    st.title("🔋 Weekly Capacity vs Demand")
    st.caption("Capacity breakdown per week. Deficit weeks are flagged in red.")

    query = """
    MATCH (c:Capacity)-[:COVERS]->(w:Week)
    RETURN w.id AS Week, c.own_hours AS Own, c.hired_hours AS Hired,
           c.overtime_hours AS Overtime, c.total_capacity AS Capacity,
           c.total_planned AS Demand, c.deficit AS Deficit
    ORDER BY Week
    """
    df = run_query(query)

    if not df.empty:
        # KPI summary
        deficit_weeks = df[df['Deficit'] < 0]
        surplus_weeks = df[df['Deficit'] >= 0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Deficit Weeks", f"{len(deficit_weeks)} / {len(df)}")
        col2.metric("Worst Deficit", f"{df['Deficit'].min():+,.0f} hrs")
        col3.metric("Total Gap", f"{df['Deficit'].sum():+,.0f} hrs")

        st.markdown("---")

        # Grouped bar chart: Capacity vs Demand
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Week'], y=df['Capacity'], name='Capacity',
            marker_color='#3498db'
        ))
        fig.add_trace(go.Bar(
            x=df['Week'], y=df['Demand'], name='Demand',
            marker_color=df['Deficit'].apply(lambda d: '#e74c3c' if d < 0 else '#2ecc71')
        ))
        fig.update_layout(
            barmode='group', template='plotly_dark',
            title='Capacity vs Demand by Week', height=450,
            yaxis_title='Hours'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stacked capacity breakdown
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df['Week'], y=df['Own'], name='Own Staff', marker_color='#2ecc71'))
        fig2.add_trace(go.Bar(x=df['Week'], y=df['Hired'], name='Hired Staff', marker_color='#3498db'))
        fig2.add_trace(go.Bar(x=df['Week'], y=df['Overtime'], name='Overtime', marker_color='#f39c12'))
        fig2.add_trace(go.Scatter(
            x=df['Week'], y=df['Demand'], name='Demand',
            mode='lines+markers', line=dict(color='#e74c3c', width=3, dash='dot')
        ))
        fig2.update_layout(
            barmode='stack', template='plotly_dark',
            title='Capacity Breakdown (Own + Hired + Overtime) vs Demand', height=400,
            yaxis_title='Hours'
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Color-coded table
        def color_deficit(val):
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'background-color: #c0392b; color: white; font-weight: bold'
                elif val > 0:
                    return 'background-color: #27ae60; color: white'
            return ''

        st.subheader("Weekly Breakdown")
        styled = df.style.map(color_deficit, subset=['Deficit'])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.warning("No capacity data found. Have you run seed_graph.py?")


# ═══════════════════════════════════════════════════════════════════════
# PAGE 4: WORKER COVERAGE
# ═══════════════════════════════════════════════════════════════════════
elif page == "👷 Worker Coverage":
    st.title("👷 Worker Coverage Matrix")
    st.caption("Which workers can cover which stations. Single-point-of-failure stations are flagged.")

    # Coverage matrix
    query = """
    MATCH (w:Worker)
    OPTIONAL MATCH (w)-[:CAN_COVER]->(s:Station)
    OPTIONAL MATCH (w)-[:HAS_CERT]->(c:Certification)
    RETURN w.name AS Worker, w.role AS Role, w.type AS Type,
           collect(DISTINCT s.code) AS Can_Cover,
           collect(DISTINCT c.name) AS Certifications
    ORDER BY Worker
    """
    df = run_query(query)

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Build a proper cross-tab matrix
        matrix_query = """
        MATCH (s:Station)
        OPTIONAL MATCH (w:Worker)-[:CAN_COVER|WORKS_AT]->(s)
        RETURN s.code AS Station_Code, s.name AS Station_Name,
               collect(DISTINCT w.name) AS Workers,
               count(DISTINCT w) AS Worker_Count
        ORDER BY Station_Code
        """
        matrix_df = run_query(matrix_query)

        if not matrix_df.empty:
            st.subheader("Station → Worker Coverage Count")

            # Color-code by coverage count
            def color_coverage(val):
                if isinstance(val, (int, float)):
                    if val <= 1:
                        return 'background-color: #c0392b; color: white; font-weight: bold'
                    elif val <= 2:
                        return 'background-color: #f39c12; color: white'
                    else:
                        return 'background-color: #27ae60; color: white'
                return ''

            styled = matrix_df.style.map(color_coverage, subset=['Worker_Count'])
            st.dataframe(styled, use_container_width=True, hide_index=True)

            # SPOF alert
            spof = matrix_df[matrix_df['Worker_Count'] <= 1]
            if not spof.empty:
                st.error(f"🚨 **{len(spof)} Single-Point-of-Failure Stations** — only 1 worker can operate these:")
                for _, row in spof.iterrows():
                    workers = ', '.join(row['Workers']) if row['Workers'] else 'NONE'
                    st.markdown(f"- **{row['Station_Code']} ({row['Station_Name']})** → {workers}")
    else:
        st.warning("No worker data found. Have you run seed_graph.py?")


# ═══════════════════════════════════════════════════════════════════════
# PAGE 5: SELF-TEST
# ═══════════════════════════════════════════════════════════════════════
elif page == "✅ Self-Test":
    st.title("✅ System Self-Test")
    st.caption("Automated checks to verify the graph meets Level 6 requirements.")

    def run_self_test(driver):
        checks = []
        
        # Check 1: Connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except:
            checks.append(("Neo4j connected", False, 3))
            return checks  # Can't continue
        
        with driver.session() as s:
            # Check 2: Node count
            result = s.run("MATCH (n) RETURN count(n) AS c").single()
            count = result["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))
            
            # Check 3: Relationship count
            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))
            
            # Check 4: Node labels
            result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            count = result["c"]
            checks.append((f"{count} node labels (min: 6)", count >= 6, 3))
            
            # Check 5: Relationship types
            result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))
            
            # Check 6: Variance query
            result = s.run("""
                MATCH (p:Project)-[r]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                    r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
        
        return checks

    results = run_self_test(driver)
    total_score = 0

    st.markdown("### Results")
    for label, passed, pts in results:
        icon = "✅" if passed else "❌"
        score = pts if passed else 0
        st.markdown(f"{icon} **{label}** — `{score}/{pts}`")
        if passed:
            total_score += pts

    st.markdown("---")
    if total_score == 20:
        st.success(f"### 🎉 SELF-TEST SCORE: {total_score}/20")
    elif total_score >= 15:
        st.warning(f"### ⚠️ SELF-TEST SCORE: {total_score}/20")
    else:
        st.error(f"### ❌ SELF-TEST SCORE: {total_score}/20")

    # Show variance results detail
    if total_score > 0:
        st.markdown("---")
        st.subheader("Variance Detail (>10% overrun)")
        var_df = run_query("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.name AS Project, s.name AS Station, r.week AS Week,
                   r.planned_hours AS Planned, r.actual_hours AS Actual,
                   round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1) AS Overrun_Pct
            ORDER BY Overrun_Pct DESC
        """)
        if not var_df.empty:
            st.dataframe(var_df, use_container_width=True, hide_index=True)