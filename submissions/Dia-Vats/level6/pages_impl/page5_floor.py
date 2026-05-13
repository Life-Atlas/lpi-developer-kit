"""Page 5 — Factory Floor (Bonus B)"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query

# Grid positions per spec: 011→row0,col0 / 012→row0,col1 / ... / 021→row2,col1
STATION_GRID = {
    "011": (0, 0), "012": (0, 1), "013": (0, 2), "014": (0, 3),
    "015": (1, 0), "016": (1, 1), "017": (1, 2), "018": (1, 3),
    "019": (2, 0), "021": (2, 1),
}

FEEDS_INTO_EDGES = [
    ("011","012"),("012","013"),("013","014"),("014","015"),
    ("015","016"),("016","017"),("017","018"),("018","019"),("019","021"),
]


def render():
    st.markdown('<div class="page-title">Factory Floor</div>', unsafe_allow_html=True)
    st.markdown("Scatter-based factory floor plan. Stations coloured by load severity. Hover for active projects and overload %.")

    rows = run_query("""
        MATCH (wo:WorkOrder)-[:AT_STATION]->(s:Station)
        MATCH (wo)-[r:SCHEDULED_IN]->(wk:Week)
        MATCH (p:Project)-[:HAS_WORKORDER]->(wo)
        WITH s,
             sum(r.planned_hours) AS planned,
             sum(r.actual_hours)  AS actual,
             collect(DISTINCT p.project_name) AS projects
        RETURN
            s.station_code AS station_code,
            s.station_name AS station_name,
            planned, actual, projects
    """)

    if not rows:
        st.error("No data returned. Run seed_graph.py first.")
        return

    df = pd.DataFrame(rows)
    df["variance_pct"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)

    def severity_color(v):
        if v > 15:  return "#ef4444"
        if v > 5:   return "#f97316"
        if v > 0:   return "#facc15"
        return "#4ade80"

    # Build scatter points
    x_vals, y_vals, colors, sizes, labels, hovers = [], [], [], [], [], []
    station_pos = {}  # code -> (x, y) for drawing edges

    for _, row in df.iterrows():
        sc = row["station_code"]
        if sc not in STATION_GRID:
            continue
        grid_r, grid_c = STATION_GRID[sc]
        # invert row so row0 is at top
        x = grid_c * 2.5
        y = (2 - grid_r) * 2.0
        station_pos[sc] = (x, y)

        proj_list = ", ".join(row["projects"][:3])
        hover = (f"<b>{sc} — {row['station_name']}</b><br>"
                 f"Planned: {row['planned']:.0f} hrs<br>"
                 f"Actual:  {row['actual']:.0f} hrs<br>"
                 f"Overload: {row['variance_pct']:.1f}%<br>"
                 f"Projects: {proj_list}")

        x_vals.append(x); y_vals.append(y)
        colors.append(severity_color(row["variance_pct"]))
        sizes.append(40 + max(0, row["variance_pct"]) * 1.5)
        labels.append(f"{sc}")
        hovers.append(hover)

    fig = go.Figure()

    # Draw FEEDS_INTO edges first
    for src, dst in FEEDS_INTO_EDGES:
        if src in station_pos and dst in station_pos:
            sx, sy = station_pos[src]
            dx, dy = station_pos[dst]
            fig.add_trace(go.Scatter(
                x=[sx, dx], y=[sy, dy], mode="lines",
                line=dict(color="#334155", width=2, dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))

    # Station nodes
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode="markers+text",
        marker=dict(color=colors, size=sizes, line=dict(color="#1e293b", width=2),
                    opacity=0.9),
        text=labels, textposition="middle center",
        textfont=dict(color="#f1f5f9", size=11, family="Inter"),
        hovertext=hovers, hoverinfo="text",
        showlegend=False,
    ))

    # Legend annotation
    for color, label in [("#4ade80","On track"),("#facc15","Slight over"),
                         ("#f97316",">5% over"),("#ef4444",">15% over")]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=color, size=12),
            name=label, showlegend=True,
        ))

    fig.update_layout(
        template="plotly_dark",
        title="Factory Floor — Station Load Map",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 9]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 5]),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.8)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    # Table summary
    display = df[df["station_code"].isin(STATION_GRID)][
        ["station_code","station_name","planned","actual","variance_pct"]
    ].copy()
    display.columns = ["Code","Station","Planned hrs","Actual hrs","Overload %"]
    st.dataframe(display.style.background_gradient(subset=["Overload %"], cmap="RdYlGn_r"),
                 use_container_width=True, hide_index=True)
