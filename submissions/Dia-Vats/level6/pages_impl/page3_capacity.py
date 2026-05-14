"""Page 3 — Capacity Tracker"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query


def render():
    st.markdown('<div class="page-title">Capacity Tracker</div>', unsafe_allow_html=True)
    st.markdown("Weekly factory capacity vs planned demand. Red bars = deficit weeks.")

    rows = run_query("""
        MATCH (wk:Week)-[:HAS_CAPACITY]->(cs:CapacitySnapshot)
        RETURN
            wk.week_id          AS week_id,
            cs.total_capacity   AS total_capacity,
            cs.total_planned    AS total_planned,
            cs.deficit          AS deficit,
            cs.overtime_hours   AS overtime_hours,
            cs.own_staff_count  AS own_staff,
            cs.hired_staff_count AS hired_staff
        ORDER BY wk.week_id
    """)

    if not rows:
        st.error("No data returned. Run seed_graph.py first.")
        return

    df = pd.DataFrame(rows)
    week_order = ["w1","w2","w3","w4","w5","w6","w7","w8"]
    df["week_id"] = pd.Categorical(df["week_id"], categories=week_order, ordered=True)
    df = df.sort_values("week_id")

    deficit_weeks = int((df["deficit"] < 0).sum())
    total_weeks   = len(df)

    # ── KPI cards ─────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="label">Deficit Weeks</div><div class="value" style="color:#f87171">{deficit_weeks} of {total_weeks}</div></div>', unsafe_allow_html=True)
    with col2:
        total_def = int(df[df["deficit"] < 0]["deficit"].sum())
        st.markdown(f'<div class="metric-card"><div class="label">Total Deficit hrs</div><div class="value" style="color:#f87171">{total_def}</div></div>', unsafe_allow_html=True)
    with col3:
        ot = int(df["overtime_hours"].sum())
        st.markdown(f'<div class="metric-card"><div class="label">Total Overtime hrs</div><div class="value" style="color:#fbbf24">{ot}</div></div>', unsafe_allow_html=True)

    # Insight text
    st.warning(f"**{deficit_weeks} of {total_weeks} weeks are in deficit** — factory demand exceeds available capacity in {deficit_weeks} out of {total_weeks} weeks. Consider scheduling overtime or additional hired staff.")

    st.markdown("---")

    # ── Grouped bar chart ──────────────────────────────────────────────────────
    cap_colors  = ["#3b82f6"] * len(df)
    plan_colors = ["#ef4444" if d < 0 else "#f97316" for d in df["deficit"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Total Capacity", x=df["week_id"], y=df["total_capacity"],
        marker_color=cap_colors, opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Total Planned", x=df["week_id"], y=df["total_planned"],
        marker_color=plan_colors, opacity=0.9,
    ))
    fig.add_trace(go.Scatter(
        name="Deficit / Surplus", x=df["week_id"], y=df["deficit"],
        mode="lines+markers",
        line=dict(color="#a855f7", width=2, dash="dot"),
        marker=dict(size=8, color=["#ef4444" if d < 0 else "#4ade80" for d in df["deficit"]]),
    ))
    fig.add_hline(y=0, line_color="#64748b", line_dash="dash")
    fig.update_layout(
        barmode="group", template="plotly_dark",
        title="Weekly Capacity vs Planned Demand",
        xaxis_title="Week", yaxis_title="Hours",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=440,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,17,23,0.6)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**WEEKLY BREAKDOWN**")
    display = df[["week_id","own_staff","hired_staff","total_capacity","total_planned","overtime_hours","deficit"]].copy()
    display.columns = ["Week","Own Staff","Hired Staff","Capacity hrs","Planned hrs","Overtime hrs","Deficit"]

    def color_deficit(val):
        if val < 0:
            return "background-color:#7f1d1d; color:#fca5a5; font-weight:700"
        return "color:#4ade80; font-weight:700"

    st.dataframe(
        display.style.applymap(color_deficit, subset=["Deficit"]),
        use_container_width=True, hide_index=True
    )
