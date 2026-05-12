"""
app.py — Streamlit dashboard for the Swedish steel factory knowledge graph.

Run:
    streamlit run app.py

Requires .env with:
    NEO4J_URI=bolt://...
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=...
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

import queries

# ── config ─────────────────────────────────────────────────────────────────────
load_dotenv()

NEO4J_URI      = st.secrets.get("NEO4J_URI",      os.getenv("NEO4J_URI",      "bolt://localhost:7687"))
NEO4J_USER     = st.secrets.get("NEO4J_USER",     os.getenv("NEO4J_USER",     "neo4j"))
NEO4J_PASSWORD = st.secrets.get("NEO4J_PASSWORD", os.getenv("NEO4J_PASSWORD", "password"))

st.set_page_config(
    page_title="Factory Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── driver (cached) ────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Connecting to Neo4j…")
def get_driver():
    return queries.get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


driver = get_driver()

# ── sidebar navigation ─────────────────────────────────────────────────────────

PAGES = [
    "🏗️  Project Overview",
    "⚙️  Station Load",
    "📊  Capacity Tracker",
    "👷  Worker Coverage",
    "✅  Self-Test",
]

st.sidebar.title("🏭 Factory Dashboard")
st.sidebar.caption("Swedish Steel Fabrication")
page = st.sidebar.radio("Navigation", PAGES, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(f"Neo4j: `{NEO4J_URI}`")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Project Overview
# ══════════════════════════════════════════════════════════════════════════════

if page == PAGES[0]:
    st.title("🏗️ Project Overview")
    st.caption("All 8 projects — total planned vs actual hours and variance")

    rows = queries.get_all_projects(driver)
    if not rows:
        st.error("No project data found. Have you run seed_graph.py?")
        st.stop()

    df = pd.DataFrame(rows)
    df["products_str"] = df["products"].apply(lambda x: ", ".join(sorted(x)))

    # KPI strip
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Projects", len(df))
    col2.metric("Total Planned Hours", f"{df['total_planned'].sum():,.0f}")
    col3.metric("Total Actual Hours",  f"{df['total_actual'].sum():,.0f}")
    over = (df["variance_pct"] > 0).sum()
    col4.metric("Projects Over Budget", f"{over} / {len(df)}")

    st.divider()

    # Summary table
    display = df[["project_id","project_name","project_number",
                  "total_planned","total_actual","variance_pct","products_str"]].copy()
    display.columns = ["ID","Name","Number","Planned h","Actual h","Variance %","Products"]

    def style_variance(val):
        if val > 10:
            return "background-color:#ffd6d6; color:#c00"
        elif val > 0:
            return "background-color:#fff3cd"
        else:
            return "background-color:#d6ffd6"

    styled = display.style.map(style_variance, subset=["Variance %"]) \
                          .format({"Planned h": "{:.1f}", "Actual h": "{:.1f}",
                                   "Variance %": "{:+.1f}%"})
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()

    # Grouped bar chart – planned vs actual per project
    st.subheader("Planned vs Actual Hours by Project")
    fig = go.Figure()
    fig.add_bar(name="Planned", x=df["project_name"], y=df["total_planned"],
                marker_color="#4C72B0")
    fig.add_bar(name="Actual",  x=df["project_name"], y=df["total_actual"],
                marker_color="#DD8452")
    fig.update_layout(barmode="group", xaxis_tickangle=-30,
                      height=380, margin=dict(t=20, b=80))
    st.plotly_chart(fig, use_container_width=True)

    # Weekly breakdown
    st.subheader("Weekly Hours per Project")
    wdf_rows = queries.get_project_week_breakdown(driver)
    wdf = pd.DataFrame(wdf_rows)
    fig2 = px.line(wdf, x="week", y="planned_hours", color="project_name",
                   markers=True, title="Planned Hours per Week",
                   labels={"planned_hours": "Planned Hours", "week": "Week"})
    fig2.update_layout(height=340)
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Station Load
# ══════════════════════════════════════════════════════════════════════════════

elif page == PAGES[1]:
    st.title("⚙️ Station Load")
    st.caption("Hours per station across weeks — red bars indicate actual > planned")

    load_rows = queries.get_station_load(driver)
    if not load_rows:
        st.warning("No station load data found.")
        st.stop()

    df = pd.DataFrame(load_rows)

    # Heatmap: station × week (actual hours)
    st.subheader("Actual Hours Heatmap (Station × Week)")
    pivot = df.pivot_table(index="station_name", columns="week",
                           values="actual_hours", aggfunc="sum").fillna(0)
    fig = px.imshow(pivot, color_continuous_scale="RdYlGn_r",
                    labels=dict(color="Actual h"),
                    aspect="auto", height=400)
    fig.update_layout(margin=dict(t=20, l=160))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Grouped bar per station per week
    st.subheader("Planned vs Actual per Station per Week")
    station_options = sorted(df["station_name"].unique())
    selected = st.multiselect("Filter stations", station_options,
                              default=station_options[:5])
    filtered = df[df["station_name"].isin(selected)]

    fig2 = go.Figure()
    for week in sorted(filtered["week"].unique()):
        sub = filtered[filtered["week"] == week]
        fig2.add_bar(name=f"{week} Planned", x=sub["station_name"],
                     y=sub["planned_hours"], opacity=0.6)
        fig2.add_bar(name=f"{week} Actual",  x=sub["station_name"],
                     y=sub["actual_hours"])
    fig2.update_layout(barmode="group", height=400, xaxis_tickangle=-30)
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Overloaded table
    st.subheader("⚠️ Overloaded Station-Weeks (Actual > Planned)")
    overloaded = df[df["overloaded"] == True][
        ["station_code","station_name","week","planned_hours","actual_hours"]].copy()
    overloaded["excess_h"] = overloaded["actual_hours"] - overloaded["planned_hours"]
    overloaded.columns = ["Code","Station","Week","Planned h","Actual h","Excess h"]
    if overloaded.empty:
        st.success("No overloaded station-weeks found.")
    else:
        st.dataframe(overloaded.style.highlight_max(subset=["Excess h"], color="#ffd6d6"),
                     use_container_width=True, hide_index=True)

    # Station totals
    st.divider()
    st.subheader("Station Totals (All Weeks)")
    tot_rows = queries.get_station_totals(driver)
    tot_df = pd.DataFrame(tot_rows)
    fig3 = px.bar(tot_df, x="station_name", y=["total_planned","total_actual"],
                  barmode="group", labels={"value":"Hours","variable":"Type"},
                  color_discrete_sequence=["#4C72B0","#DD8452"])
    fig3.update_layout(xaxis_tickangle=-30, height=360)
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Capacity Tracker
# ══════════════════════════════════════════════════════════════════════════════

elif page == PAGES[2]:
    st.title("📊 Capacity Tracker")
    st.caption("Weekly workforce capacity vs planned demand — deficit weeks highlighted in red")

    cap_rows = queries.get_weekly_capacity(driver)
    if not cap_rows:
        st.warning("No capacity data found.")
        st.stop()

    df = pd.DataFrame(cap_rows)

    # KPIs
    deficit_weeks = (df["deficit"] < 0).sum()
    total_deficit = df[df["deficit"] < 0]["deficit"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Weeks",    len(df))
    c2.metric("Deficit Weeks",  deficit_weeks, delta=f"{deficit_weeks} at risk",
              delta_color="inverse")
    c3.metric("Worst Deficit",  f"{df['deficit'].min():+,} h")
    c4.metric("Cumulative Gap", f"{total_deficit:+,} h")

    st.divider()

    # Stacked bar: own + hired + overtime vs planned demand line
    st.subheader("Weekly Capacity vs Demand")
    fig = go.Figure()
    fig.add_bar(name="Own Hours",      x=df["week"], y=df["own_hours"],
                marker_color="#4C72B0")
    fig.add_bar(name="Hired Hours",    x=df["week"], y=df["hired_hours"],
                marker_color="#55A868")
    fig.add_bar(name="Overtime Hours", x=df["week"], y=df["overtime_hours"],
                marker_color="#C44E52")
    fig.add_trace(go.Scatter(
        name="Total Planned Demand",
        x=df["week"], y=df["total_planned"],
        mode="lines+markers",
        line=dict(color="black", width=2, dash="dash"),
        marker=dict(size=8)
    ))
    fig.update_layout(barmode="stack", height=420,
                      yaxis_title="Hours",
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Deficit waterfall
    st.subheader("Weekly Deficit / Surplus")
    colors = ["#c00" if d < 0 else "#2a9d2a" for d in df["deficit"]]
    fig2 = go.Figure(go.Bar(
        x=df["week"], y=df["deficit"],
        marker_color=colors,
        text=[f"{d:+,}" for d in df["deficit"]],
        textposition="outside"
    ))
    fig2.add_hline(y=0, line_width=1.5, line_dash="solid", line_color="black")
    fig2.update_layout(height=320, yaxis_title="Deficit / Surplus (hours)")
    st.plotly_chart(fig2, use_container_width=True)

    # Detail table
    st.divider()
    st.subheader("Weekly Capacity Detail")
    display = df[["week","own_staff","hired_staff","own_hours",
                  "hired_hours","overtime_hours","total_capacity",
                  "total_planned","deficit"]].copy()
    display.columns = ["Week","Own Staff","Hired","Own h","Hired h",
                        "OT h","Capacity","Planned","Deficit"]

    def colour_deficit(val):
        return "color: #c00; font-weight:bold" if val < 0 else "color: #2a9d2a"

    st.dataframe(
        display.style.map(colour_deficit, subset=["Deficit"]),
        use_container_width=True, hide_index=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Worker Coverage
# ══════════════════════════════════════════════════════════════════════════════

elif page == PAGES[3]:
    st.title("👷 Worker Coverage")
    st.caption("Which workers can cover which stations — single-point-of-failure stations highlighted")

    cov_rows = queries.get_worker_coverage_matrix(driver)
    spof_rows = queries.get_single_point_of_failure_stations(driver)
    workers_rows = queries.get_all_workers(driver)
    station_count_rows = queries.get_station_worker_count(driver)

    if not cov_rows:
        st.warning("No coverage data found.")
        st.stop()

    cov_df = pd.DataFrame(cov_rows)
    workers_df = pd.DataFrame(workers_rows)
    sc_df = pd.DataFrame(station_count_rows)

    # KPIs
    spof_count = len(spof_rows)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Workers", len(workers_df))
    c2.metric("Total Stations", cov_df["station_code"].nunique())
    c3.metric("⚠️ Single-Point-of-Failure Stations", spof_count,
              delta="risk" if spof_count else "none", delta_color="inverse")

    st.divider()

    # Coverage matrix (pivot)
    st.subheader("Coverage Matrix (Worker × Station)")
    pivot = cov_df.pivot_table(index="name", columns="station_name",
                                values="station_code", aggfunc="count").fillna(0)
    pivot = pivot.astype(int)

    # Build colour map: SPOF stations → orange
    spof_station_names = {r["station_name"] for r in spof_rows}
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, "#f5f5f5"], [1, "#2196F3"]],
        showscale=False,
        text=pivot.values,
        texttemplate="%{text}",
    ))
    # Highlight SPOF columns
    for i, col in enumerate(pivot.columns):
        if col in spof_station_names:
            fig.add_vrect(x0=i - 0.5, x1=i + 0.5,
                          fillcolor="orange", opacity=0.15, line_width=0)
    fig.update_layout(
        height=420,
        xaxis_tickangle=-35,
        margin=dict(l=150, b=120),
        annotations=[dict(
            x=0.5, y=-0.22, xref="paper", yref="paper",
            text="<b>Orange columns = single-point-of-failure stations</b>",
            showarrow=False, font=dict(color="darkorange")
        )]
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # SPOF detail
    if spof_rows:
        st.subheader("⚠️ Single-Point-of-Failure Stations")
        spof_df = pd.DataFrame(spof_rows)[["station_code","station_name","sole_worker"]]
        spof_df.columns = ["Code","Station","Sole Worker"]
        st.dataframe(spof_df.style.map(lambda _: "background:#fff3cd"),
                     use_container_width=True, hide_index=True)
    else:
        st.success("✅ No single-point-of-failure stations found.")

    st.divider()

    # Worker table
    st.subheader("Worker Directory")
    wd = workers_df[["worker_id","name","role","type","hours_per_week","certifications"]].copy()
    wd.columns = ["ID","Name","Role","Type","h/week","Certifications"]
    st.dataframe(wd, use_container_width=True, hide_index=True)

    # Station coverage bar
    st.divider()
    st.subheader("Number of Workers per Station")
    fig2 = px.bar(sc_df, x="station_name", y="worker_count",
                  color="worker_count",
                  color_continuous_scale=["red","orange","green"],
                  labels={"worker_count":"Workers","station_name":"Station"})
    fig2.add_hline(y=1.5, line_dash="dot", line_color="red",
                   annotation_text="SPOF threshold")
    fig2.update_layout(xaxis_tickangle=-30, height=360, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Self-Test
# ══════════════════════════════════════════════════════════════════════════════

elif page == PAGES[4]:
    st.title("✅ Self-Test")
    st.caption("Automated checks against the live Neo4j graph")

    if st.button("▶  Run Self-Test", type="primary", use_container_width=True):
        with st.spinner("Running checks…"):
            checks, earned, possible = queries.run_all_checks(driver)

        st.divider()

        for chk in checks:
            icon = "✅" if chk["ok"] else "❌"
            pts_label = f"{chk['pts']}/{chk['pts']}" if chk["ok"] else f"0/{chk['pts']}"
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(f"{icon} **{chk['label']}** — `{chk['msg']}`")
            col_b.markdown(f"**{pts_label} pts**")

            # Show variance detail table for CHECK 6
            if "detail" in chk and chk["detail"]:
                detail_df = pd.DataFrame(chk["detail"])
                detail_df.columns = ["Project ID", "Project Name", "Variance %"]
                st.dataframe(detail_df, use_container_width=True, hide_index=True)

        st.divider()

        # Score bar
        pct = int(earned / possible * 100)
        colour = "green" if pct >= 80 else "orange" if pct >= 50 else "red"
        st.markdown(
            f"""
            <div style="background:#f0f0f0;border-radius:8px;padding:20px;text-align:center">
              <h2 style="color:{colour};margin:0">
                {earned} / {possible} pts &nbsp;·&nbsp; {pct}%
              </h2>
              <p style="margin:4px 0 0 0;color:#555">Self-Test Score</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if earned == possible:
            st.balloons()
    else:
        st.info("Click **Run Self-Test** to execute all checks against your Neo4j instance.")

        # Schema preview
        st.divider()
        st.subheader("Graph Schema Reference")
        schema_md = """
| Node Label | Source | Description |
|---|---|---|
| `Project` | production.csv | 8 construction projects |
| `Product` | production.csv | 7 product types (IQB, SB, …) |
| `Station` | production.csv | 9+ production stations |
| `Worker` | workers.csv | 14 workers |
| `Week` | capacity.csv | 8 planning weeks |
| `Etapp` | production.csv | ET1, ET2 |
| `BOP` | production.csv | BOP1, BOP2, BOP3 |

| Relationship | Description |
|---|---|
| `PRODUCES` | Project → Product |
| `SCHEDULED_AT` | Project → Station (per week) |
| `WORKS_AT` | Worker → Station |
| `CAN_COVER` | Worker → Station |
| `IN_ETAPP` | Project → Etapp |
| `IN_BOP` | Project → BOP |
| `HAS_CAPACITY` | Week → Week (self-loop with capacity props) |
| `HAS_SCHEDULE` | Week → Station (aggregated hours) |
"""
        st.markdown(schema_md)