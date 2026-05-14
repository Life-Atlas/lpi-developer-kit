"""
app.py — Factory Knowledge Graph Dashboard
Streamlit app with 5 pages: Overview, Station Load, Capacity Tracker,
Worker Coverage, and Self-Test.

All data comes from Neo4j — not raw CSV reads.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Factory Graph Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Neo4j connection ───────────────────────────────────────────────────────────
@st.cache_resource
def get_driver():
    # Streamlit Cloud uses st.secrets; local dev uses .env
    try:
        uri      = st.secrets["NEO4J_URI"]
        user     = st.secrets.get("NEO4J_USER", "neo4j")
        password = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        uri      = os.getenv("NEO4J_URI")
        user     = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        st.error("⚠️ Neo4j credentials not found. Add them to `.env` or Streamlit secrets.")
        st.stop()

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


def query(cypher, **params):
    driver = get_driver()
    with driver.session() as s:
        result = s.run(cypher, **params)
        return [dict(r) for r in result]


# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.title("🏭 Factory Dashboard")
st.sidebar.markdown("Swedish Steel Fabrication Co.")
st.sidebar.divider()

pages = {
    "📊 Project Overview":    "overview",
    "⚙️ Station Load":        "station_load",
    "📅 Capacity Tracker":    "capacity",
    "👷 Worker Coverage":     "workers",
    "🧪 Self-Test":           "self_test",
}
page_label = st.sidebar.radio("Navigate to", list(pages.keys()))
page = pages[page_label]

st.sidebar.divider()
st.sidebar.caption("Data source: Neo4j Knowledge Graph")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — PROJECT OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "overview":
    st.title("📊 Project Overview")
    st.markdown("All 8 construction projects with planned vs actual hours and variance.")

    rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH p.id AS project_id, p.name AS project_name,
             sum(r.planned_hours) AS total_planned,
             sum(r.actual_hours)  AS total_actual
        RETURN project_id, project_name, total_planned, total_actual
        ORDER BY project_id
    """)

    if not rows:
        st.warning("No project data found. Have you run seed_graph.py?")
        st.stop()

    df = pd.DataFrame(rows)
    df["variance_hrs"] = df["total_actual"] - df["total_planned"]
    df["variance_pct"] = ((df["variance_hrs"] / df["total_planned"]) * 100).round(1)

    # Metrics strip
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Projects", len(df))
    col2.metric("Total Planned Hrs", f"{df['total_planned'].sum():.0f}")
    col3.metric("Total Actual Hrs",  f"{df['total_actual'].sum():.0f}")
    over = df[df["variance_pct"] > 10]
    col4.metric("Projects Over 10% variance", len(over), delta=None)

    st.divider()

    # Bar chart planned vs actual
    fig = go.Figure()
    fig.add_bar(name="Planned", x=df["project_name"], y=df["total_planned"],
                marker_color="#4A90D9")
    fig.add_bar(name="Actual",  x=df["project_name"], y=df["total_actual"],
                marker_color="#E05C5C")
    fig.update_layout(
        barmode="group",
        title="Planned vs Actual Hours per Project",
        xaxis_title="Project",
        yaxis_title="Hours",
        legend_title="Type",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Products per project
    prod_rows = query("""
        MATCH (p:Project)-[:PRODUCES]->(pr:Product)
        WITH p.id AS pid, p.name AS project, collect(pr.code) AS products
        RETURN project, products
        ORDER BY pid
    """)
    prod_map = {r["project"]: ", ".join(sorted(r["products"])) for r in prod_rows}
    df["products"] = df["project_name"].map(prod_map)

    # Styled table
    def colour_variance(val):
        if val > 10:
            return "color: #E05C5C; font-weight: bold"
        elif val < -10:
            return "color: #F0A500; font-weight: bold"
        return ""

    display = df[["project_id", "project_name", "total_planned", "total_actual",
                   "variance_hrs", "variance_pct", "products"]].copy()
    display.columns = ["ID", "Project", "Planned Hrs", "Actual Hrs",
                       "Variance Hrs", "Variance %", "Products"]

    st.dataframe(
        display.style.map(colour_variance, subset=["Variance %"]),
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — STATION LOAD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "station_load":
    st.title("⚙️ Station Load")
    st.markdown("Hours per station per week — **red** means actual > planned.")

    rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH s.code AS code, s.name AS station, r.week AS week,
             sum(r.planned_hours) AS planned, sum(r.actual_hours) AS actual
        RETURN station, code, week, planned, actual
        ORDER BY code, week
    """)

    if not rows:
        st.warning("No station load data found.")
        st.stop()

    df = pd.DataFrame(rows)
    df["overloaded"] = df["actual"] > df["planned"]
    df["label"] = df["station"] + " (" + df["code"] + ")"

    # Week selector
    weeks = sorted(df["week"].unique())
    sel_week = st.selectbox("Filter by week (or All)", ["All"] + weeks)
    if sel_week != "All":
        df = df[df["week"] == sel_week]

    # Grouped bar: planned vs actual per station
    fig = go.Figure()
    fig.add_bar(name="Planned", x=df["label"], y=df["planned"],
                marker_color="#4A90D9", offsetgroup=0)
    fig.add_bar(name="Actual",  x=df["label"], y=df["actual"],
                marker_color=["#E05C5C" if v else "#66BB6A" for v in df["overloaded"]],
                offsetgroup=1)
    fig.update_layout(
        barmode="group",
        title=f"Station Load {'— ' + sel_week if sel_week != 'All' else '(All Weeks, summed)'}",
        xaxis_title="Station",
        yaxis_title="Hours",
        height=430,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap: actual hours by station × week (all data)
    all_rows = query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH s.code AS code, s.name AS station, r.week AS week,
             sum(r.actual_hours) AS actual_hours
        RETURN station, week, actual_hours
        ORDER BY code, week
    """)
    heat_df = pd.DataFrame(all_rows)
    pivot   = heat_df.pivot_table(index="station", columns="week", values="actual_hours", fill_value=0)
    fig2 = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn_r",
        title="Heatmap: Actual Hours by Station × Week",
        aspect="auto",
        labels=dict(color="Actual Hrs"),
    )
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("🔴 **Red cells** = higher actual hours (potential overload)")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CAPACITY TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "capacity":
    st.title("📅 Capacity Tracker")
    st.markdown("Weekly workforce capacity vs total planned demand. **Red = deficit weeks.**")

    rows = query("""
        MATCH (w:Week)-[:HAS_CAPACITY]->(cr:CapacityRecord)
        RETURN w.id AS week,
               cr.own_hours      AS own_hours,
               cr.hired_hours    AS hired_hours,
               cr.overtime_hours AS overtime_hours,
               cr.total_capacity AS total_capacity,
               cr.total_planned  AS total_planned,
               cr.deficit        AS deficit
        ORDER BY w.id
    """)

    if not rows:
        st.warning("No capacity data found.")
        st.stop()

    df = pd.DataFrame(rows)

    # Metrics
    deficit_weeks = df[df["deficit"] < 0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Weeks", len(df))
    c2.metric("Deficit Weeks", len(deficit_weeks))
    c3.metric("Worst Deficit", f"{df['deficit'].min()} hrs")

    st.divider()

    # Stacked area: capacity breakdown
    fig = go.Figure()
    fig.add_bar(name="Own Hours",      x=df["week"], y=df["own_hours"],      marker_color="#4A90D9")
    fig.add_bar(name="Hired Hours",    x=df["week"], y=df["hired_hours"],    marker_color="#7EC8E3")
    fig.add_bar(name="Overtime Hours", x=df["week"], y=df["overtime_hours"], marker_color="#F0A500")
    fig.add_scatter(name="Planned Demand", x=df["week"], y=df["total_planned"],
                    mode="lines+markers", line=dict(color="#E05C5C", width=3, dash="dash"),
                    marker=dict(size=8))
    fig.update_layout(
        barmode="stack",
        title="Capacity Breakdown vs Planned Demand",
        xaxis_title="Week",
        yaxis_title="Hours",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Deficit chart
    colours = ["#E05C5C" if d < 0 else "#66BB6A" for d in df["deficit"]]
    fig2 = go.Figure(go.Bar(
        x=df["week"], y=df["deficit"],
        marker_color=colours,
        text=df["deficit"].apply(lambda x: f"{x:+d} hrs"),
        textposition="outside",
    ))
    fig2.update_layout(
        title="Surplus / Deficit per Week",
        xaxis_title="Week",
        yaxis_title="Hrs (positive = surplus, negative = deficit)",
        height=330,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Table
    styled = df.copy()
    styled.columns = ["Week", "Own Hrs", "Hired Hrs", "OT Hrs",
                      "Total Capacity", "Planned Demand", "Deficit"]

    def highlight_deficit(row):
        return ["background-color: #fde8e8" if row["Deficit"] < 0 else "" for _ in row]

    st.dataframe(
        styled.style.apply(highlight_deficit, axis=1),
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — WORKER COVERAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "workers":
    st.title("👷 Worker Coverage")
    st.markdown("Which workers cover which stations. 🔴 = single-point-of-failure station (only 1 worker certified).")

    # Matrix: worker × station CAN_COVER
    rows = query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN w.name AS worker, w.role AS role, w.type AS type, s.name AS station
        ORDER BY w.id, s.code
    """)

    if not rows:
        st.warning("No worker coverage data found.")
        st.stop()

    df = pd.DataFrame(rows)

    workers_list  = df["worker"].unique().tolist()
    stations_list = sorted(df["station"].unique().tolist())

    # Build binary matrix
    matrix = pd.DataFrame(0, index=workers_list, columns=stations_list)
    for _, row in df.iterrows():
        matrix.loc[row["worker"], row["station"]] = 1

    # Find SPOFs
    spof_stations = [s for s in stations_list if matrix[s].sum() <= 1]

    c1, c2, c3 = st.columns(3)
    c1.metric("Workers", len(workers_list))
    c2.metric("Stations", len(stations_list))
    c3.metric("⚠️ SPOF Stations", len(spof_stations))

    if spof_stations:
        st.warning(f"**Single-Point-of-Failure Stations:** {', '.join(spof_stations)}")

    st.divider()

    # Heatmap matrix
    fig = px.imshow(
        matrix,
        color_continuous_scale=[[0, "#f5f5f5"], [1, "#4A90D9"]],
        title="Worker × Station Coverage Matrix (blue = certified)",
        aspect="auto",
        labels=dict(color="Certified"),
    )
    # Mark SPOF station columns in red
    for i, col in enumerate(stations_list):
        if col in spof_stations:
            fig.add_shape(
                type="rect",
                x0=i - 0.5, x1=i + 0.5, y0=-0.5, y1=len(workers_list) - 0.5,
                line=dict(color="#E05C5C", width=2),
            )
    fig.update_layout(height=420, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🔴 Red border = SPOF station")

    # Station coverage count
    coverage_df = pd.DataFrame({
        "Station": stations_list,
        "Workers Certified": [int(matrix[s].sum()) for s in stations_list],
        "SPOF": ["⚠️ YES" if s in spof_stations else "✅ No" for s in stations_list],
    })
    st.dataframe(coverage_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Worker Details")
    wdetail = query("""
        MATCH (w:Worker)
        RETURN w.id AS id, w.name AS name, w.role AS role, w.type AS type,
               w.hours_per_week AS hrs_week, w.certifications AS certs,
               w.primary_station AS primary_station
        ORDER BY w.id
    """)
    st.dataframe(pd.DataFrame(wdetail), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "self_test":
    st.title("🧪 Self-Test")
    st.markdown("Automated checks against the live Neo4j database.")

    def run_self_test(driver):
        checks = []

        # Check 1: Connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except Exception as e:
            checks.append((f"Neo4j connection failed: {e}", False, 3))
            return checks

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
            result = s.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"
            ).single()
            count = result["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))

            # Check 6: Variance query
            result = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results (min: 1)", len(rows) > 0, 5))

        return checks

    if st.button("▶️ Run Self-Test", type="primary"):
        with st.spinner("Running checks…"):
            driver = get_driver()
            checks = run_self_test(driver)

        total_earned = 0
        total_max    = sum(c[2] for c in checks)

        for label, passed, pts in checks:
            icon   = "✅" if passed else "❌"
            colour = "green" if passed else "red"
            earned = pts if passed else 0
            total_earned += earned
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:6px 12px;margin:4px 0;border-radius:6px;"
                f"background:{'#e8f8e8' if passed else '#fde8e8'}'>"
                f"<span>{icon} {label}</span>"
                f"<strong style='color:{colour}'>{earned}/{pts}</strong></div>",
                unsafe_allow_html=True,
            )

        pct = int(total_earned / total_max * 100)
        st.divider()
        col1, col2 = st.columns([3, 1])
        col1.progress(pct / 100)
        col2.markdown(f"### {total_earned}/{total_max}")
        if total_earned == total_max:
            st.balloons()
            st.success("🎉 Perfect score! All checks passed.")
        elif total_earned >= 15:
            st.info(f"Good progress! {total_max - total_earned} pts to go.")
        else:
            st.error("Some checks failed. Verify seed_graph.py ran successfully.")
    else:
        st.info("Click **Run Self-Test** to execute all 6 automated checks.")
        st.markdown("""
| Check | Points | Criteria |
|-------|--------|----------|
| Neo4j connected | 3 | Database reachable |
| Node count | 3 | ≥ 50 nodes |
| Relationship count | 3 | ≥ 100 relationships |
| Node labels | 3 | ≥ 6 distinct labels |
| Relationship types | 3 | ≥ 8 distinct types |
| Variance query | 5 | Returns projects with actual > 110% planned |
| **Total** | **20** | |
""")