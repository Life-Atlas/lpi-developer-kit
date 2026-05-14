"""Page 6 — Forecast (Bonus C)"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query

WEEK_NUM = {"w1":1,"w2":2,"w3":3,"w4":4,"w5":5,"w6":6,"w7":7,"w8":8}


def render():
    st.markdown('<div class="page-title">Forecast</div>', unsafe_allow_html=True)
    st.markdown("Linear trend extrapolation per station from weeks w1–w8, predicting week 9 load.")

    rows = run_query("""
        MATCH (wo:WorkOrder)-[:AT_STATION]->(s:Station)
        MATCH (wo)-[r:SCHEDULED_IN]->(wk:Week)
        RETURN
            s.station_code AS station_code,
            s.station_name AS station_name,
            wk.week_id     AS week_id,
            sum(r.actual_hours) AS actual_hours
        ORDER BY s.station_code, wk.week_id
    """)

    if not rows:
        st.error("No data returned. Run seed_graph.py first.")
        return

    df = pd.DataFrame(rows)
    df["week_num"] = df["week_id"].map(WEEK_NUM)
    df = df.dropna(subset=["week_num"])

    stations = sorted(df["station_code"].unique())
    sel = st.multiselect("Select stations to display", stations, default=stations[:5])
    if not sel:
        st.warning("Select at least one station.")
        return

    fig = go.Figure()
    predictions = []

    colors_palette = [
        "#3b82f6","#f97316","#a855f7","#22c55e","#f43f5e",
        "#06b6d4","#eab308","#6366f1","#14b8a6","#ec4899",
    ]

    for i, sc in enumerate(sel):
        sub = df[df["station_code"] == sc].sort_values("week_num")
        if len(sub) < 2:
            continue
        station_name = sub["station_name"].iloc[0]
        color = colors_palette[i % len(colors_palette)]

        x = sub["week_num"].values
        y = sub["actual_hours"].values

        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        trend_fn = np.poly1d(coeffs)
        pred_w9 = float(trend_fn(9))

        # Trend line over w1–w9
        x_trend = np.linspace(1, 9, 50)
        y_trend = trend_fn(x_trend)

        # Actual data points
        fig.add_trace(go.Scatter(
            x=sub["week_id"], y=y,
            mode="lines+markers",
            name=f"{sc} actual",
            line=dict(color=color, width=2),
            marker=dict(size=7),
            legendgroup=sc,
        ))

        # Week labels for trend x-axis (w1..w9)
        week_labels = [f"w{int(n)}" for n in np.round(x_trend)]

        # Trend line
        fig.add_trace(go.Scatter(
            x=week_labels, y=y_trend,
            mode="lines",
            name=f"{sc} trend",
            line=dict(color=color, width=1.5, dash="dot"),
            opacity=0.5,
            legendgroup=sc,
            showlegend=False,
        ))

        # Week-9 predicted point
        fig.add_trace(go.Scatter(
            x=["w9"], y=[pred_w9],
            mode="markers",
            name=f"{sc} w9 forecast",
            marker=dict(size=14, color=color, symbol="star",
                        line=dict(color="#fff", width=2)),
            legendgroup=sc,
            showlegend=True,
        ))

        predictions.append({
            "Station Code": sc,
            "Station": station_name,
            "Trend (slope)": f"{slope:+.2f} hrs/wk",
            "Week 8 Actual": f"{y[-1]:.1f} hrs",
            "Week 9 Forecast": f"{max(0, pred_w9):.1f} hrs",
            "Risk": "High" if pred_w9 > 60 else ("Medium" if pred_w9 > 30 else "Low"),
        })

    fig.update_layout(
        template="plotly_dark",
        title="Station Load Forecast — Linear Extrapolation to Week 9",
        xaxis_title="Week", yaxis_title="Actual Hours",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.6)",
    )
    st.plotly_chart(fig, use_container_width=True)

    if predictions:
        st.markdown("---")
        st.subheader("Week 9 Forecast Summary")
        pred_df = pd.DataFrame(predictions)
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        st.caption("Star markers on the chart indicate week 9 predicted load. Forecast uses simple OLS linear regression on actual hours w1–w8.")
