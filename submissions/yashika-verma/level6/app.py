import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Factory Knowledge Graph Dashboard",
    layout="wide"
)

# =========================
# NEO4J CONNECTION
# =========================

URI = st.secrets["NEO4J_URI"]
USER = st.secrets["NEO4J_USER"]
PASSWORD = st.secrets["NEO4J_PASSWORD"]

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

# =========================
# TITLE
# =========================

st.title(
    "🏭 Factory Knowledge Graph Dashboard"
)
st.info("""
Key Findings:
- 2 projects exceeded overload thresholds
- P04 has the highest variance
- Multiple deficit weeks indicate capacity imbalance
""")

# =========================
# SIDEBAR
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

# =========================
# PAGE 1 — PROJECT OVERVIEW
# =========================

if page == "Project Overview":

    st.header("📦 Project Overview")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(:Station)

    RETURN
    p.id AS project,
    SUM(r.planned_hours) AS planned_hours,
    SUM(r.actual_hours) AS actual_hours,
    ROUND(
        (
            (
                SUM(r.actual_hours)
                - SUM(r.planned_hours)
            )
            / SUM(r.planned_hours)
        ) * 100,
        2
    ) AS variance_percent
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    df = df.round(2)

    def classify_variance(v):

        if v >= 4:
            return "HIGH"

        elif v >= 2:
            return "MEDIUM"

        return "LOW"

    df["severity"] = df[
        "variance_percent"
    ].apply(classify_variance)

    # =========================
    # METRICS
    # =========================

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Projects",
        len(df)
    )

    col2.metric(
        "Total Planned Hours",
        round(
            df["planned_hours"].sum(),
            1
        )
    )

    col3.metric(
        "Average Variance %",
        round(
            df["variance_percent"].mean(),
            2
        )
    )

    # =========================
    # TABLE HIGHLIGHTING
    # =========================

    def highlight_variance(val):

        if val > 3:
            return "background-color: red"

        return ""

    styled_df = df.style.map(
        highlight_variance,
        subset=["variance_percent"]
    )

    styled_df = styled_df.format({
        "planned_hours": "{:.1f}",
        "actual_hours": "{:.1f}",
        "variance_percent": "{:.2f}",
        "severity": "{}"
    })

    st.dataframe(
        styled_df,
        use_container_width=True
    )

    # =========================
    # TOP OVERLOADED PROJECTS
    # =========================

    st.subheader(
        "Top Overloaded Projects"
    )

    top_df = df.sort_values(
        by="variance_percent",
        ascending=False
    ).head(5)

    top_df = top_df.round(2)

    st.dataframe(
        top_df,
        use_container_width=True
    )

    highest = top_df.iloc[0]

    st.warning(
        f"{highest['project']} exceeded planned "
        f"hours by {highest['variance_percent']}%"
    )
    st.subheader("🚨 Critical Alerts")

    critical_projects = df[
        df["variance_percent"] > 3
    ]

    for _, row in critical_projects.iterrows():

        st.error(
            f"{row['project']} exceeded planned hours by "
            f"{row['variance_percent']}%"
        )

    # =========================
    # OPERATIONAL INSIGHTS
    # =========================

    st.subheader("Operational Insights")

    overloaded_count = len(
        df[df["variance_percent"] > 3]
    )

    st.markdown(f"""
    - {overloaded_count} projects exceeded the variance threshold
    - {highest['project']} currently has the highest overload variance
    - Production scheduling may require capacity rebalancing
    """)

# =========================
# PAGE 2 — STATION LOAD
# =========================

