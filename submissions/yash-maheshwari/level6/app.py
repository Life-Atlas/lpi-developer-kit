import os
import streamlit as st
import pandas as pd
import plotly.express as px
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Factory Dashboard", page_icon="🏭", layout="wide")

# ── Connection ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_driver():
    try:
        uri  = st.secrets["NEO4J_URI"]
        user = st.secrets["NEO4J_USER"]
        pwd  = st.secrets["NEO4J_PASSWORD"]
    except:
        uri  = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        pwd  = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, pwd))

driver = get_driver()

def query(cypher, **params):
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher, **params)]

# ── Sidebar ───────────────────────────────────────────────────────────────────
page = st.sidebar.radio("Navigate", [
    "📊 Project Overview",
    "🏗️ Station Load",
    "📅 Capacity Tracker",
    "👷 Worker Coverage",
    "🧪 Self-Test",
])

# ── PAGE 1: Project Overview ──────────────────────────────────────────────────
if page == "📊 Project Overview":
    st.title("📊 Project Overview")

    rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN p.id AS project_id, p.name AS project,
               sum(r.planned_hours) AS planned,
               sum(r.actual_hours)  AS actual
        ORDER BY project_id
    """)
    df = pd.DataFrame(rows)
    df["variance_%"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Projects", len(df))
    col2.metric("Total Planned", f"{df['planned'].sum():.0f} h")
    col3.metric("Total Actual",  f"{df['actual'].sum():.0f} h")

    fig = px.bar(df, x="project", y=["planned","actual"], barmode="group",
                 title="Planned vs Actual Hours per Project")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True, hide_index=True)

# ── PAGE 2: Station Load ──────────────────────────────────────────────────────
elif page == "🏗️ Station Load":
    st.title("🏗️ Station Load")

    rows = query("""
        MATCH (s:Station)-[r:LOADED_IN]->(w:Week)
        RETURN s.name AS station, w.id AS week,
               r.planned_hours AS planned, r.actual_hours AS actual
        ORDER BY s.code, w.id
    """)
    df = pd.DataFrame(rows)
    df["variance_%"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)

    # Heatmap
    pivot = df.pivot(index="station", columns="week", values="variance_%").fillna(0)
    fig = px.imshow(pivot, text_auto=".1f", aspect="auto",
                    color_continuous_scale=["green","yellow","red"],
                    title="Variance % by Station × Week")
    st.plotly_chart(fig, use_container_width=True)

    # Week filter
    week = st.select_slider("Week", sorted(df["week"].unique()))
    fig2 = px.bar(df[df["week"] == week], x="station", y=["planned","actual"],
                  barmode="group", title=f"Station Load — {week}")
    st.plotly_chart(fig2, use_container_width=True)

# ── PAGE 3: Capacity Tracker ──────────────────────────────────────────────────
elif page == "📅 Capacity Tracker":
    st.title("📅 Capacity Tracker")

    rows = query("""
        MATCH (w:Week)
        RETURN w.id AS week, w.total_capacity AS capacity,
               w.total_planned AS planned, w.deficit AS deficit
        ORDER BY w.id
    """)
    df = pd.DataFrame(rows)

    fig = px.bar(df, x="week", y=["capacity","planned"], barmode="group",
                 title="Capacity vs Planned Demand per Week")
    st.plotly_chart(fig, use_container_width=True)

    df["status"] = df["deficit"].apply(lambda x: "🔴 Deficit" if x < 0 else "🟢 Surplus")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ── PAGE 4: Worker Coverage ───────────────────────────────────────────────────
elif page == "👷 Worker Coverage":
    st.title("👷 Worker Coverage")

    rows = query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN w.name AS worker, s.name AS station
        ORDER BY s.code, w.name
    """)
    df = pd.DataFrame(rows)

    matrix = df.pivot_table(index="worker", columns="station", aggfunc="size", fill_value=0)
    matrix_display = matrix.map(lambda x: "✅" if x else "")
    st.subheader("Coverage Matrix")
    st.dataframe(matrix_display, use_container_width=True)

    # Single point of failure
    spof = query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        WITH s, count(w) AS cnt, collect(w.name) AS workers
        WHERE cnt = 1
        RETURN s.name AS station, workers[0] AS only_worker
    """)
    if spof:
        st.warning("⚠️ These stations have only ONE qualified worker:")
        st.dataframe(pd.DataFrame(spof), use_container_width=True, hide_index=True)

# ── PAGE 5: Self-Test ─────────────────────────────────────────────────────────
elif page == "🧪 Self-Test":
    st.title("🧪 Self-Test")

    if st.button("▶️ Run Self-Test", type="primary"):
        checks = []

        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except Exception as e:
            checks.append((f"Neo4j connection failed: {e}", False, 3))

        with driver.session() as s:
            c = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            checks.append((f"{c} nodes (min 50)", c >= 50, 3))

            c = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            checks.append((f"{c} relationships (min 100)", c >= 100, 3))

            c = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
            checks.append((f"{c} node labels (min 6)", c >= 6, 3))

            c = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()["c"]
            checks.append((f"{c} relationship types (min 8)", c >= 8, 3))

            rows = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name, s.name LIMIT 10
            """).data()
            checks.append((f"Variance query: {len(rows)} results (min 1)", len(rows) > 0, 5))

        score = 0
        for label, passed, pts in checks:
            score += pts if passed else 0
            if passed:
                st.success(f"✅ {label} — {pts}/{pts} pts")
            else:
                st.error(f"❌ {label} — 0/{pts} pts")

        st.markdown("---")
        st.markdown(f"## Score: {score}/20")
        st.progress(score / 20)