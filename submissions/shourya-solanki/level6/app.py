import os
import streamlit as st
import pandas as pd
import plotly.express as px
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def query(cypher, **params):
    driver = get_driver()
    with driver.session() as s:
        result = s.run(cypher, **params)
        return [dict(r) for r in result]

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Factory Graph Dashboard", layout="wide")

page = st.sidebar.radio("Navigate", [
    "Project Overview",
    "Station Load",
    "Capacity Tracker",
    "Worker Coverage",
    "Self-Test"
])

# ── Page 1: Project Overview ─────────────────────────────────
if page == "Project Overview":
    st.title("Project Overview")
    st.caption("All 8 projects with planned vs actual hours and variance.")

    rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN p.project_name AS project,
               sum(r.planned_hours) AS planned,
               sum(r.actual_hours) AS actual
        ORDER BY p.project_name
    """)
    df = pd.DataFrame(rows)
    df["variance_%"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)

    for _, row in df.iterrows():
        color = "🔴" if row["variance_%"] > 10 else "🟡" if row["variance_%"] > 0 else "🟢"
        st.metric(
            label=f"{color} {row['project']}",
            value=f"{row['actual']:.0f}h actual",
            delta=f"{row['variance_%']:+.1f}% vs planned"
        )

    st.divider()
    st.dataframe(df.rename(columns={
        "project": "Project",
        "planned": "Planned Hours",
        "actual": "Actual Hours",
        "variance_%": "Variance %"
    }), use_container_width=True)

# ── Page 2: Station Load ──────────────────────────────────────
elif page == "Station Load":
    st.title("Station Load")
    st.caption("Planned vs actual hours per station across all weeks.")

    rows = query("""
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
    RETURN s.station_name AS station,
           r.week AS week,
           sum(r.planned_hours) AS planned,
           sum(r.actual_hours) AS actual
    """)
    df = pd.DataFrame(rows)
    df["overloaded"] = df["actual"] > df["planned"]

    fig = px.bar(
        df, x="station", y=["planned", "actual"],
        barmode="group",
        color_discrete_map={"planned": "#4C9BE8", "actual": "#E8614C"},
        title="Planned vs Actual Hours by Station",
        labels={"value": "Hours", "variable": "Type"}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Overloaded station-weeks")
    overloaded = df[df["overloaded"]][["station", "week", "planned", "actual"]]
    if not overloaded.empty:
        st.dataframe(overloaded, use_container_width=True)
    else:
        st.success("No overloaded stations.")

# ── Page 3: Capacity Tracker ──────────────────────────────────
elif page == "Capacity Tracker":
    st.title("Capacity Tracker")
    st.caption("Weekly workforce capacity vs planned demand. Red = deficit.")

    rows = query("""
        MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
        RETURN w.week_id AS week,
               c.total_capacity AS capacity,
               c.total_planned AS planned,
               c.deficit AS deficit
        ORDER BY week
    """)
    df = pd.DataFrame(rows)

    fig = px.bar(
        df, x="week", y=["capacity", "planned"],
        barmode="group",
        color_discrete_map={"capacity": "#4C9BE8", "planned": "#E8614C"},
        title="Capacity vs Planned Demand by Week"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        df, x="week", y="deficit",
        color="deficit",
        color_continuous_scale=["red", "green"],
        title="Weekly Deficit (negative = over capacity)"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Deficit weeks")
    deficit_weeks = df[df["deficit"] < 0]
    if not deficit_weeks.empty:
        st.dataframe(deficit_weeks, use_container_width=True)

# ── Page 4: Worker Coverage ───────────────────────────────────
elif page == "Worker Coverage":
    st.title("Worker Coverage")
    st.caption("Which workers can cover which stations. Orange = single point of failure.")

    rows = query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN s.station_name AS station,
               collect(w.name) AS workers,
               count(w) AS coverage
        ORDER BY coverage ASC
    """)
    df = pd.DataFrame(rows)
    df["risk"] = df["coverage"].apply(lambda x: "⚠️ Single point of failure" if x == 1 else "✅ OK")

    st.dataframe(df.rename(columns={
        "station": "Station",
        "workers": "Available Workers",
        "coverage": "# Workers",
        "risk": "Risk"
    }), use_container_width=True)

    fig = px.bar(
        df, x="station", y="coverage",
        color="coverage",
        color_continuous_scale=["red", "yellow", "green"],
        title="Worker Coverage per Station"
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Page 5: Self-Test ─────────────────────────────────────────
elif page == "Self-Test":
    st.title("Self-Test")
    st.caption("Automated checks against the Neo4j graph.")

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
            count = result["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))

            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))

            result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            count = result["c"]
            checks.append((f"{count} node labels (min: 6)", count >= 6, 3))

            result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))

            result = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.project_name AS project, s.station_name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))

        return checks

    driver = get_driver()
    checks = run_self_test(driver)
    total = 0
    max_total = 0

    for label, passed, pts in checks:
        max_total += pts
        if passed:
            total += pts
            st.success(f"✅ {label}   {pts}/{pts}")
        else:
            st.error(f"❌ {label}   0/{pts}")

    st.divider()
    st.subheader(f"SELF-TEST SCORE: {total}/{max_total}")