"""
app.py  —  Factory Knowledge Graph Dashboard
Streamlit app powered by Neo4j.

Pages:
  1. Project Overview   — totals, variance, products per project
  2. Station Load       — planned vs actual hours per station/week (interactive)
  3. Capacity Tracker   — weekly workforce capacity vs demand
  4. Worker Coverage    — who covers which station; single-point-of-failure alert
  5. Self-Test          — automated scoring checklist
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase

# ── Connection ────────────────────────────────────────────────────────────────

@st.cache_resource
def init_driver():
    try:
        uri  = st.secrets["NEO4J_URI"]
        user = st.secrets["NEO4J_USER"]
        pw   = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        uri  = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        pw   = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, pw))


def qry(driver, cypher: str, **params) -> list[dict]:
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher, **params)]


# ── Page 1: Project Overview ──────────────────────────────────────────────────

def page_project_overview(driver):
    st.title("📊 Project Overview")
    st.caption("Aggregated planned vs actual hours across all 8 projects.")

    rows = qry(driver, """
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
        RETURN p.project_id   AS project_id,
               p.project_name AS project_name,
               sum(r.planned_hours) AS total_planned,
               sum(r.actual_hours)  AS total_actual,
               collect(DISTINCT prod.product_type) AS products
        ORDER BY p.project_id
    """)

    df = pd.DataFrame(rows)
    df["variance_pct"] = (
        (df["total_actual"] - df["total_planned"]) / df["total_planned"] * 100
    ).round(1)
    df["products_str"] = df["products"].apply(lambda x: ", ".join(sorted(x)))
    df["status"] = df["variance_pct"].apply(
        lambda v: "🔴 Over" if v > 10 else ("🟡 Near" if v > 0 else "🟢 On track")
    )

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projects", len(df))
    c2.metric("Total Planned hrs", f"{df['total_planned'].sum():.0f}")
    c3.metric("Total Actual hrs",  f"{df['total_actual'].sum():.0f}")
    over_budget = (df["variance_pct"] > 10).sum()
    c4.metric("Projects > 10% over", int(over_budget),
              delta=f"{over_budget}", delta_color="inverse")

    st.divider()

    # Summary table
    display = df[["project_id", "project_name", "total_planned",
                  "total_actual", "variance_pct", "status", "products_str"]].copy()
    display.columns = ["ID", "Project", "Planned hrs", "Actual hrs",
                       "Variance %", "Status", "Products"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.divider()

    # Bar chart
    fig = go.Figure()
    fig.add_bar(name="Planned", x=df["project_name"], y=df["total_planned"],
                marker_color="#4C9BE8")
    fig.add_bar(name="Actual",  x=df["project_name"], y=df["total_actual"],
                marker_color=df["variance_pct"].apply(
                    lambda v: "#E85C4C" if v > 10 else "#5CB85C"))
    fig.update_layout(barmode="group", title="Planned vs Actual Hours by Project",
                      xaxis_title="Project", yaxis_title="Hours",
                      legend=dict(orientation="h"),
                      plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Variance gauge strip
    fig2 = px.bar(df, x="project_name", y="variance_pct",
                  color="variance_pct",
                  color_continuous_scale=["#5CB85C", "#F0AD4E", "#E85C4C"],
                  labels={"project_name": "Project", "variance_pct": "Variance %"},
                  title="Variance % per Project (positive = over plan)")
    fig2.add_hline(y=10, line_dash="dash", line_color="red",
                   annotation_text="10% threshold")
    fig2.update_layout(coloraxis_showscale=False,
                       plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)


# ── Page 2: Station Load ──────────────────────────────────────────────────────

def page_station_load(driver):
    st.title("🏭 Station Load")
    st.caption("Hours per station across weeks. Red bars = actual exceeded plan.")

    rows = qry(driver, """
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.station_name       AS station,
               r.week               AS week,
               sum(r.planned_hours) AS planned_hours,
               sum(r.actual_hours)  AS actual_hours
        ORDER BY station, week
    """)
    df = pd.DataFrame(rows)
    df["over_plan"] = df["actual_hours"] > df["planned_hours"]
    df["variance_pct"] = (
        (df["actual_hours"] - df["planned_hours"]) / df["planned_hours"] * 100
    ).round(1)

    # Filter controls
    col1, col2 = st.columns(2)
    stations = sorted(df["station"].unique())
    sel_stations = col1.multiselect("Filter stations", stations, default=stations)
    weeks = sorted(df["week"].unique())
    sel_weeks = col2.multiselect("Filter weeks", weeks, default=weeks)

    mask = df["station"].isin(sel_stations) & df["week"].isin(sel_weeks)
    dff = df[mask]

    # Grouped bar: planned vs actual
    fig = go.Figure()
    for week in sorted(dff["week"].unique()):
        wdf = dff[dff["week"] == week]
        fig.add_bar(name=f"Planned {week}", x=wdf["station"], y=wdf["planned_hours"],
                    opacity=0.7)
        fig.add_bar(name=f"Actual {week}",  x=wdf["station"], y=wdf["actual_hours"],
                    marker_color=wdf["over_plan"].apply(
                        lambda v: "#E85C4C" if v else "#5CB85C"),
                    opacity=0.9)
    fig.update_layout(barmode="group",
                      title="Station Load: Planned vs Actual Hours per Week",
                      xaxis_title="Station", yaxis_title="Hours",
                      legend=dict(orientation="h", y=-0.25),
                      plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap: variance % by station × week
    pivot = dff.pivot_table(index="station", columns="week",
                            values="variance_pct", aggfunc="mean")
    fig2 = px.imshow(pivot, text_auto=".1f",
                     color_continuous_scale=["#5CB85C", "#F0AD4E", "#E85C4C"],
                     zmin=-20, zmax=20,
                     title="Variance % Heatmap (red = over plan)",
                     labels=dict(x="Week", y="Station", color="Var %"))
    fig2.update_layout(coloraxis_colorbar=dict(title="Var %"))
    st.plotly_chart(fig2, use_container_width=True)

    # Detail table
    with st.expander("📋 Raw data table"):
        st.dataframe(
            dff[["station", "week", "planned_hours", "actual_hours", "variance_pct"]],
            use_container_width=True, hide_index=True,
        )

    # Overrun callouts
    overruns = dff[dff["over_plan"]]
    if not overruns.empty:
        st.warning(f"⚠️ {len(overruns)} station-week combinations exceeded planned hours:")
        for _, r in overruns.iterrows():
            st.write(
                f"  • **{r['station']}** / {r['week']}: "
                f"planned {r['planned_hours']:.0f}h → actual {r['actual_hours']:.0f}h "
                f"({r['variance_pct']:+.1f}%)"
            )


# ── Page 3: Capacity Tracker ──────────────────────────────────────────────────

def page_capacity_tracker(driver):
    st.title("📅 Capacity Tracker")
    st.caption("8-week workforce capacity vs total planned demand. Red = deficit week.")

    rows = qry(driver, """
        MATCH (w:Week)
        RETURN w.week_id        AS week,
               w.own_hours      AS own_hours,
               w.hired_hours    AS hired_hours,
               w.overtime_hours AS overtime_hours,
               w.total_capacity AS total_capacity,
               w.total_planned  AS total_planned,
               w.deficit        AS deficit
        ORDER BY w.week_id
    """)
    df = pd.DataFrame(rows)
    df["deficit_flag"] = df["deficit"] < 0

    # KPI strip
    total_deficit = df[df["deficit"] < 0]["deficit"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Weeks in Deficit", int(df["deficit_flag"].sum()))
    c2.metric("Total Deficit Hours", f"{total_deficit:+.0f}")
    c3.metric("Avg Capacity Utilisation",
              f"{(df['total_planned'] / df['total_capacity'] * 100).mean():.1f}%")

    st.divider()

    # Stacked capacity vs demand
    fig = go.Figure()
    fig.add_bar(name="Own Hours",      x=df["week"], y=df["own_hours"],
                marker_color="#4C9BE8")
    fig.add_bar(name="Hired Hours",    x=df["week"], y=df["hired_hours"],
                marker_color="#7EC8E3")
    fig.add_bar(name="Overtime Hours", x=df["week"], y=df["overtime_hours"],
                marker_color="#F0AD4E")
    fig.add_scatter(name="Total Planned Demand", x=df["week"], y=df["total_planned"],
                    mode="lines+markers",
                    line=dict(color="#E85C4C", width=3, dash="dash"),
                    marker=dict(size=10))
    fig.update_layout(barmode="stack",
                      title="Weekly Capacity Breakdown vs Planned Demand",
                      xaxis_title="Week", yaxis_title="Hours",
                      legend=dict(orientation="h"),
                      plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Deficit bar chart (colour-coded)
    fig2 = px.bar(df, x="week", y="deficit",
                  color="deficit",
                  color_continuous_scale=["#E85C4C", "#F0AD4E", "#5CB85C"],
                  title="Weekly Deficit / Surplus (red = shortfall)",
                  labels={"week": "Week", "deficit": "Deficit (hrs)"})
    fig2.add_hline(y=0, line_color="black", line_width=1)
    fig2.update_layout(coloraxis_showscale=False,
                       plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

    # Table with conditional row colour
    st.subheader("Capacity Detail Table")
    styled = df[["week", "own_hours", "hired_hours", "overtime_hours",
                 "total_capacity", "total_planned", "deficit"]].copy()
    styled.columns = ["Week", "Own hrs", "Hired hrs", "Overtime",
                      "Total Cap", "Total Plan", "Deficit"]

    def highlight_deficit(row):
        if row["Deficit"] < 0:
            return ["background-color: #ffd6d6"] * len(row)
        return [""] * len(row)

    st.dataframe(styled.style.apply(highlight_deficit, axis=1),
                 use_container_width=True, hide_index=True)


# ── Page 4: Worker Coverage ───────────────────────────────────────────────────

def page_worker_coverage(driver):
    st.title("👷 Worker Coverage")
    st.caption("Who can cover which station. 🔴 = only one certified worker (SPOF).")

    # Worker → stations matrix
    rows = qry(driver, """
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN w.worker_id AS worker_id,
               w.name      AS worker,
               w.role      AS role,
               w.type      AS type,
               collect(s.station_name) AS covered_stations
        ORDER BY worker
    """)
    df_workers = pd.DataFrame(rows)

    # Station → worker count (for SPOF detection)
    spof_rows = qry(driver, """
        MATCH (s:Station)
        OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
        WITH s, count(w) AS worker_count
        RETURN s.station_code AS station_code,
               s.station_name AS station,
               worker_count
        ORDER BY worker_count
    """)
    df_spof = pd.DataFrame(spof_rows)
    spof_stations = set(df_spof[df_spof["worker_count"] <= 1]["station"].tolist())

    # Build pivot for heatmap
    all_stations = sorted(
        {s for row in df_workers["covered_stations"] for s in row}
    )
    matrix_data = []
    for _, row in df_workers.iterrows():
        r = {"Worker": row["worker"]}
        for st_name in all_stations:
            r[st_name] = 1 if st_name in row["covered_stations"] else 0
        matrix_data.append(r)
    df_matrix = pd.DataFrame(matrix_data).set_index("Worker")

    # Heatmap
    col_labels = ["🔴 " + s if s in spof_stations else s for s in df_matrix.columns]
    fig = px.imshow(
        df_matrix.values,
        x=col_labels, y=df_matrix.index.tolist(),
        color_continuous_scale=["#F0F0F0", "#4C9BE8"],
        zmin=0, zmax=1,
        title="Worker Coverage Matrix (🔴 column = single-point-of-failure station)",
        labels=dict(x="Station", y="Worker", color="Covers"),
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    # SPOF alert
    if spof_stations:
        st.error(
            f"🚨 Single-Point-of-Failure Stations detected: **{', '.join(sorted(spof_stations))}**\n\n"
            "These stations have only 1 certified worker — any absence causes full stoppage."
        )

    # Station coverage count bar
    fig2 = px.bar(
        df_spof.sort_values("worker_count"),
        x="station", y="worker_count",
        color="worker_count",
        color_continuous_scale=["#E85C4C", "#F0AD4E", "#5CB85C"],
        title="Number of Workers Who Can Cover Each Station",
        labels={"station": "Station", "worker_count": "Eligible Workers"},
    )
    fig2.add_hline(y=1, line_dash="dash", line_color="red",
                   annotation_text="SPOF threshold")
    fig2.update_layout(coloraxis_showscale=False,
                       plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

    # Full worker table
    with st.expander("📋 Worker detail table"):
        display = df_workers.copy()
        display["covered_stations"] = display["covered_stations"].apply(
            lambda x: ", ".join(sorted(x))
        )
        display["spof_flag"] = display["covered_stations"].apply(
            lambda x: "⚠️" if any(s in x for s in spof_stations) else ""
        )
        display.columns = ["ID", "Name", "Role", "Type", "Stations Covered", "SPOF?"]
        st.dataframe(display, use_container_width=True, hide_index=True)


# ── Page 5: Self-Test ─────────────────────────────────────────────────────────

def run_self_test(driver) -> list[tuple[str, bool, int]]:
    checks: list[tuple[str, bool, int]] = []

    # Check 1: Connection alive
    try:
        with driver.session() as s:
            s.run("RETURN 1")
        checks.append(("Neo4j connected", True, 3))
    except Exception as e:
        checks.append((f"Neo4j connection failed: {e}", False, 3))
        return checks  # Can't continue

    with driver.session() as s:
        # Check 2: Node count ≥ 50
        c = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        checks.append((f"{c} nodes (min: 50)", c >= 50, 3))

        # Check 3: Relationship count ≥ 100
        c = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        checks.append((f"{c} relationships (min: 100)", c >= 100, 3))

        # Check 4: ≥ 6 distinct node labels
        c = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        checks.append((f"{c} node labels (min: 6)", c >= 6, 3))

        # Check 5: ≥ 8 distinct relationship types
        c = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN count(relationshipType) AS c"
        ).single()["c"]
        checks.append((f"{c} relationship types (min: 8)", c >= 8, 3))

        # Check 6: Variance query returns results
        result = s.run("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.project_name AS project,
                   s.station_name AS station,
                   r.planned_hours AS planned,
                   r.actual_hours  AS actual
            LIMIT 10
        """)
        rows = [dict(r) for r in result]
        checks.append((f"Variance query: {len(rows)} results (need > 0)", len(rows) > 0, 5))

    return checks


