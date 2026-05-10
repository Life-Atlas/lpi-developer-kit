""" app.py — Factory Knowledge Graph Dashboard
Level 6 Submission: Harshit Kumar (hrk0503)

Streamlit dashboard with 5 pages:
  1. Project Overview
  2. Station Load
  3. Capacity Tracker
  4. Worker Coverage
  5. Self-Test

All data fetched from Neo4j (not raw CSV).
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# -- Neo4j connection (cached) --
@st.cache_resource
def get_driver():
    try:
        uri      = st.secrets.get("NEO4J_URI",      os.getenv("NEO4J_URI",      ""))
        user     = st.secrets.get("NEO4J_USER",     os.getenv("NEO4J_USER",     "neo4j"))
        password = st.secrets.get("NEO4J_PASSWORD",  os.getenv("NEO4J_PASSWORD", ""))
    except FileNotFoundError:
        uri      = os.getenv("NEO4J_URI",      "")
        user     = os.getenv("NEO4J_USER",     "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
    return GraphDatabase.driver(uri, auth=(user, password))


def run_query(query, params=None):
    """Execute a Cypher query and return results as a list of dicts."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(r) for r in result]


# -- Sidebar navigation --
st.set_page_config(
    page_title="Factory KG Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.sidebar.title("🏭 Factory Graph")
st.sidebar.markdown("**Harshit Kumar** | Level 6")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Project Overview",
        "🏗️ Station Load",
        "⚡ Capacity Tracker",
        "👷 Worker Coverage",
        "🧪 Self-Test",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption("Data: 8 projects, 9 stations, 13 workers, 8 weeks")
st.sidebar.caption("Source: Neo4j Aura Free")


# == PAGE 1: Project Overview ==
if page == "📊 Project Overview":
    st.title("📊 Project Overview")
    st.markdown("All 8 construction projects — planned vs actual hours and variance.")

    try:
        rows = run_query("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            RETURN p.id AS project_id,
                   p.name AS project_name,
                   sum(r.planned_hours) AS total_planned,
                   sum(r.actual_hours)  AS total_actual,
                   count(DISTINCT s.code) AS stations_used
            ORDER BY p.id
        """)
        if rows:
            df = pd.DataFrame(rows)
            df["variance_pct"] = ((df["total_actual"] - df["total_planned"]) / df["total_planned"] * 100).round(1)
            df["status"] = df["variance_pct"].apply(
                lambda v: "Over" if v > 10 else ("Near" if v > 0 else "On Track")
            )
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Projects", len(df))
            col2.metric("Total Planned Hours", f"{df['total_planned'].sum():.0f}h")
            col3.metric("Total Actual Hours",  f"{df['total_actual'].sum():.0f}h")
            over_budget = (df["variance_pct"] > 10).sum()
            col4.metric("Projects Over Budget", f"{over_budget}/8")
            st.markdown("---")
            display_df = df[["project_id","project_name","total_planned","total_actual","variance_pct","stations_used","status"]].copy()
            display_df.columns = ["ID","Project","Planned (h)","Actual (h)","Variance %","Stations","Status"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.markdown("---")
            fig = px.bar(
                df, x="project_name", y=["total_planned","total_actual"],
                barmode="group",
                labels={"value":"Hours","project_name":"Project","variable":"Type"},
                title="Planned vs Actual Hours per Project",
                color_discrete_map={"total_planned":"#4A90D9","total_actual":"#E05C5C"},
            )
            fig.update_layout(xaxis_tickangle=-30, legend_title="")
            fig.data[0].name = "Planned"
            fig.data[1].name = "Actual"
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data found. Have you run seed_graph.py?")
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure Neo4j credentials are set in Streamlit secrets or .env file.")


# == PAGE 2: Station Load ==
elif page == "🏗️ Station Load":
    st.title("🏗️ Station Load")
    st.markdown("Hours per station across weeks — red = actual exceeds planned.")

    try:
        rows = run_query("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            RETURN s.name AS station, r.week AS week,
                   sum(r.actual_hours)  AS actual_hours,
                   sum(r.planned_hours) AS planned_hours
            ORDER BY station, week
        """)
        if rows:
            df = pd.DataFrame(rows)
            df["over_planned"] = df["actual_hours"] > df["planned_hours"]
            pivot = df.pivot_table(index="station", columns="week", values="actual_hours", aggfunc="sum").fillna(0)
            fig = px.imshow(
                pivot,
                labels=dict(x="Week", y="Station", color="Actual Hours"),
                title="Actual Hours per Station x Week",
                color_continuous_scale="YlOrRd", aspect="auto",
            )
            st.plotly_chart(fig, use_container_width=True)
            station_sum = df.groupby("station")[["planned_hours","actual_hours"]].sum().reset_index()
            fig2 = px.bar(
                station_sum, x="station", y=["planned_hours","actual_hours"],
                barmode="group", title="Total Planned vs Actual by Station",
                color_discrete_map={"planned_hours":"#4A90D9","actual_hours":"#E05C5C"},
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data found. Have you run seed_graph.py?")
    except Exception as e:
        st.error(f"Database error: {e}")


# == PAGE 3: Capacity Tracker ==
elif page == "⚡ Capacity Tracker":
    st.title("⚡ Capacity Tracker")
    try:
        rows = run_query("""
            MATCH (wk:Week)-[:HAS_CAPACITY]->(c:Capacity)
            RETURN wk.id AS week, c.own_hours AS own_hours, c.hired_hours AS hired_hours,
                   c.overtime_hours AS overtime_hours, c.total_capacity AS total_capacity,
                   c.total_planned AS total_planned, c.deficit AS deficit
            ORDER BY wk.id
        """)
        if rows:
            df = pd.DataFrame(rows)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Own Staff",  x=df["week"], y=df["own_hours"],      marker_color="#4A90D9"))
            fig.add_trace(go.Bar(name="Hired Staff", x=df["week"], y=df["hired_hours"],   marker_color="#7BC8A4"))
            fig.add_trace(go.Bar(name="Overtime",   x=df["week"], y=df["overtime_hours"], marker_color="#F5A623"))
            fig.add_trace(go.Scatter(
                name="Demand", x=df["week"], y=df["total_planned"],
                mode="lines+markers", line=dict(color="#E05C5C", width=3)))
            fig.update_layout(barmode="stack", title="Weekly Capacity vs Demand",
                              xaxis_title="Week", yaxis_title="Hours")
            st.plotly_chart(fig, use_container_width=True)
            df["deficit_color"] = df["deficit"].apply(lambda x: "Deficit" if x < 0 else "Surplus")
            fig2 = px.bar(df, x="week", y="deficit", color="deficit_color",
                          color_discrete_map={"Deficit":"#E05C5C","Surplus":"#7BC8A4"},
                          title="Weekly Surplus / Deficit")
            fig2.add_hline(y=0, line_color="black", line_width=1.5)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data found. Have you run seed_graph.py?")
    except Exception as e:
        st.error(f"Database error: {e}")


# == PAGE 4: Worker Coverage ==
elif page == "👷 Worker Coverage":
    st.title("👷 Worker Coverage")
    try:
        rows = run_query("""
            MATCH (w:Worker)-[r:WORKS_AT|CAN_COVER]->(s:Station)
            RETURN w.name AS worker, type(r) AS relationship, s.code AS station_code
            ORDER BY s.code, w.name
        """)
        if rows:
            df = pd.DataFrame(rows)
            all_stations = sorted(df["station_code"].unique())
            all_workers  = sorted(df["worker"].unique())
            matrix_data  = {}
            for worker in all_workers:
                matrix_data[worker] = {}
                for station in all_stations:
                    primary = df[(df["worker"]==worker)&(df["station_code"]==station)&(df["relationship"]=="WORKS_AT")]
                    cover   = df[(df["worker"]==worker)&(df["station_code"]==station)&(df["relationship"]=="CAN_COVER")]
                    matrix_data[worker][station] = "PRIMARY" if not primary.empty else ("COVER" if not cover.empty else "")
            matrix_df = pd.DataFrame(matrix_data).T
            st.markdown("### Coverage Matrix (PRIMARY = main station, COVER = can cover)")
            st.dataframe(matrix_df, use_container_width=True)
        else:
            st.warning("No data found. Have you run seed_graph.py?")
    except Exception as e:
        st.error(f"Database error: {e}")


# == PAGE 5: Self-Test ==
elif page == "🧪 Self-Test":
    st.title("🧪 Self-Test")
    st.markdown("Automated checks against the live Neo4j graph.")
    st.markdown("---")

    if st.button("▶️ Run Self-Test", type="primary"):
        driver = get_driver()
        checks = []
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
            with driver.session() as s:
                n = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
                checks.append((f"{n} nodes (min: 50)", n >= 50, 3))
                r = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
                checks.append((f"{r} relationships (min: 100)", r >= 100, 3))
                labels = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
                checks.append((f"{labels} node labels (min: 6)", labels >= 6, 3))
                rels = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()["c"]
                checks.append((f"{rels} relationship types (min: 8)", rels >= 8, 3))
                var = [dict(r) for r in s.run(
                    "MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station) WHERE r.actual_hours > r.planned_hours * 1.1 RETURN p.name LIMIT 10")]
                checks.append((f"Variance query: {len(var)} results", len(var) > 0, 5))
        except Exception as e:
            checks.append((f"Connection failed: {e}", False, 3))
        score = sum(pts for _, ok, pts in checks if ok)
        total = sum(pts for _, _, pts in checks)
        st.markdown("### Results")
        for label, ok, pts in checks:
            if ok:
                st.success(f"✅ {label} — {pts}/{pts}")
            else:
                st.error(f"❌ {label} — 0/{pts}")
        st.markdown("---")
        pct = round(score / total * 100)
        if score == total:
            st.balloons()
            st.success(f"## 🎉 SELF-TEST SCORE: {score}/{total} ({pct}%)")
        else:
            st.warning(f"## SELF-TEST SCORE: {score}/{total} ({pct}%)")
    else:
        st.info("Click **Run Self-Test** to validate the graph.")
        st.markdown("""
**Checks performed:**
1. Neo4j connection alive (3 pts)
2. Node count >= 50 (3 pts)
3. Relationship count >= 100 (3 pts)
4. 6+ distinct node labels (3 pts)
5. 8+ distinct relationship types (3 pts)
6. Variance query returns results (5 pts)

**Max score: 20/20**
""")
