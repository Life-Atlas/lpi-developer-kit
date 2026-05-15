"""
app.py — Streamlit dashboard for the Swedish steel factory knowledge graph.
All data comes from Neo4j queries.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ── Neo4j connection ──────────────────────────────────────────────────────────

@st.cache_resource
def get_driver():
    uri  = st.secrets.get("NEO4J_URI",      os.getenv("NEO4J_URI"))
    user = st.secrets.get("NEO4J_USER",     os.getenv("NEO4J_USER", "neo4j"))
    pwd  = st.secrets.get("NEO4J_PASSWORD", os.getenv("NEO4J_PASSWORD"))
    return GraphDatabase.driver(uri, auth=(user, pwd))

def run_query(query, params=None):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(r) for r in result]

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Factory Graph Dashboard",
    page_icon="🏭",
    layout="wide",
)

# ── Sidebar navigation ────────────────────────────────────────────────────────

st.sidebar.title("🏭 Factory Dashboard")
page = st.sidebar.radio(
    "Navigate",
    ["Project Overview", "Station Load", "Capacity Tracker", "Worker Coverage", "Self-Test"],
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: Project Overview
# ─────────────────────────────────────────────────────────────────────────────

if page == "Project Overview":
    st.title("📋 Project Overview")
    st.caption("All 8 projects — planned vs actual hours and product breakdown")

    rows = run_query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH p,
             sum(r.planned_hours) AS total_planned,
             sum(r.actual_hours)  AS total_actual
        RETURN p.name  AS project,
               p.id    AS pid,
               total_planned,
               total_actual,
               round((total_actual - total_planned) / total_planned * 100 * 10) / 10 AS variance_pct
        ORDER BY p.id
    """)
    df = pd.DataFrame(rows)

    # KPI row
    col1, col2, col3 = st.columns(3)
    col1.metric("Projects", len(df))
    col2.metric("Total planned hours", f"{int(df['total_planned'].sum()):,}")
    over = len(df[df['variance_pct'] > 10])
    col3.metric("Projects >10% over", over, delta=f"+{over}" if over else "0", delta_color="inverse")

    st.divider()

    # Variance bar chart
    colors = ["#e05252" if v > 10 else "#52b852" if v < 0 else "#f0a830"
              for v in df["variance_pct"]]
    fig = go.Figure(go.Bar(
        x=df["project"], y=df["variance_pct"],
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in df["variance_pct"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Variance % per project (actual vs planned hours)",
        yaxis_title="Variance %",
        xaxis_title="",
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
    )
    fig.add_hline(y=10,  line_dash="dot", line_color="red",  annotation_text="10% alert")
    fig.add_hline(y=0,   line_dash="solid", line_color="gray", line_width=0.5)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Detailed table")

    df_display = df.rename(columns={
        "project": "Project", "pid": "ID",
        "total_planned": "Planned h", "total_actual": "Actual h", "variance_pct": "Variance %"
    })
    df_display["Status"] = df_display["Variance %"].apply(
        lambda v: "🔴 Over" if v > 10 else ("🟢 Under" if v < 0 else "🟡 On track"))

    st.dataframe(
        df_display[["ID","Project","Planned h","Actual h","Variance %","Status"]],
        use_container_width=True, hide_index=True,
    )

    # Products per project
    st.subheader("Products per project")
    prod_rows = run_query("""
        MATCH (p:Project)-[:PRODUCES]->(pr:Product)
        RETURN p.name AS project, p.id AS pid, collect(pr.type) AS products
        ORDER BY pid
    """)
    prod_df = pd.DataFrame(prod_rows)
    prod_df["products"] = prod_df["products"].apply(lambda x: ", ".join(sorted(x)))
    st.dataframe(prod_df.rename(columns={"project":"Project","products":"Products"}),
                 use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: Station Load
# ─────────────────────────────────────────────────────────────────────────────

elif page == "Station Load":
    st.title("🏗️ Station Load")
    st.caption("Hours per station × week — red cells are over-planned")

    rows = run_query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.name AS station, r.week AS week,
               sum(r.planned_hours) AS planned,
               sum(r.actual_hours)  AS actual
        ORDER BY station, week
    """)
    df = pd.DataFrame(rows)

    week_order = ["w1","w2","w3","w4","w5","w6","w7","w8"]
    existing_weeks = sorted(df["week"].unique(), key=lambda w: week_order.index(w) if w in week_order else 99)

    view = st.radio("Show", ["Actual hours", "Planned hours", "Variance %"], horizontal=True)

    if view == "Actual hours":
        pivot = df.pivot_table(index="station", columns="week", values="actual", aggfunc="sum").reindex(columns=existing_weeks)
        color_scale = "YlOrRd"
        title = "Actual hours per station per week"
    elif view == "Planned hours":
        pivot = df.pivot_table(index="station", columns="week", values="planned", aggfunc="sum").reindex(columns=existing_weeks)
        color_scale = "Blues"
        title = "Planned hours per station per week"
    else:
        df["variance"] = (df["actual"] - df["planned"]) / df["planned"].replace(0, 1) * 100
        pivot = df.pivot_table(index="station", columns="week", values="variance", aggfunc="mean").reindex(columns=existing_weeks)
        color_scale = "RdYlGn_r"
        title = "Mean variance % per station per week"

    fig = px.imshow(
        pivot,
        color_continuous_scale=color_scale,
        title=title,
        labels=dict(color=view),
        aspect="auto",
        text_auto=".0f",
    )
    fig.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Station total actual vs planned")

    station_totals = run_query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.name AS station,
               sum(r.planned_hours) AS planned,
               sum(r.actual_hours)  AS actual
        ORDER BY actual DESC
    """)
    st_df = pd.DataFrame(station_totals)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Planned", x=st_df["station"], y=st_df["planned"],
                          marker_color="#5b8dee"))
    fig2.add_trace(go.Bar(name="Actual", x=st_df["station"], y=st_df["actual"],
                          marker_color="#e07a5f"))
    fig2.update_layout(
        barmode="group", height=380,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: Capacity Tracker
# ─────────────────────────────────────────────────────────────────────────────

elif page == "Capacity Tracker":
    st.title("📊 Capacity Tracker")
    st.caption("Weekly workforce capacity vs planned demand — red = deficit")

    rows = run_query("""
        MATCH (wk:Week)
        WHERE wk.total_capacity IS NOT NULL
        RETURN wk.name AS week,
               wk.own_hours AS own,
               wk.hired_hours AS hired,
               wk.overtime_hours AS overtime,
               wk.total_capacity AS capacity,
               wk.total_planned AS planned,
               wk.deficit AS deficit
        ORDER BY wk.name
    """)
    df = pd.DataFrame(rows)

    week_order = ["w1","w2","w3","w4","w5","w6","w7","w8"]
    df["week"] = pd.Categorical(df["week"], categories=week_order, ordered=True)
    df = df.sort_values("week")

    # KPI row
    deficit_weeks = df[df["deficit"] < 0]
    total_deficit = int(df[df["deficit"] < 0]["deficit"].sum())
    col1, col2, col3 = st.columns(3)
    col1.metric("Deficit weeks", len(deficit_weeks), delta=f"{len(deficit_weeks)}/8", delta_color="inverse")
    col2.metric("Total deficit hours", total_deficit, delta_color="inverse")
    col3.metric("Surplus weeks", len(df[df["deficit"] >= 0]))

    st.divider()

    # Capacity vs planned line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["week"], y=df["capacity"], name="Total capacity",
        line=dict(color="#4e9af1", width=2.5), mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=df["week"], y=df["planned"], name="Total planned",
        line=dict(color="#f06c6c", width=2.5), mode="lines+markers"
    ))
    # shade deficit areas
    for _, r in df.iterrows():
        if r["deficit"] < 0:
            fig.add_vrect(
                x0=str(r["week"]), x1=str(r["week"]),
                fillcolor="rgba(240,108,108,0.15)", layer="below", line_width=0
            )
    fig.update_layout(
        title="Capacity vs planned demand by week",
        height=380,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", title="Hours"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stacked bar: own + hired + overtime
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Own hours",      x=df["week"], y=df["own"],      marker_color="#5b8dee"))
    fig2.add_trace(go.Bar(name="Hired hours",    x=df["week"], y=df["hired"],    marker_color="#7ed3b2"))
    fig2.add_trace(go.Bar(name="Overtime hours", x=df["week"], y=df["overtime"], marker_color="#f0c05a"))
    fig2.add_trace(go.Scatter(
        name="Planned demand", x=df["week"], y=df["planned"],
        mode="lines+markers", line=dict(color="red", dash="dot", width=2),
    ))
    fig2.update_layout(
        barmode="stack", title="Capacity breakdown by week",
        height=380,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Weekly detail")
    df["Status"] = df["deficit"].apply(lambda d: "🔴 Deficit" if d < 0 else "🟢 Surplus")
    st.dataframe(
        df[["week","own","hired","overtime","capacity","planned","deficit","Status"]].rename(
            columns={"week":"Week","own":"Own h","hired":"Hired h","overtime":"Overtime h",
                     "capacity":"Total cap","planned":"Planned","deficit":"Deficit"}),
        use_container_width=True, hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: Worker Coverage
# ─────────────────────────────────────────────────────────────────────────────

elif page == "Worker Coverage":
    st.title("👷 Worker Coverage")
    st.caption("Which workers cover which stations — red = single point of failure")

    # Coverage matrix
    rows = run_query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN w.name AS worker, w.role AS role,
               collect(s.code) AS stations
        ORDER BY w.id
    """)
    workers_df = pd.DataFrame(rows)

    station_rows = run_query("MATCH (s:Station) RETURN s.code AS code, s.name AS name ORDER BY s.code")
    all_stations = [r["code"] for r in station_rows]
    station_names = {r["code"]: r["name"] for r in station_rows}

    # Build matrix
    matrix = {}
    for _, row in workers_df.iterrows():
        matrix[row["worker"]] = {s: ("✓" if s in row["stations"] else "") for s in all_stations}
    matrix_df = pd.DataFrame(matrix).T
    matrix_df.columns = [f"{c} {station_names.get(c,'')}" for c in matrix_df.columns]

    # Single-point-of-failure stations
    spof_rows = run_query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        WITH s, count(w) AS worker_count
        WHERE worker_count = 1
        MATCH (w2:Worker)-[:CAN_COVER]->(s)
        RETURN s.code AS code, s.name AS name, w2.name AS only_worker
    """)
    spof_df = pd.DataFrame(spof_rows)

    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader("Coverage matrix")
        st.dataframe(matrix_df, use_container_width=True)

    with col2:
        st.subheader("⚠️ Single-point-of-failure stations")
        if not spof_df.empty:
            for _, r in spof_df.iterrows():
                st.error(f"**{r['code']} {r['name']}**\nOnly covered by: {r['only_worker']}")
        else:
            st.success("No single-point-of-failure stations")

    st.divider()
    st.subheader("Workers per station (coverage count)")

    count_rows = run_query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN s.code + ' ' + s.name AS station, count(w) AS workers
        ORDER BY workers ASC
    """)
    count_df = pd.DataFrame(count_rows)
    colors = ["#e05252" if c == 1 else "#f0a830" if c == 2 else "#52b852"
              for c in count_df["workers"]]
    fig = go.Figure(go.Bar(
        x=count_df["station"], y=count_df["workers"],
        marker_color=colors,
        text=count_df["workers"], textposition="outside",
    ))
    fig.update_layout(
        height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", title="Workers who can cover"),
        xaxis_title="",
    )
    fig.add_hline(y=1, line_dash="dot", line_color="red", annotation_text="SPOF threshold")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Worker details")
    detail_rows = run_query("""
        MATCH (w:Worker)
        OPTIONAL MATCH (w)-[:WORKS_AT]->(ps:Station)
        RETURN w.id AS id, w.name AS name, w.role AS role,
               w.certifications AS certs,
               w.hours_per_week AS hours,
               w.type AS type,
               ps.name AS primary_station
        ORDER BY w.id
    """)
    st.dataframe(
        pd.DataFrame(detail_rows).rename(columns={
            "id":"ID","name":"Name","role":"Role","certs":"Certifications",
            "hours":"Hours/week","type":"Type","primary_station":"Primary Station"
        }),
        use_container_width=True, hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: Self-Test
# ─────────────────────────────────────────────────────────────────────────────

elif page == "Self-Test":
    st.title("🧪 Self-Test")
    st.caption("Automated checks — verifies the graph meets all L6 requirements")

    def run_self_test(driver):
        checks = []

        # Check 1: Connection
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except Exception as e:
            checks.append((f"Neo4j connection FAILED: {e}", False, 3))
            return checks  # can't continue

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
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)
            rows = [dict(r) for r in result]
            checks.append((f"Variance query: {len(rows)} results found", len(rows) > 0, 5))

        return checks

    if st.button("▶ Run self-test", type="primary"):
        with st.spinner("Running checks..."):
            try:
                driver = get_driver()
                results = run_self_test(driver)

                total_score = 0
                total_max   = sum(pts for _, _, pts in results)

                st.divider()
                for label, passed, pts in results:
                    icon = "✅" if passed else "❌"
                    score_str = f"{pts}/{pts}" if passed else f"0/{pts}"
                    col1, col2 = st.columns([6,1])
                    col1.markdown(f"{icon} {label}")
                    col2.markdown(f"**{score_str}**")
                    if passed:
                        total_score += pts

                st.divider()
                pct = int(total_score / total_max * 100)
                if total_score == total_max:
                    st.success(f"### 🎉 SELF-TEST SCORE: {total_score}/{total_max} — Perfect!")
                elif total_score >= 14:
                    st.warning(f"### SELF-TEST SCORE: {total_score}/{total_max} ({pct}%)")
                else:
                    st.error(f"### SELF-TEST SCORE: {total_score}/{total_max} ({pct}%)")

                # Show variance results table if check 6 passed
                if results[-1][1]:
                    with st.expander("Variance query results (projects >10% over)"):
                        driver2 = get_driver()
                        with driver2.session() as s:
                            r = s.run("""
                                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                                WHERE r.actual_hours > r.planned_hours * 1.1
                                RETURN p.name AS project, s.name AS station,
                                       r.week AS week,
                                       r.planned_hours AS planned,
                                       r.actual_hours AS actual,
                                       round((r.actual_hours - r.planned_hours)
                                             / r.planned_hours * 100 * 10) / 10 AS variance_pct
                                ORDER BY variance_pct DESC
                            """)
                            st.dataframe(pd.DataFrame([dict(row) for row in r]),
                                        use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Could not connect to Neo4j: {e}")
                st.info("Check your .env file or Streamlit secrets — NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
    else:
        st.info("Click **Run self-test** to verify your graph meets all L6 requirements.")
        st.markdown("""
        **Checks:**
        - ✅ Neo4j connection alive **(3 pts)**
        - ✅ Node count ≥ 50 **(3 pts)**
        - ✅ Relationship count ≥ 100 **(3 pts)**
        - ✅ 6+ distinct node labels **(3 pts)**
        - ✅ 8+ distinct relationship types **(3 pts)**
        - ✅ Variance query returns results **(5 pts)**
        """)