def page_self_test(driver):
    st.title("✅ Self-Test")
    st.caption("Automated checks — runs against your live Neo4j instance.")

    if st.button("▶️  Run Self-Test", type="primary", use_container_width=True):
        with st.spinner("Running checks…"):
            checks = run_self_test(driver)

        total_earned = 0
        total_possible = sum(pts for _, _, pts in checks)

        st.divider()
        for label, passed, pts in checks:
            icon = "✅" if passed else "❌"
            earned = pts if passed else 0
            total_earned += earned
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"{icon} {label}")
            col2.markdown(f"**{earned}/{pts}**")

        st.divider()
        colour = "green" if total_earned == total_possible else (
            "orange" if total_earned >= total_possible * 0.6 else "red"
        )
        st.markdown(
            f"<h2 style='color:{colour}'>SELF-TEST SCORE: {total_earned} / {total_possible}</h2>",
            unsafe_allow_html=True,
        )

        # Show variance detail rows
        if checks[-1][1]:  # variance check passed
            st.subheader("Over-plan details (>10% variance)")
            rows = qry(driver, """
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.project_name AS project,
                       s.station_name AS station,
                       r.week         AS week,
                       r.planned_hours AS planned,
                       r.actual_hours  AS actual,
                       round((r.actual_hours - r.planned_hours)
                             / r.planned_hours * 100, 1) AS variance_pct
                ORDER BY variance_pct DESC
            """)
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Click **Run Self-Test** to start the automated checks.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Factory Dashboard",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar
    st.sidebar.title("🏗️ Factory Dashboard")
    st.sidebar.caption("Swedish Steel Fabrication Co.")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigate",
        [
            "📊 Project Overview",
            "🏭 Station Load",
            "📅 Capacity Tracker",
            "👷 Worker Coverage",
            "✅ Self-Test",
        ],
    )

    st.sidebar.divider()
    st.sidebar.caption("8 projects · 10 stations · 14 workers · 8 weeks")

    # Init driver
    try:
        driver = init_driver()
    except Exception as e:
        st.error(f"❌ Could not connect to Neo4j: {e}")
        st.info("Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in `.env` or Streamlit secrets.")
        return

    # Route
    if page == "📊 Project Overview":
        page_project_overview(driver)
    elif page == "🏭 Station Load":
        page_station_load(driver)
    elif page == "📅 Capacity Tracker":
        page_capacity_tracker(driver)
    elif page == "👷 Worker Coverage":
        page_worker_coverage(driver)
    elif page == "✅ Self-Test":
        page_self_test(driver)


if __name__ == "__main__":
    main()