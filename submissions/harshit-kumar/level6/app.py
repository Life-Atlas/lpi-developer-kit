"""
app.py — Factory Knowledge Graph Dashboard
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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Factory KG Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Neo4j connection (cached) ─────────────────────────────────────────────────
@st.cache_resource
def get_driver():
    try:
        uri      = st.secrets.get("NEO4J_URI",      os.getenv("NEO4J_URI",      ""))
        user     = st.secrets.get("NEO4J_USER",     os.getenv("NEO4J_USER",     "neo4j"))
        password = st.secrets.get("NEO4J_PASSWORD", os.getenv("NEO4J_PASSWORD", ""))
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


# ── Sidebar navigation ────────────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: Project Overview
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Project Overview":
    st.title("📊 Project Overview")
    st.markdown("All 8 construction projects — planned vs actual hours and variance.")

    try:
        rows = run_query("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            RETURN
                p.id    AS project_id,
                p.name  AS project_name,
                sum(r.planned_hours) AS total_planned,
                sum(r.actual_hours)  AS total_actual,
                count(DISTINCT s.code) AS stations_used
            ORDER BY p.id
        """)

        if rows:
            df = pd.DataFrame(rows)
            df["variance_pct"] = ((df["total_actual"] - df["total_planned"]) / df["total_planned"] * 100).round(1)
            df["status"] = df["variance_pct"].apply(
                lambda v: "🔴 Over" if v > 10 else ("🟡 Near" if v > 0 else "🟢 On Track")
            )

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Projects", len(df))
            col2.metric("Total Planned Hours", f"{df['total_planned'].sum():.0f}h")
            col3.metric("Total Actual Hours", f"{df['total_actual'].sum():.0f}h")
            over_budget = (df["variance_pct"] > 10).sum()
            col4.metric("Projects Over Budget", f"{over_budget}/8", delta=f"+{over_budget}" if over_budget > 0 else "0")

            st.markdown("---")

            # Table
            display_df = df[["project_id", "project_name", "total_planned", "total_actual", "variance_pct", "stations_used", "status"]].copy()
            display_df.columns = ["ID", "Project", "Planned (h)", "Actual (h)", "Variance %", "Stations", "Status"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Bar chart
            fig = px.bar(
                df,
                x="project_name",
                y=["total_planned", "total_actual"],
                barmode="group",
                labels={"value": "Hours", "project_name": "Project", "variable": "Type"},
                title="Planned vs Actual Hours per Project",
                color_discrete_map={"total_planned": "#4A90D9", "total_actual": "#E05C5C"},
            )
            fig.update_layout(xaxis_tickangle=-30, legend_title="")
            fig.data[0].name = "Planned"
            fig.data[1].name = "Actual"
            st.plotly_chart(fig, use_container_width=True)

            # Products per project
            st.markdown("### Products Involved per Project")
            prod_rows = run_query("""
                MATCH (p:Project)-[:PRODUCES]->(pr:Product)
                RETURN p.id AS pid, p.name AS project, collect(pr.type) AS products
                ORDER BY pid
            """)
            if prod_rows:
                prod_df = pd.DataFrame(prod_rows)
                prod_df["products"] = prod_df["products"].apply(lambda x: ", ".join(sorted(x)))
                prod_df = prod_df.drop(columns=["pid"], errors="ignore")
                st.dataframe(prod_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found. Have you run seed_graph.py?")

    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure Neo4j credentials are set in Streamlit secrets or .env file.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: Station Load
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Station Load":
    st.title("🏗️ Station Load")
    st.markdown("Hours per station across weeks — red = actual exceeds planned.")

    try:
        rows = run_query("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            RETURN
                s.name AS station,
                r.week AS week,
                sum(r.actual_hours)  AS actual_hours,
                sum(r.planned_hours) AS planned_hours
            ORDER BY station, week
        """)

        if rows:
            df = pd.DataFrame(rows)
            df["over_planned"] = df["actual_hours"] > df["planned_hours"]
            df["variance_pct"] = ((df["actual_hours"] - df["planned_hours"]) / df["planned_hours"] * 100).round(1)

            # Pivot for heatmap
            pivot_actual = df.pivot_table(index="station", columns="week", values="actual_hours", aggfunc="sum").fillna(0)
            pivot_planned = df.pivot_table(index="station", columns="week", values="planned_hours", aggfunc="sum").fillna(0)

            # Sort weeks
            week_order = [f"w{i}" for i in range(1, 9)]
            pivot_actual = pivot_actual.reindex(columns=[w for w in week_order if w in pivot_actual.columns])
            pivot_planned = pivot_planned.reindex(columns=[w for w in week_order if w in pivot_planned.columns])

            # Overload mask
            over_mask = pivot_actual > pivot_planned

            col1, col2 = st.columns(2)
            col1.metric("Total Station-Week Combos", len(df))
            overloaded = df["over_planned"].sum()
            col2.metric("Overloaded Station-Weeks", f"{overloaded}/{len(df)}", delta=f"+{overloaded}" if overloaded > 0 else "0", delta_color="inverse")

            st.markdown("---")

            # Heatmap — actual hours
            fig = px.imshow(
                pivot_actual,
                labels=dict(x="Week", y="Station", color="Actual Hours"),
                title="Actual Hours per Station x Week",
                color_continuous_scale="YlOrRd",
                aspect="auto",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Bar chart — actual vs planned per station (summed across all weeks)
            station_sum = df.groupby("station")[["planned_hours", "actual_hours"]].sum().reset_index()
            station_sum["over"] = station_sum["actual_hours"] > station_sum["planned_hours"]
            fig2 = px.bar(
                station_sum,
                x="station",
                y=["planned_hours", "actual_hours"],
                barmode="group",
                title="Total Planned vs Actual by Station (all weeks)",
                labels={"value": "Hours", "station": "Station", "variable": "Type"},
                color_discrete_map={"planned_hours": "#4A90D9", "actual_hours": "#E05C5C"},
            )
            fig2.update_layout(xaxis_tickangle=-30)
            fig2.data[0].name = "Planned"
            fig2.data[1].name = "Actual"
            st.plotly_chart(fig2, use_container_width=True)

            # Overloaded detail table
            st.markdown("### Overloaded Station-Week Records (Actual > Planned)")
            overload_df = df[df["over_planned"]].sort_values("variance_pct", ascending=False)
            if not overload_df.empty:
                st.dataframe(
                    overload_df[["station", "week", "planned_hours", "actual_hours", "variance_pct"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("No overloaded station-week combinations!")
        else:
            st.warning("No data found. Have you run seed_graph.py?")

    except Exception as e:
        st.error(f"Database error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: Capacity Tracker
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚡ Capacity Tracker":
    st.title("⚡ Capacity Tracker")
    st.markdown("Weekly workforce capacity (own + hired + overtime) vs total planned demand.")

    try:
        rows = run_query("""
            MATCH (wk:Week)-[:HAS_CAPACITY]->(c:Capacity)
            RETURN
                wk.id AS week,
                c.own_hours AS own_hours,
                c.hired_hours AS hired_hours,
                c.overtime_hours AS overtime_hours,
                c.total_capacity AS total_capacity,
                c.total_planned AS total_planned,
                c.deficit AS deficit
            ORDER BY wk.id
        """)

        if rows:
            df = pd.DataFrame(rows)

            # Metrics
            total_deficit = df[df["deficit"] < 0]["deficit"].sum()
            deficit_weeks = (df["deficit"] < 0).sum()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Weeks", len(df))
            col2.metric("Deficit Weeks", f"{deficit_weeks}/8", delta=f"{deficit_weeks}" if deficit_weeks > 0 else "0", delta_color="inverse")
            col3.metric("Total Deficit Hours", f"{total_deficit}h", delta=f"{total_deficit}h", delta_color="inverse")

            st.markdown("---")

            # Stacked bar: own + hired + overtime
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Own Staff", x=df["week"], y=df["own_hours"], marker_color="#4A90D9"))
            fig.add_trace(go.Bar(name="Hired Staff", x=df["week"], y=df["hired_hours"], marker_color="#7BC8A4"))
            fig.add_trace(go.Bar(name="Overtime", x=df["week"], y=df["overtime_hours"], marker_color="#F5A623"))
            fig.add_trace(go.Scatter(
                name="Total Planned Demand",
                x=df["week"],
                y=df["total_planned"],
                mode="lines+markers",
                line=dict(color="#E05C5C", width=3),
                marker=dict(size=8),
            ))
            fig.update_layout(
                barmode="stack",
                title="Weekly Capacity vs Demand",
                xaxis_title="Week",
                yaxis_title="Hours",
                legend=dict(orientation="h"),
                height=450,
            )
            # Color background of deficit weeks
            for _, row in df[df["deficit"] < 0].iterrows():
                fig.add_vrect(
                    x0=row["week"], x1=row["week"],
                    fillcolor="red", opacity=0.08,
                    layer="below", line_width=0,
                )
            st.plotly_chart(fig, use_container_width=True)

            # Deficit bar chart
            df["deficit_color"] = df["deficit"].apply(lambda x: "Deficit" if x < 0 else "Surplus")
            fig2 = px.bar(
                df,
                x="week",
                y="deficit",
                color="deficit_color",
                color_discrete_map={"Deficit": "#E05C5C", "Surplus": "#7BC8A4"},
                title="Weekly Surplus / Deficit",
                labels={"deficit": "Hours", "week": "Week", "deficit_color": ""},
            )
            fig2.add_hline(y=0, line_color="black", line_width=1.5)
            st.plotly_chart(fig2, use_container_width=True)

            # Data table
            st.markdown("### Weekly Capacity Data")
            display_df = df.copy()
            display_df["status"] = display_df["deficit"].apply(lambda x: "🔴 Deficit" if x < 0 else "🟢 Surplus")
            st.dataframe(
                display_df[["week", "own_hours", "hired_hours", "overtime_hours", "total_capacity", "total_planned", "deficit", "status"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.warning("No data found. Have you run seed_graph.py?")

    except Exception as e:
        st.error(f"Database error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Worker Coverage
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👷 Worker Coverage":
    st.title("👷 Worker Coverage")
    st.markdown("Which workers cover which stations — and which stations are single points of failure.")

    try:
        rows = run_query("""
            MATCH (w:Worker)-[r:WORKS_AT|CAN_COVER]->(s:Station)
            RETURN
                w.name AS worker,
                w.role AS role,
                w.type AS worker_type,
                type(r) AS relationship,
                s.code AS station_code,
                s.name AS station_name
            ORDER BY s.code, w.name
        """)

        if rows:
            df = pd.DataFrame(rows)

            # Single-point-of-failure stations (only 1 CAN_COVER worker)
            spof_query = run_query("""
                MATCH (s:Station)
                OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
                WITH s, count(w) AS coverage_count
                WHERE coverage_count <= 1
                RETURN s.code AS station_code, s.name AS station_name, coverage_count
                ORDER BY coverage_count
            """)

            spof_df = pd.DataFrame(spof_query) if spof_query else pd.DataFrame()

            col1, col2 = st.columns(2)
            col1.metric("Total Workers", df["worker"].nunique())
            col2.metric("⚠️ Single-Point-of-Failure Stations", len(spof_df) if not spof_df.empty else 0)

            if not spof_df.empty:
                st.warning(f"**Single-point-of-failure stations** (only 1 or 0 certified workers): {', '.join(spof_df['station_name'].tolist())}")

            st.markdown("---")

            # Coverage matrix
            all_stations = sorted(df["station_code"].unique())
            all_workers  = sorted(df["worker"].unique())

            # Build matrix
            matrix_data = {}
            for worker in all_workers:
                matrix_data[worker] = {}
                for station in all_stations:
                    primary = df[(df["worker"] == worker) & (df["station_code"] == station) & (df["relationship"] == "WORKS_AT")]
                    cover   = df[(df["worker"] == worker) & (df["station_code"] == station) & (df["relationship"] == "CAN_COVER")]
                    if not primary.empty:
                        matrix_data[worker][station] = "PRIMARY"
                    elif not cover.empty:
                        matrix_data[worker][station] = "COVER"
                    else:
                        matrix_data[worker][station] = ""

            matrix_df = pd.DataFrame(matrix_data).T
            matrix_df.index.name = "Worker"

            # Colour-coded display
            def color_cell(val):
                if val == "PRIMARY":
                    return "background-color: #4A90D9; color: white; font-weight: bold"
                elif val == "COVER":
                    return "background-color: #7BC8A4; color: black"
                return ""

            st.markdown("### Coverage Matrix  (🔵 Primary | 🟢 Can Cover)")
            styled = matrix_df.style.map(color_cell)
            st.dataframe(styled, use_container_width=True)

            # Worker details table
            st.markdown("---")
            st.markdown("### Worker Details")
            worker_details = run_query("""
                MATCH (w:Worker)
                OPTIONAL MATCH (w)-[:WORKS_AT]->(s:Station)
                RETURN w.id AS id, w.name AS name, w.role AS role,
                       w.type AS type, w.hours_per_week AS hours_per_week,
                       w.certifications AS certifications,
                       s.name AS primary_station
                ORDER BY w.id
            """)
            if worker_details:
                st.dataframe(pd.DataFrame(worker_details), use_container_width=True, hide_index=True)
        else:
            st.warning("No data found. Have you run seed_graph.py?")

    except Exception as e:
        st.error(f"Database error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: Self-Test
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧪 Self-Test":
    st.title("🧪 Self-Test")
    st.markdown("Automated checks against the live Neo4j graph. Click **Run Tests** to start.")
    st.markdown("---")

    def run_self_test(driver):
        checks = []

        # CHECK 1: Connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except Exception as e:
            checks.append((f"Neo4j connected — FAILED: {e}", False, 3))
            return checks  # Can't continue

        with driver.session() as s:
            # CHECK 2: Node count >= 50
            result = s.run("MATCH (n) RETURN count(n) AS c").single()
            count = result["c"]
            checks.append((f"{count} nodes (min: 50)", count >= 50, 3))

            # CHECK 3: Relationship count >= 100
            result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationships (min: 100)", count >= 100, 3))

            # CHECK 4: Node labels >= 6
            result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
            count = result["c"]
            checks.append((f"{count} node labels (min: 6)", count >= 6, 3))

            # CHECK 5: Relationship types >= 8
            result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
            count = result["c"]
            checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))

            # CHECK 6: Variance query returns results
            result = s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))

        return checks

    if st.button("▶️ Run Self-Test", type="primary"):
        driver = get_driver()
        with st.spinner("Running checks..."):
            try:
                checks = run_self_test(driver)
                total_score = 0
                max_score   = sum(c[2] for c in checks)

                st.markdown("### Results")
                for label, passed, pts in checks:
                    if passed:
                        st.success(f"✅  {label}  **{pts}/{pts}**")
                        total_score += pts
                    else:
                        st.error(f"❌  {label}  **0/{pts}**")

                st.markdown("---")
                pct = round(total_score / max_score * 100)
                if total_score == max_score:
                    st.balloons()
                    st.success(f"## 🎉 SELF-TEST SCORE: {total_score}/{max_score}  ({pct}%)")
                else:
                    st.warning(f"## SELF-TEST SCORE: {total_score}/{max_score}  ({pct}%)")

                # Show variance details
                if checks[-1][1]:  # Variance check passed
                    st.markdown("### Projects with >10% Variance (from graph)")
                    var_rows = run_query("""
                        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                        WHERE r.actual_hours > r.planned_hours * 1.1
                        RETURN
                            p.name AS project,
                            s.name AS station,
                            r.week AS week,
                            r.planned_hours AS planned,
                            r.actual_hours AS actual,
                            round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1) AS variance_pct
                        ORDER BY variance_pct DESC
                    """)
                    if var_rows:
                        st.dataframe(pd.DataFrame(var_rows), use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Test failed: {e}")
    else:
        st.info("Click **Run Self-Test** to validate the graph.")
        st.markdown("""
        **Checks performed:**
        1. Neo4j connection alive (3 pts)
        2. Node count ≥ 50 (3 pts)
        3. Relationship count ≥ 100 (3 pts)
        4. 6+ distinct node labels (3 pts)
        5. 8+ distinct relationship types (3 pts)
        6. Variance query returns results (5 pts)

        **Max score: 20/20**
        """)
