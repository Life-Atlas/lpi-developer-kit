"""Page 2 — Station Load Heatmap"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query


def render():
    st.markdown('<div class="page-title">Station Load</div>', unsafe_allow_html=True)
    st.markdown("Heatmap of variance % by station × week. Red = overloaded (>10%), green = on track.")

    rows = run_query("""
        MATCH (wo:WorkOrder)-[:AT_STATION]->(s:Station)
        MATCH (wo)-[r:SCHEDULED_IN]->(wk:Week)
        RETURN
            s.station_code AS station_code,
            s.station_name AS station_name,
            wk.week_id     AS week_id,
            sum(r.planned_hours) AS planned,
            sum(r.actual_hours)  AS actual
        ORDER BY s.station_code, wk.week_id
    """)

    if not rows:
        st.error("No data returned. Run seed_graph.py first.")
        return

    df = pd.DataFrame(rows)
    df["variance_pct"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)
    df["label"] = df["station_code"] + "\n" + df["station_name"]

    # pivot for heatmap
    week_order = ["w1","w2","w3","w4","w5","w6","w7","w8"]
    pivot = df.pivot_table(index="label", columns="week_id", values="variance_pct", aggfunc="mean")
    pivot = pivot.reindex(columns=[w for w in week_order if w in pivot.columns])

    stations = list(pivot.index)
    weeks    = list(pivot.columns)
    z_vals   = pivot.values.tolist()

    # Custom text for hover
    hover_text = []
    for s_label in stations:
        row_texts = []
        for wk in weeks:
            try:
                v = pivot.loc[s_label, wk]
                row_texts.append(f"Station: {s_label}<br>Week: {wk}<br>Variance: {v:.1f}%")
            except Exception:
                row_texts.append("")
        hover_text.append(row_texts)

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=weeks,
        y=stations,
        text=pivot.values.tolist(),
        texttemplate="%{text:.1f}%",
        colorscale=[
            [0.0, "#166534"],
            [0.3, "#4ade80"],
            [0.5, "#facc15"],
            [0.7, "#f97316"],
            [1.0, "#991b1b"],
        ],
        zmid=0,
        zmin=-20, zmax=30,
        colorbar=dict(title="Variance %", ticksuffix="%"),
        hovertext=hover_text,
        hoverinfo="text",
    ))
    fig.update_layout(
        template="plotly_dark",
        title="Station Load Heatmap — Variance % (Actual vs Planned)",
        xaxis_title="Week", yaxis_title="Station",
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.8)",
        margin=dict(l=180, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**OVERLOADED CELLS — VARIANCE > 10%**")
    overloaded = df[df["variance_pct"] > 10][["station_code","station_name","week_id","planned","actual","variance_pct"]]
    overloaded.columns = ["Code","Station","Week","Planned hrs","Actual hrs","Variance %"]
    if len(overloaded):
        st.dataframe(
            overloaded.style.highlight_between(subset=["Variance %"], left=10, right=999,
                                                props="background-color:#7f1d1d;color:#fca5a5;font-weight:600"),
            use_container_width=True, hide_index=True
        )
    else:
        st.success("No overloaded cells found.")
