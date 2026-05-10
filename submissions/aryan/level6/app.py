import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import os

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Factory Production Dashboard",
    layout="wide"
)

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# =========================
# CONNECT TO NEO4J
# =========================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

# =========================
# SIDEBAR NAVIGATION
# =========================

page = st.sidebar.radio(
    "Navigation",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Self-Test"
    ]
)

# ============================================================
# PAGE 1 — PROJECT OVERVIEW
# ============================================================

if page == "Project Overview":

    st.title("Project Overview")

    with driver.session() as session:

        result = session.run("""

        MATCH (p:Project)-[r:USES_STATION]->(s:Station)

        RETURN
            p.name AS project,
            sum(r.planned_hours) AS planned_hours,
            sum(r.actual_hours) AS actual_hours,
            round(
                (
                    (sum(r.actual_hours) - sum(r.planned_hours))
                    / sum(r.planned_hours)
                ) * 100,
                2
            ) AS variance_pct

        ORDER BY variance_pct DESC

        """)

        rows = [dict(r) for r in result]

    df = pd.DataFrame(rows)

    st.dataframe(df, use_container_width=True)

    st.subheader("Project Variance Chart")

    fig = px.bar(
        df,
        x="project",
        y="variance_pct",
        hover_data=["planned_hours", "actual_hours"]
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PAGE 2 — STATION LOAD
# ============================================================

elif page == "Station Load":

    st.title("Station Load")

    with driver.session() as session:

        result = session.run("""

        MATCH (p:Project)-[r:USES_STATION]->(s:Station)

        RETURN
            s.name AS station,
            r.week AS week,
            sum(r.planned_hours) AS planned_hours,
            sum(r.actual_hours) AS actual_hours

        ORDER BY week

        """)

        rows = [dict(r) for r in result]

    df = pd.DataFrame(rows)

    st.dataframe(df, use_container_width=True)

    st.subheader("Planned vs Actual Hours")

    fig = px.bar(
        df,
        x="station",
        y=["planned_hours", "actual_hours"],
        barmode="group",
        animation_frame="week"
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PAGE 3 — CAPACITY TRACKER
# ============================================================

elif page == "Capacity Tracker":

    st.title("Capacity Tracker")

    with driver.session() as session:

        result = session.run("""

        MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)

        RETURN
            w.week AS week,
            c.total_capacity AS total_capacity,
            c.total_planned AS total_planned,
            c.deficit AS deficit,
            c.overtime_hours AS overtime_hours

        ORDER BY week

        """)

        rows = [dict(r) for r in result]

    df = pd.DataFrame(rows)

    st.dataframe(df, use_container_width=True)

    st.subheader("Capacity vs Planned Demand")

    fig = px.line(
        df,
        x="week",
        y=["total_capacity", "total_planned"]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Deficit by Week")

    fig2 = px.bar(
        df,
        x="week",
        y="deficit"
    )

    st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# PAGE 4 — WORKER COVERAGE
# ============================================================

elif page == "Worker Coverage":

    st.title("Worker Coverage")

    with driver.session() as session:

        result = session.run("""

        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)

        RETURN
            w.name AS worker,
            collect(s.station_code) AS stations

        """)

        rows = [dict(r) for r in result]

    df = pd.DataFrame(rows)

    st.subheader("Coverage Matrix")

    st.dataframe(df, use_container_width=True)

    st.subheader("Single Point of Failure Stations")

    with driver.session() as session:

        result = session.run("""

        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)

        WITH s, count(w) AS workers

        WHERE workers = 1

        RETURN
            s.station_code AS station,
            workers

        """)

        risk_rows = [dict(r) for r in result]

    risk_df = pd.DataFrame(risk_rows)

    st.dataframe(risk_df, use_container_width=True)

# ============================================================
# PAGE 5 — SELF TEST
# ============================================================

elif page == "Self-Test":

    st.title("Self-Test")

    def run_self_test(driver):

        checks = []

        # =========================
        # CHECK 1 — CONNECTION
        # =========================

        try:

            with driver.session() as s:
                s.run("RETURN 1")

            checks.append(("Neo4j connected", True, 3))

        except:

            checks.append(("Neo4j connected", False, 3))

            return checks

        with driver.session() as s:

            # =========================
            # CHECK 2 — NODE COUNT
            # =========================

            result = s.run("""
            MATCH (n)
            RETURN count(n) AS c
            """).single()

            node_count = result["c"]

            checks.append((
                f"{node_count} nodes (min: 50)",
                node_count >= 50,
                3
            ))

            # =========================
            # CHECK 3 — REL COUNT
            # =========================

            result = s.run("""
            MATCH ()-[r]->()
            RETURN count(r) AS c
            """).single()

            rel_count = result["c"]

            checks.append((
                f"{rel_count} relationships (min: 100)",
                rel_count >= 100,
                3
            ))

            # =========================
            # CHECK 4 — NODE LABELS
            # =========================

            result = s.run("""
            CALL db.labels()
            YIELD label
            RETURN count(label) AS c
            """).single()

            label_count = result["c"]

            checks.append((
                f"{label_count} node labels (min: 6)",
                label_count >= 6,
                3
            ))

            # =========================
            # CHECK 5 — REL TYPES
            # =========================

            result = s.run("""
            CALL db.relationshipTypes()
            YIELD relationshipType
            RETURN count(relationshipType) AS c
            """).single()

            rel_type_count = result["c"]

            checks.append((
                f"{rel_type_count} relationship types (min: 8)",
                rel_type_count >= 8,
                3
            ))

            # =========================
            # CHECK 6 — VARIANCE QUERY
            # =========================

            result = s.run("""

            MATCH (p:Project)-[r:USES_STATION]->(s:Station)

            WHERE r.actual_hours > r.planned_hours * 1.1

            RETURN
                p.name AS project,
                s.name AS station,
                r.planned_hours AS planned,
                r.actual_hours AS actual

            LIMIT 10

            """)

            rows = [dict(r) for r in result]

            checks.append((
                f"Variance query: {len(rows)} results",
                len(rows) > 0,
                5
            ))

        return checks

    checks = run_self_test(driver)

    total_score = 0
    max_score = 20

    for label, passed, points in checks:

        if passed:

            st.success(f"✅ {label}   {points}/{points}")

            total_score += points

        else:

            st.error(f"❌ {label}   0/{points}")

    st.markdown("---")

    st.subheader(f"SELF-TEST SCORE: {total_score}/{max_score}")

# =========================
# CLOSE DRIVER
# =========================

driver.close()
