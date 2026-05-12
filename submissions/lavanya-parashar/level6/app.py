import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ── connection ────────────────────────────────────────────────────────────────


@st.cache_resource
def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    return GraphDatabase.driver(uri, auth=(user, password))

def query(cypher, **params):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, **params)
        return [dict(r) for r in result]

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Factory Production Dashboard",
    page_icon="🏭",
    layout="wide"
)

# ── sidebar navigation ────────────────────────────────────────────────────────

st.sidebar.image("https://img.icons8.com/fluency/96/factory.png", width=60)
st.sidebar.title("Factory Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Project Overview", "Station Load", "Capacity Tracker", "Worker Coverage", "Self-Test"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Swedish Steel Fabrication Co.")
st.sidebar.caption("Graph: Neo4j Aura | UI: Streamlit")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — PROJECT OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if page == "Project Overview":
    st.title("📋 Project Overview")
    st.markdown("All 8 construction projects with planned vs actual hours and variance.")
    st.markdown("---")

    rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
        RETURN
            p.project_id                                            AS id,
            p.project_name                                          AS project,
            p.project_number                                        AS number,
            sum(r.planned_hours)                                    AS total_planned,
            sum(r.actual_hours)                                     AS total_actual,
            round((sum(r.actual_hours) - sum(r.planned_hours))
                / sum(r.planned_hours) * 100)                       AS variance_pct,
            collect(DISTINCT prod.product_type)                     AS products
        ORDER BY variance_pct DESC
    """)

    df = pd.DataFrame(rows)

    # ── top metric cards ──
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Projects", len(df))
    col2.metric("Total Planned Hours", f"{df['total_planned'].sum():.0f} h")
    col3.metric("Total Actual Hours",  f"{df['total_actual'].sum():.0f} h")
    overall_var = (df['total_actual'].sum() - df['total_planned'].sum()) / df['total_planned'].sum() * 100
    col4.metric("Overall Variance", f"{overall_var:.1f}%",
                delta_color="inverse" if overall_var > 0 else "normal")

    st.markdown("---")

    # ── colour coded table ──
    def colour_variance(val):
        if val > 10:
            return "background-color: #ffcccc; color: #7b0000"
        elif val > 5:
            return "background-color: #fff3cc; color: #7a5c00"
        else:
            return "background-color: #ccf0d4; color: #1a5c2a"

    display_df = df.copy()
    display_df["products"] = display_df["products"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    display_df.columns = ["ID", "Project", "Number", "Planned (h)", "Actual (h)", "Variance %", "Products"]

    styled = display_df.style.map(colour_variance, subset=["Variance %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── bar chart planned vs actual ──
    st.subheader("Planned vs Actual Hours per Project")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Planned", x=df["project"], y=df["total_planned"],
                         marker_color="#4C9BE8"))
    fig.add_trace(go.Bar(name="Actual",  x=df["project"], y=df["total_actual"],
                         marker_color="#E8654C"))
    fig.update_layout(barmode="group", xaxis_tickangle=-30,
                      height=420, plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — STATION LOAD
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Station Load":
    st.title("🏗️ Station Load")
    st.markdown("Planned vs actual hours per station, broken down by week.")
    st.markdown("---")

    rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN
            s.station_code          AS station_code,
            s.station_name          AS station,
            r.week                  AS week,
            sum(r.planned_hours)    AS planned_hours,
            sum(r.actual_hours)     AS actual_hours
        ORDER BY station_code, week
    """)

    df = pd.DataFrame(rows)
    df["overloaded"] = df["actual_hours"] > df["planned_hours"]
    df["variance_pct"] = ((df["actual_hours"] - df["planned_hours"])
                          / df["planned_hours"] * 100).round(1)

    # ── week filter ──
    weeks = sorted(df["week"].unique())
    selected_week = st.selectbox("Filter by Week (or see all)", ["All weeks"] + weeks)

    if selected_week != "All weeks":
        df_view = df[df["week"] == selected_week]
    else:
        df_view = df.groupby(["station_code", "station"], as_index=False).agg(
            planned_hours=("planned_hours", "sum"),
            actual_hours=("actual_hours", "sum")
        )
        df_view["overloaded"] = df_view["actual_hours"] > df_view["planned_hours"]

    st.markdown("---")

    # ── grouped bar ──
    st.subheader("Planned vs Actual Hours by Station")
    colours_planned = ["#4C9BE8"] * len(df_view)
    colours_actual  = ["#E8654C" if v else "#5DBE7A" for v in df_view["overloaded"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Planned", x=df_view["station"],
                         y=df_view["planned_hours"], marker_color=colours_planned))
    fig.add_trace(go.Bar(name="Actual",  x=df_view["station"],
                         y=df_view["actual_hours"],  marker_color=colours_actual))
    fig.update_layout(barmode="group", xaxis_tickangle=-30,
                      height=440, plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.1))
    fig.update_traces(hovertemplate="%{x}<br>Hours: %{y:.1f}h")
    st.plotly_chart(fig, use_container_width=True)

    st.caption("🔴 Red actual bars = station overloaded (actual > planned)")

    st.markdown("---")

    # ── overload summary table ──
    st.subheader("Overloaded Stations")
    overloaded = df[df["overloaded"]].copy()
    overloaded = overloaded[["station", "week", "planned_hours", "actual_hours", "variance_pct"]]
    overloaded.columns = ["Station", "Week", "Planned (h)", "Actual (h)", "Variance %"]
    overloaded = overloaded.sort_values("Variance %", ascending=False)
    st.dataframe(overloaded, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CAPACITY TRACKER
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Capacity Tracker":
    st.title("📊 Capacity Tracker")
    st.markdown("Weekly workforce capacity vs planned demand. Red weeks = deficit.")
    st.markdown("---")

    rows = query("""
        MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
        RETURN
            w.week                  AS week,
            c.own_hours             AS own_hours,
            c.hired_hours           AS hired_hours,
            c.overtime_hours        AS overtime_hours,
            c.total_capacity        AS total_capacity,
            c.total_planned         AS total_planned,
            c.deficit               AS deficit
        ORDER BY week
    """)

    df = pd.DataFrame(rows)
    df["status"] = df["deficit"].apply(lambda x: "⚠️ Deficit" if x < 0 else "✅ OK")

    # ── summary metrics ──
    deficit_weeks = df[df["deficit"] < 0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Deficit Weeks", f"{len(deficit_weeks)} / {len(df)}")
    col2.metric("Worst Deficit", f"{deficit_weeks['deficit'].min():.0f} hrs" if len(deficit_weeks) > 0 else "None")
    col3.metric("Total Overtime Used", f"{df['overtime_hours'].sum():.0f} hrs")

    st.markdown("---")

    # ── line chart ──
    st.subheader("Capacity vs Planned Demand by Week")
    fig = go.Figure()

    # shade deficit weeks
    for _, row in df[df["deficit"] < 0].iterrows():
        fig.add_vrect(x0=row["week"], x1=row["week"],
                      fillcolor="rgba(255,80,80,0.12)",
                      layer="below", line_width=0)

    fig.add_trace(go.Scatter(x=df["week"], y=df["total_capacity"],
                             name="Total Capacity", mode="lines+markers",
                             line=dict(color="#4C9BE8", width=2.5),
                             marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=df["week"], y=df["total_planned"],
                             name="Total Planned", mode="lines+markers",
                             line=dict(color="#E8654C", width=2.5),
                             marker=dict(size=8)))

    # deficit annotations
    for _, row in df[df["deficit"] < 0].iterrows():
        fig.add_annotation(x=row["week"], y=row["total_planned"] + 15,
                           text=f"{row['deficit']:.0f}h",
                           showarrow=False, font=dict(color="#cc0000", size=11))

    fig.update_layout(height=440, plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.1),
                      xaxis_title="Week", yaxis_title="Hours")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── stacked bar: capacity breakdown ──
    st.subheader("Capacity Breakdown by Week")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Own Hours",      x=df["week"], y=df["own_hours"],
                          marker_color="#4C9BE8"))
    fig2.add_trace(go.Bar(name="Hired Hours",    x=df["week"], y=df["hired_hours"],
                          marker_color="#5DBE7A"))
    fig2.add_trace(go.Bar(name="Overtime Hours", x=df["week"], y=df["overtime_hours"],
                          marker_color="#F0A500"))
    fig2.update_layout(barmode="stack", height=380,
                       plot_bgcolor="rgba(0,0,0,0)",
                       legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── detail table ──
    st.subheader("Weekly Capacity Table")
    display = df[["week","own_hours","hired_hours","overtime_hours",
                  "total_capacity","total_planned","deficit","status"]].copy()
    display.columns = ["Week","Own Hrs","Hired Hrs","Overtime","Capacity","Planned","Deficit","Status"]

    def colour_deficit(val):
        if isinstance(val, (int, float)) and val < 0:
            return "background-color: #ffcccc; color: #7b0000"
        return ""

    st.dataframe(display.style.map(colour_deficit, subset=["Deficit"]),
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — WORKER COVERAGE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Worker Coverage":
    st.title("👷 Worker Coverage Matrix")
    st.markdown("Which workers cover which stations. Red stations = single point of failure.")
    st.markdown("---")

    # coverage data
    rows = query("""
        MATCH (w:Worker)-[r:WORKS_AT|CAN_COVER]->(s:Station)
        RETURN
            w.name          AS worker,
            w.role          AS role,
            s.station_code  AS station_code,
            s.station_name  AS station,
            type(r)         AS coverage_type
        ORDER BY w.name, s.station_code
    """)

    # spof data
    spof_rows = query("""
        MATCH (w:Worker)-[:WORKS_AT|CAN_COVER]->(s:Station)
        WITH s, collect(DISTINCT w.name) AS workers, count(DISTINCT w) AS coverage
        RETURN
            s.station_code  AS station_code,
            s.station_name  AS station,
            workers         AS covering_workers,
            coverage        AS worker_count,
            CASE WHEN coverage = 1
                 THEN "⚠️ SPOF"
                 ELSE "✅ OK" END AS risk_status
        ORDER BY coverage ASC
    """)

    df       = pd.DataFrame(rows)
    df_spof  = pd.DataFrame(spof_rows)

    # ── spof summary ──
    spof_count = len(df_spof[df_spof["risk_status"] == "⚠️ SPOF"])
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Workers", df["worker"].nunique())
    col2.metric("Total Stations", df["station"].nunique())
    col3.metric("⚠️ SPOF Stations", spof_count)

    st.markdown("---")

    # ── coverage matrix ──
    st.subheader("Coverage Matrix")

    pivot = df.pivot_table(index="worker", columns="station",
                           values="coverage_type", aggfunc="first")
    pivot = pivot.fillna("—")
    pivot = pivot.replace({"WORKS_AT": "🔵 Primary", "CAN_COVER": "🟡 Backup"})

    # highlight SPOF station columns
    spof_stations = df_spof[df_spof["risk_status"] == "⚠️ SPOF"]["station"].tolist()

    def highlight_spof_col(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in df.columns:
            if col in spof_stations:
                styles[col] = "background-color: #ffcccc"
        return styles

    st.dataframe(pivot.style.apply(highlight_spof_col, axis=None),
                 use_container_width=True)

    st.caption("🔵 Primary = WORKS_AT  |  🟡 Backup = CAN_COVER  |  🔴 Red column = Single Point of Failure")

    st.markdown("---")

    # ── spof detail table ──
    st.subheader("Station Risk Summary")
    display_spof = df_spof.copy()
    display_spof["covering_workers"] = display_spof["covering_workers"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else x
    )
    display_spof.columns = ["Code", "Station", "Covering Workers", "Worker Count", "Risk"]

    def colour_risk(val):
        if "SPOF" in str(val):
            return "background-color: #ffcccc; color: #7b0000; font-weight: bold"
        return "background-color: #ccf0d4; color: #1a5c2a"

    st.dataframe(display_spof.style.map(colour_risk, subset=["Risk"]),
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — SELF TEST
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Self-Test":
    st.title("🧪 Self-Test")
    st.markdown("Automated checks to verify the graph is correctly built.")
    st.markdown("---")

    def run_self_test(driver):
        checks = []

        # Check 1 — connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except Exception as e:
            checks.append((f"Neo4j connected — {e}", False, 3))
            return checks

        with driver.session() as s:

            # Check 2 — node count
            result = s.run("MATCH (n) RETURN count(n) AS c").single()
            count = result["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))

            # Check 3 — relationship count
            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))

            # Check 4 — node labels
            result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            count = result["c"]
            checks.append((f"{count} node labels (min: 6)", count >= 6, 3))

            # Check 5 — relationship types
            result = s.run(
                "CALL db.relationshipTypes() YIELD relationshipType "
                "RETURN count(relationshipType) AS c"
            ).single()
            count = result["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))

            # Check 6 — variance query (adapted to our schema)
            result = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN
                    p.project_name  AS project,
                    s.station_name  AS station,
                    r.planned_hours AS planned,
                    r.actual_hours  AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results (min: 1)", len(rows) > 0, 5))

        return checks

    if st.button("▶️ Run Self-Test", type="primary"):
        with st.spinner("Running checks..."):
            driver  = get_driver()
            results = run_self_test(driver)

        total_score = 0
        max_score   = 0

        for label, passed, points in results:
            max_score += points
            if passed:
                total_score += points
                st.success(f"✅  {label}   —   {points}/{points} pts")
            else:
                st.error(  f"❌  {label}   —   0/{points} pts")

        st.markdown("---")
        pct = int(total_score / max_score * 100)

        if total_score == max_score:
            st.balloons()
            st.success(f"### 🎉 SELF-TEST SCORE: {total_score}/{max_score}  ({pct}%)")
        elif total_score >= 14:
            st.warning(f"### ⚠️ SELF-TEST SCORE: {total_score}/{max_score}  ({pct}%)")
        else:
            st.error(  f"### ❌ SELF-TEST SCORE: {total_score}/{max_score}  ({pct}%)")

    else:
        st.info("Click the button above to run all checks.")