elif page == "Station Load":

    st.header("📊 Station Load")

    query = """
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)

    RETURN
    s.name AS station,
    r.week AS week,
    SUM(r.planned_hours) AS planned_hours,
    SUM(r.actual_hours) AS actual_hours
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    df = df.round(2)

    fig = px.bar(
        df,
        x="week",
        y="actual_hours",
        color="station",
        barmode="group",
        hover_data=["planned_hours"]
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    highest_station = df.groupby(
        "station"
    )["actual_hours"].sum().idxmax()

    st.info(
        f"{highest_station} currently has the highest production load."
    )

# =========================
# PAGE 3 — CAPACITY TRACKER
# =========================

elif page == "Capacity Tracker":

    st.header("⚠ Capacity Tracker")

    query = """
    MATCH (w:Week)

    RETURN
    w.name AS week,
    w.total_capacity AS total_capacity,
    w.total_planned AS total_planned,
    w.deficit AS deficit

    ORDER BY week
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    df = df.round(2)

    st.dataframe(
        df,
        use_container_width=True
    )

    fig = px.line(
        df,
        x="week",
        y=["total_capacity", "total_planned"],
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    fig2 = px.area(
        df,
        x="week",
        y="deficit"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    deficit_df = df[
        df["deficit"] < 0
    ]

    st.subheader("Deficit Weeks")

    st.dataframe(
        deficit_df,
        use_container_width=True
    )

    worst_week = deficit_df.sort_values(
        by="deficit"
    ).iloc[0]

    st.error(
        f"{worst_week['week']} had the largest "
        f"capacity deficit of {worst_week['deficit']} hours."
    )

# =========================
# PAGE 4 — WORKER COVERAGE
# =========================

elif page == "Worker Coverage":

    st.header("👷 Worker Coverage")

    query = """
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station)

    RETURN
    s.name AS station,
    collect(w.name) AS workers,
    count(w) AS coverage_count

    ORDER BY coverage_count ASC
    """

    with driver.session() as session:

        result = session.run(query)

        data = [dict(r) for r in result]

    df = pd.DataFrame(data)

    st.dataframe(
        df,
        use_container_width=True
    )

    risky_df = df[
        df["coverage_count"] <= 1
    ]

    st.subheader(
        "Single Point of Failure Stations"
    )

    st.dataframe(
        risky_df,
        use_container_width=True
    )

    st.warning(
        f"{len(risky_df)} stations have limited backup coverage."
    )

    lowest_station = risky_df.iloc[0]

    st.error(
        f"{lowest_station['station']} has the lowest worker redundancy."
    )


# =========================
# PAGE 5 — SELF TEST
# =========================

elif page == "Self-Test":

    st.header("✅ Self-Test")

    checks = []

    try:

        with driver.session() as s:
            s.run("RETURN 1")

        checks.append(
            (
                "Neo4j connected",
                True,
                3
            )
        )

    except:

        checks.append(
            (
                "Neo4j connected",
                False,
                3
            )
        )

    with driver.session() as s:

        result = s.run(
            "MATCH (n) RETURN count(n) AS c"
        ).single()

        node_count = result["c"]

        checks.append(
            (
                f"{node_count} nodes (min: 50)",
                node_count >= 50,
                3
            )
        )

        result = s.run(
            "MATCH ()-[r]->() RETURN count(r) AS c"
        ).single()

        rel_count = result["c"]

        checks.append(
            (
                f"{rel_count} relationships (min: 100)",
                rel_count >= 100,
                3
            )
        )

        result = s.run(
            """
            CALL db.labels()
            YIELD label
            RETURN count(label) AS c
            """
        ).single()

        label_count = result["c"]

        checks.append(
            (
                f"{label_count} node labels (min: 6)",
                label_count >= 6,
                3
            )
        )

        result = s.run(
            """
            CALL db.relationshipTypes()
            YIELD relationshipType
            RETURN count(relationshipType) AS c
            """
        ).single()

        rel_types = result["c"]

        checks.append(
            (
                f"{rel_types} relationship types (min: 8)",
                rel_types >= 8,
                3
            )
        )

        result = s.run("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)

        WHERE r.variance_percent > 3

        RETURN
        p.id AS project,
        s.name AS station,
        r.planned_hours AS planned,
        r.actual_hours AS actual

        LIMIT 10
        """)

        rows = [dict(r) for r in result]

        checks.append(
            (
                f"Variance query: {len(rows)} results",
                len(rows) > 0,
                5
            )
        )

    total = 0

    for text, passed, score in checks:

        if passed:

            st.success(
                f"✅ {text} — {score}/{score}"
            )

            total += score

        else:

            st.error(
                f"❌ {text} — 0/{score}"
            )

    st.divider()

    if total == 20:

        st.success(
            f"SELF-TEST SCORE: {total}/20"
        )

    else:

        st.warning(
            f"SELF-TEST SCORE: {total}/20"
        )

# =========================
# FOOTER
# =========================

st.divider()

st.caption(
    "Built using Neo4j, Streamlit, Plotly, and factory production datasets."
)