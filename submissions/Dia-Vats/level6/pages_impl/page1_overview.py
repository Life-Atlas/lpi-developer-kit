"""Page 1 — Project Overview"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query


def render():
    st.markdown('<div class="page-title">Project Overview</div>', unsafe_allow_html=True)
    st.markdown("Planned vs actual hours per project, variance analysis, and bottleneck summary.")

    rows = run_query("""
        MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)
        RETURN
            p.project_id   AS project_id,
            p.project_name AS project_name,
            sum(wo.planned_hours) AS total_planned,
            sum(wo.actual_hours)  AS total_actual,
            sum(CASE WHEN wo.is_bottleneck THEN 1 ELSE 0 END) AS bottleneck_count
        ORDER BY p.project_id
    """)

    if not rows:
        st.error("No data returned. Run seed_graph.py first.")
        return

    df = pd.DataFrame(rows)
    df["variance_pct"] = ((df["total_actual"] - df["total_planned"]) / df["total_planned"] * 100).round(1)

    # ── KPI cards ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="label">Total Projects</div><div class="value">{len(df)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="label">Total Planned hrs</div><div class="value">{int(df["total_planned"].sum()):,}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="label">Total Actual hrs</div><div class="value">{int(df["total_actual"].sum()):,}</div></div>', unsafe_allow_html=True)
    with col4:
        btn = int(df["bottleneck_count"].sum())
        st.markdown(f'<div class="metric-card"><div class="label">Bottleneck Work Orders</div><div class="value" style="color:#f87171">{btn}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Grouped bar chart ──────────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Planned hrs", x=df["project_name"], y=df["total_planned"],
        marker_color="#3b82f6", marker_line_color="#1d4ed8", marker_line_width=1,
    ))
    fig.add_trace(go.Bar(
        name="Actual hrs", x=df["project_name"], y=df["total_actual"],
        marker_color="#f97316", marker_line_color="#c2410c", marker_line_width=1,
    ))
    fig.update_layout(
        barmode="group", template="plotly_dark",
        title="Planned vs Actual Hours — All Projects",
        xaxis_title="Project", yaxis_title="Hours",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420, margin=dict(l=40, r=20, t=60, b=100),
        xaxis_tickangle=-30,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,17,23,0.6)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**PROJECT DETAIL TABLE**")

    # ── Variance table ─────────────────────────────────────────────────────────
    display_df = df[["project_id","project_name","total_planned","total_actual","variance_pct","bottleneck_count"]].copy()
    display_df.columns = ["ID","Project","Planned hrs","Actual hrs","Variance %","Bottlenecks"]

    def color_variance(val):
        if val > 10:
            return "background-color:#7f1d1d; color:#fca5a5; font-weight:600"
        elif val > 0:
            return "color:#fbbf24"
        return "color:#4ade80"

    styled = display_df.style.applymap(color_variance, subset=["Variance %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)
