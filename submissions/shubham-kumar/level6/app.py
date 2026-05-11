"""
app.py  —  Factory Intelligence Dashboard
Neo4j + Streamlit  |  Level 6  |  Shubham Kumar
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from neo4j import GraphDatabase

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Factory Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS — targets Streamlit's actual rendered DOM ────────────────────────────

st.markdown("""
<style>

/* ── Global font ── */
html, body, [class*="css"], .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu  { visibility: hidden; }
footer     { visibility: hidden; }
header     { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Main container ── */
.main .block-container {
    padding: 2.25rem 2.75rem 3rem 2.75rem;
    max-width: 1400px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: 1px solid #1e293b !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
    color: #94a3b8 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #1e293b !important;
}

/* Sidebar radio labels */
section[data-testid="stSidebar"] .stRadio label span {
    color: #cbd5e1 !important;
    font-size: 0.875rem !important;
}
section[data-testid="stSidebar"] .stRadio label:has(input:checked) span {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ── Main content area — force light background ── */
.stApp {
    background: #f1f5f9 !important;
}
.main .block-container {
    background: #ffffff;
    border-radius: 12px;
    padding: 2.25rem 2.75rem 3rem 2.75rem;
    max-width: 1400px;
    box-shadow: 0 1px 4px rgba(15,23,42,0.06);
}
h1, h2, h3, h4, p, span, label, div {
    color: #0f172a;
}
.stMarkdown p { color: #374151; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px;
    padding: 1.1rem 1.4rem !important;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #64748b !important;
}
[data-testid="stMetricLabel"] p {
    color: #64748b !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    line-height: 1.2 !important;
}
[data-testid="stMetricValue"] div {
    font-size: 1.8rem !important;
    color: #0f172a !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.775rem !important;
}

/* ── Headings ── */
h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; }

/* ── Divider ── */
hr { border-color: #e2e8f0 !important; margin: 1.5rem 0 !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Button ── */
.stButton > button[kind="primary"] {
    background: #2563eb !important;
    border: none !important;
    border-radius: 7px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.5rem !important;
    font-size: 0.875rem !important;
}

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-size: 0.875rem !important;
    line-height: 1.6 !important;
}

/* ── Self-test rows ── */
.check-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.1rem;
    border-radius: 7px;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.check-pass {
    background: #f0fdf4;
    border-left: 3px solid #16a34a;
    color: #14532d;
}
.check-fail {
    background: #fef2f2;
    border-left: 3px solid #dc2626;
    color: #7f1d1d;
}
.check-score {
    font-weight: 700;
    font-size: 0.8rem;
    margin-left: 1rem;
    white-space: nowrap;
}
.score-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin-top: 1rem;
    font-weight: 700;
    font-size: 1rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.score-full { background:#f0fdf4; color:#14532d; border:1px solid #bbf7d0; }
.score-part { background:#fffbeb; color:#78350f; border:1px solid #fde68a; }
.score-low  { background:#fef2f2; color:#7f1d1d; border:1px solid #fecaca; }

</style>
""", unsafe_allow_html=True)


# ── Neo4j ─────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_driver():
    try:
        uri  = st.secrets["NEO4J_URI"]
        user = st.secrets.get("NEO4J_USER", "neo4j")
        pwd  = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        uri  = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd  = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, pwd))


def query(cypher, params=None):
    driver = get_driver()
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher, params or {})]


# ── Chart defaults ────────────────────────────────────────────────────────────

BLUE   = "#2563eb"
RED    = "#ef4444"
GREEN  = "#16a34a"
AMBER  = "#f59e0b"
PURPLE = "#7c3aed"

def _base_layout(**overrides):
    base = dict(
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                  size=12, color="#374151"),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=48, b=44, l=52, r=20),
        title_font=dict(size=13, color="#0f172a", family="inherit"),
        title_x=0,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(size=11), bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(showgrid=False,    linecolor="#e2e8f0", tickfont=dict(size=11), tickcolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=11), tickcolor="#e2e8f0"),
    )
    base.update(overrides)
    return base


def show_chart(fig, height=400):
    fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch")


# ── Shared helpers ────────────────────────────────────────────────────────────

def page_title(title, subtitle):
    st.markdown(f"## {title}")
    st.caption(subtitle)
    st.divider()


def section_label(text):
    st.markdown(
        f'<p style="font-size:0.7rem;font-weight:600;color:#94a3b8;'
        f'text-transform:uppercase;letter-spacing:0.08em;margin:1.5rem 0 0.5rem 0">'
        f'{text}</p>',
        unsafe_allow_html=True,
    )


# ── Page 1 — Project Overview ─────────────────────────────────────────────────

def page_project_overview():
    page_title(
        "Project Overview",
        "Planned vs actual performance across all 8 active construction projects.",
    )

    rows = query("""
        MATCH (p:Project)-[:HAS_ENTRY]->(pe:ProductionEntry)
        MATCH (pe)-[:FOR_PRODUCT]->(pr:Product)
        RETURN p.project_id   AS project_id,
               p.project_name AS project_name,
               p.etapp        AS etapp,
               sum(pe.planned_hours)          AS total_planned,
               sum(pe.actual_hours)           AS total_actual,
               sum(pe.completed_units)        AS total_units,
               collect(DISTINCT pr.product_type) AS products
        ORDER BY p.project_id
    """)
    df = pd.DataFrame(rows)
    df["variance_pct"] = (
        (df["total_actual"] - df["total_planned"]) / df["total_planned"] * 100
    ).round(1)
    df["label"] = df["project_id"] + "  " + df["project_name"]

    over  = int((df["variance_pct"] > 10).sum())
    avg_v = df["variance_pct"].mean()
    sign  = "+" if avg_v >= 0 else ""

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Projects",   len(df))
    c2.metric("Over 10% Variance", over,
              delta=f"{over} projects" if over else "All within plan",
              delta_color="inverse" if over else "off")
    c3.metric("Average Variance",  f"{sign}{avg_v:.1f}%")
    c4.metric("Units Completed",   f"{int(df['total_units'].sum()):,}")

    # ── Hours side-by-side with product breakdown ──────────────────────────────
    ch_l, ch_r = st.columns(2)

    with ch_l:
        section_label("Planned vs actual hours by project")
        fig = go.Figure()
        fig.add_bar(x=df["label"], y=df["total_planned"], name="Planned",
                    marker_color=BLUE, marker_line_width=0)
        fig.add_bar(x=df["label"], y=df["total_actual"], name="Actual",
                    marker_color=RED, marker_line_width=0)
        fig.update_layout(_base_layout(
            barmode="group", yaxis_title="Hours",
            xaxis=dict(showgrid=False, linecolor="#e2e8f0",
                       tickangle=-20, tickfont=dict(size=9)),
        ))
        show_chart(fig, 380)

    with ch_r:
        section_label("Actual hours by product type per project")
        prod_rows = query("""
            MATCH (p:Project)-[:HAS_ENTRY]->(pe:ProductionEntry)-[:FOR_PRODUCT]->(pr:Product)
            RETURN p.project_id         AS project_id,
                   pr.product_type      AS product_type,
                   sum(pe.actual_hours) AS actual_hours
            ORDER BY p.project_id, pr.product_type
        """)
        if prod_rows:
            pdf = pd.DataFrame(prod_rows)
            fig_prod = px.bar(
                pdf, x="project_id", y="actual_hours", color="product_type",
                barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_prod.update_layout(_base_layout(
                yaxis_title="Actual hours", xaxis_title="Project",
                xaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=10)),
            ))
            show_chart(fig_prod, 380)

    # ── Project detail table ───────────────────────────────────────────────────
    section_label("Project detail")
    df["products"] = df["products"].apply(lambda x: ", ".join(sorted(x)) if x else "—")
    display = df[["project_id", "project_name", "etapp",
                  "total_planned", "total_actual", "variance_pct", "total_units", "products"]].copy()
    display.columns = ["ID", "Project", "Etapp",
                       "Planned hrs", "Actual hrs", "Variance %", "Units", "Products"]
    display["Planned hrs"] = display["Planned hrs"].round(1)
    display["Actual hrs"]  = display["Actual hrs"].round(1)

    def _var_style(v):
        if v > 10: return "color:#dc2626; font-weight:600"
        if v > 0:  return "color:#d97706"
        return "color:#16a34a; font-weight:500"

    st.dataframe(
        display.style.map(_var_style, subset=["Variance %"]),
        width="stretch", hide_index=True,
    )

    # ── Weekly drill-down for selected project ─────────────────────────────────
    section_label("Weekly performance drill-down")
    proj_ids = sorted(df["project_id"].tolist()) if not df.empty else []
    sel_proj = st.selectbox("Select project:", proj_ids, key="po_proj_sel")
    week_rows = query("""
        MATCH (p:Project {project_id: $pid})-[:HAS_ENTRY]->(pe:ProductionEntry)
        MATCH (pe)-[:IN_WEEK]->(w:Week)
        RETURN w.week_id               AS week,
               sum(pe.planned_hours)   AS planned,
               sum(pe.actual_hours)    AS actual,
               sum(pe.completed_units) AS units
        ORDER BY w.week_id
    """, {"pid": sel_proj})
    if week_rows:
        wdf = pd.DataFrame(week_rows)
        wdf["efficiency"] = (
            wdf["planned"] / wdf["actual"].replace(0, float("nan")) * 100
        ).round(1)
        fig_wk = go.Figure()
        fig_wk.add_bar(x=wdf["week"], y=wdf["planned"], name="Planned",
                       marker_color=BLUE, marker_line_width=0, opacity=0.85)
        fig_wk.add_bar(x=wdf["week"], y=wdf["actual"], name="Actual",
                       marker_color=RED, marker_line_width=0, opacity=0.85)
        fig_wk.add_scatter(
            x=wdf["week"], y=wdf["efficiency"],
            mode="lines+markers", name="Efficiency %",
            yaxis="y2",
            line=dict(color=AMBER, width=2, dash="dot"),
            marker=dict(size=7, color=AMBER, line=dict(width=2, color="#fff")),
        )
        fig_wk.update_layout(_base_layout(
            barmode="group", xaxis_title="Week",
            yaxis=dict(title="Hours", gridcolor="#f1f5f9",
                       linecolor="#e2e8f0", tickfont=dict(size=11)),
            yaxis2=dict(title="Efficiency %", overlaying="y", side="right",
                        showgrid=False, tickfont=dict(size=11),
                        tickcolor="#e2e8f0", linecolor="#e2e8f0",
                        range=[50, 150]),
        ))
        show_chart(fig_wk, 340)


# ── Page 2 — Station Load ─────────────────────────────────────────────────────

def page_station_load():
    page_title(
        "Station Load",
        "Variance heatmap across all production stations by week. "
        "Red cells indicate actual hours exceeded the plan.",
    )

    rows = query("""
        MATCH (pe:ProductionEntry)-[:AT_STATION]->(s:Station)
        MATCH (pe)-[:IN_WEEK]->(w:Week)
        RETURN s.station_code AS code,
               s.station_name AS name,
               w.week_id      AS week,
               sum(pe.planned_hours) AS planned,
               sum(pe.actual_hours)  AS actual
        ORDER BY s.station_code, w.week_id
    """)
    df = pd.DataFrame(rows)
    df["variance_pct"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)
    df["excess"]       = (df["actual"] - df["planned"]).clip(lower=0)
    df["station"]      = df["code"] + "  " + df["name"]

    worst      = df.loc[df["variance_pct"].idxmax()]
    overloaded = int((df.groupby("station")["variance_pct"].mean() > 0).sum())
    total_excess = df["excess"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stations Tracked",  df["station"].nunique())
    c2.metric("Stations Over Plan", overloaded,
              delta=f"{overloaded} stations", delta_color="inverse" if overloaded else "off")
    c3.metric("Worst Single Overrun",
              f"+{worst['variance_pct']}%",
              delta=f"{worst['code']} — {worst['week']}",
              delta_color="inverse")
    c4.metric("Total Excess Hours", f"{total_excess:.0f} hrs",
              delta="across all stations & weeks", delta_color="inverse")

    # ── Variance heatmap ───────────────────────────────────────────────────────
    section_label("Variance heatmap — station by week")
    pivot = df.pivot_table(
        index="station", columns="week", values="variance_pct", aggfunc="mean"
    ).fillna(0)
    fig = px.imshow(
        pivot,
        color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
        color_continuous_midpoint=0,
        text_auto=".1f",
        aspect="auto",
    )
    fig.update_coloraxes(colorbar_title="Variance %", colorbar_tickfont=dict(size=10))
    fig.update_layout(
        height=400,
        font=dict(family="-apple-system, sans-serif", size=11),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        margin=dict(t=16, b=40, l=8, r=64),
        xaxis=dict(title="", side="top", tickfont=dict(size=11)),
        yaxis=dict(title="", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, width="stretch")

    # ── Drill-down left, overrun leaderboard right ─────────────────────────────
    dd_l, dd_r = st.columns([3, 2])

    with dd_l:
        section_label("Station weekly drill-down")
        stations = sorted(df["station"].unique().tolist())
        selected = st.selectbox("Select a station:", stations)
        sub = df[df["station"] == selected].sort_values("week")
        fig2 = go.Figure()
        fig2.add_bar(x=sub["week"], y=sub["planned"], name="Planned",
                     marker_color=BLUE, marker_line_width=0)
        fig2.add_bar(x=sub["week"], y=sub["actual"], name="Actual",
                     marker_color=RED, marker_line_width=0)
        # variance % line on secondary axis
        fig2.add_scatter(
            x=sub["week"], y=sub["variance_pct"],
            mode="lines+markers", name="Variance %",
            yaxis="y2",
            line=dict(color=AMBER, width=2, dash="dot"),
            marker=dict(size=6, color=AMBER, line=dict(width=2, color="#fff")),
        )
        fig2.update_layout(_base_layout(
            barmode="group", xaxis_title="Week",
            yaxis=dict(title="Hours", gridcolor="#f1f5f9",
                       linecolor="#e2e8f0", tickfont=dict(size=11)),
            yaxis2=dict(title="Variance %", overlaying="y", side="right",
                        showgrid=False, tickfont=dict(size=11),
                        tickcolor="#e2e8f0", linecolor="#e2e8f0"),
        ))
        show_chart(fig2, 320)

    with dd_r:
        section_label("Cumulative excess hours — all weeks")
        overrun_df = (
            df.groupby("station", as_index=False)["excess"]
            .sum()
            .sort_values("excess", ascending=False)
        )
        fig_or = go.Figure()
        fig_or.add_bar(
            x=overrun_df["excess"].round(1),
            y=overrun_df["station"],
            orientation="h",
            marker_color=[RED if v > 0 else GREEN for v in overrun_df["excess"]],
            marker_line_width=0,
            text=overrun_df["excess"].apply(
                lambda v: f"+{v:.0f} h" if v > 0 else "on plan"
            ),
            textposition="outside",
            textfont=dict(size=10, color="#374151"),
        )
        fig_or.update_layout(_base_layout(
            xaxis_title="Excess hours",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", linecolor="#e2e8f0",
                       tickfont=dict(size=10)),
            yaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=9),
                       autorange="reversed"),
            showlegend=False,
        ))
        show_chart(fig_or, 320)

    # ── Projects driving overload at selected station ──────────────────────────
    section_label(f"Projects contributing overload — {selected.strip()}")
    proj_contrib = query("""
        MATCH (pe:ProductionEntry)-[:AT_STATION]->(s:Station)
        WHERE s.station_name = $sname
        MATCH (p:Project)-[:HAS_ENTRY]->(pe)
        WHERE pe.actual_hours > pe.planned_hours
        RETURN p.project_id   AS project_id,
               p.project_name AS project_name,
               round(sum(pe.actual_hours - pe.planned_hours), 1) AS excess_hours,
               round(sum(pe.actual_hours), 1)                    AS actual_hours,
               round(sum(pe.planned_hours), 1)                   AS planned_hours
        ORDER BY excess_hours DESC
    """, {"sname": selected.split("  ", 1)[-1] if "  " in selected else selected})
    if proj_contrib:
        cdf = pd.DataFrame(proj_contrib)
        cdf.columns = ["ID", "Project", "Excess hrs", "Actual hrs", "Planned hrs"]
        def _exc_style(v):
            return "color:#dc2626; font-weight:600" if v > 0 else "color:#16a34a"
        st.dataframe(
            cdf.style.map(_exc_style, subset=["Excess hrs"]),
            width="stretch", hide_index=True,
        )
    else:
        st.caption("No project overruns recorded at this station.")


# ── Page 3 — Capacity Tracker ─────────────────────────────────────────────────

def page_capacity_tracker():
    page_title(
        "Capacity Tracker",
        "Factory-wide workforce capacity against total planned demand across 8 weeks. "
        "Deficit periods indicate demand exceeded available hours.",
    )

    rows = query("""
        MATCH (w:Week)-[:HAS_CAPACITY]->(c:CapacitySnapshot)
        RETURN w.week_id         AS week,
               c.total_capacity  AS capacity,
               c.total_planned   AS planned,
               c.deficit         AS deficit,
               c.own_hours       AS own_hours,
               c.hired_hours     AS hired_hours,
               c.overtime_hours  AS overtime_hours
        ORDER BY w.week_id
    """)
    df = pd.DataFrame(rows)
    df_sorted = df.sort_values("week").copy()
    df_sorted["demand_delta"] = df_sorted["planned"].diff().fillna(0).round(1)
    cap_safe = df["capacity"].replace(0, float("nan"))
    df["overtime_pct"] = (df["overtime_hours"] / cap_safe * 100).round(1)
    df["hired_pct"]    = (df["hired_hours"]    / cap_safe * 100).round(1)

    deficit_weeks  = int((df["deficit"] < 0).sum())
    worst_deficit  = int(df["deficit"].min())
    total_overtime = int(df["overtime_hours"].sum())
    avg_ot_dep     = df["overtime_pct"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deficit Weeks", deficit_weeks,
              delta=f"out of {len(df)} weeks",
              delta_color="inverse" if deficit_weeks else "off")
    c2.metric("Worst Deficit",        f"{worst_deficit} hrs", delta_color="inverse")
    c3.metric("Total Overtime",       f"{total_overtime} hrs")
    c4.metric("Avg Overtime Dependency", f"{avg_ot_dep:.1f}%",
              delta="of capacity per week")

    # ── Capacity vs demand — full width ───────────────────────────────────────
    section_label("Capacity vs demand by week")
    fig = go.Figure()
    fig.add_scatter(
        x=df["week"], y=df["capacity"],
        mode="lines+markers", name="Available capacity",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=7, color=GREEN, line=dict(width=2, color="#fff")),
    )
    fig.add_scatter(
        x=df["week"], y=df["planned"],
        mode="lines+markers", name="Planned demand",
        line=dict(color=RED, width=2.5, dash="dot"),
        marker=dict(size=7, color=RED, line=dict(width=2, color="#fff")),
    )
    for _, row in df[df["deficit"] < 0].iterrows():
        fig.add_vrect(
            x0=row["week"], x1=row["week"],
            fillcolor="#ef4444", opacity=0.06, line_width=0,
            annotation_text=f"{int(row['deficit'])} hrs",
            annotation_font=dict(size=10, color="#b91c1c"),
            annotation_position="top left",
        )
    fig.update_layout(_base_layout(yaxis_title="Hours", xaxis_title="Week"))
    show_chart(fig, 380)

    # ── Contingent labour dependency  |  WoW demand delta ─────────────────────
    ca_l, ca_r = st.columns(2)

    with ca_l:
        section_label("Contingent labour dependency % by week")
        fig_ot = go.Figure()
        fig_ot.add_bar(x=df["week"], y=df["overtime_pct"],
                       name="Overtime %", marker_color=AMBER, marker_line_width=0)
        fig_ot.add_bar(x=df["week"], y=df["hired_pct"],
                       name="Hired staff %", marker_color=PURPLE, marker_line_width=0)
        fig_ot.update_layout(_base_layout(
            barmode="group", yaxis_title="% of total capacity", xaxis_title="Week",
        ))
        show_chart(fig_ot, 300)

    with ca_r:
        section_label("Week-over-week demand change")
        delta_colors = df_sorted["demand_delta"].apply(
            lambda v: RED if v > 0 else (GREEN if v < 0 else "#94a3b8")
        ).tolist()
        fig_delta = go.Figure()
        fig_delta.add_bar(
            x=df_sorted["week"],
            y=df_sorted["demand_delta"],
            marker_color=delta_colors,
            marker_line_width=0,
            text=df_sorted["demand_delta"].apply(
                lambda v: f"+{v:.0f}h" if v > 0 else (f"{v:.0f}h" if v < 0 else "—")
            ),
            textposition="outside",
            textfont=dict(size=10),
        )
        fig_delta.add_hline(y=0, line_color="#e2e8f0", line_width=1)
        fig_delta.update_layout(_base_layout(
            yaxis_title="Hour change vs prior week",
            xaxis_title="Week",
            showlegend=False,
        ))
        show_chart(fig_delta, 300)

    # ── Workforce breakdown — full width ───────────────────────────────────────
    section_label("Workforce composition by week")
    fig2 = go.Figure()
    fig2.add_bar(x=df["week"], y=df["own_hours"],
                 name="Permanent staff", marker_color=BLUE, marker_line_width=0)
    fig2.add_bar(x=df["week"], y=df["hired_hours"],
                 name="Hired staff", marker_color=PURPLE, marker_line_width=0)
    fig2.add_bar(x=df["week"], y=df["overtime_hours"],
                 name="Overtime", marker_color=AMBER, marker_line_width=0)
    fig2.update_layout(_base_layout(
        barmode="stack", yaxis_title="Hours", xaxis_title="Week",
    ))
    show_chart(fig2, 300)


# ── Page 4 — Worker Coverage ──────────────────────────────────────────────────

def page_worker_coverage():
    page_title(
        "Worker Coverage",
        "Operator qualification map across all production stations. "
        "Stations with one or fewer certified operators are flagged as single points of failure.",
    )

    rows = query("""
        MATCH (s:Station)
        OPTIONAL MATCH (pw:Worker)-[:PRIMARY_AT]->(s)
        OPTIONAL MATCH (cw:Worker)-[:CAN_COVER]->(s)
        WITH s,
             pw.name                   AS primary_worker,
             collect(DISTINCT cw.name) AS coverers,
             count(DISTINCT cw)        AS coverage_count
        RETURN s.station_code AS code,
               s.station_name AS name,
               primary_worker,
               coverers,
               coverage_count,
               CASE WHEN coverage_count <= 1 THEN true ELSE false END AS is_spof
        ORDER BY coverage_count ASC
    """)
    df = pd.DataFrame(rows)

    spof_n    = int(df["is_spof"].sum())
    covered_n = int((df["coverage_count"] >= 2).sum())
    avg_cover = df["coverage_count"].mean()
    max_cover = int(df["coverage_count"].max())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Single Points of Failure", spof_n,
              delta=f"{spof_n} stations at risk",
              delta_color="inverse" if spof_n else "off")
    c2.metric("Adequately Covered", covered_n,
              delta=f"stations with 2+ operators")
    c3.metric("Average Coverage", f"{avg_cover:.1f}",
              delta="operators per station")
    c4.metric("Best-Covered Station", f"{max_cover} operators",
              delta=df.loc[df["coverage_count"].idxmax(), "name"])

    # ── Coverage bar  |  Worker-station matrix ────────────────────────────────
    cv_l, cv_r = st.columns([2, 3])

    with cv_l:
        section_label("Qualified operators per station")
        df_srt = df.sort_values("coverage_count")
        fig = go.Figure()
        fig.add_bar(
            x=df_srt["coverage_count"],
            y=df_srt["name"],
            orientation="h",
            marker_color=[RED if v else GREEN for v in df_srt["is_spof"]],
            marker_line_width=0,
            text=df_srt["coverage_count"],
            textposition="outside",
            textfont=dict(size=11, color="#374151"),
        )
        fig.update_layout(_base_layout(
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", linecolor="#e2e8f0",
                       tickfont=dict(size=11), title="Operators",
                       range=[0, df["coverage_count"].max() + 2]),
            yaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=10)),
            showlegend=False,
        ))
        show_chart(fig, 420)

    with cv_r:
        section_label("Worker — station qualification matrix")
        matrix_rows = query("""
            MATCH (w:Worker)
            OPTIONAL MATCH (w)-[:CAN_COVER]->(s:Station)
            RETURN w.name AS worker, collect(DISTINCT s.station_name) AS stations
            ORDER BY w.name
        """)
        if matrix_rows:
            mdf = pd.DataFrame(matrix_rows)
            # unique station names — avoids duplicate-column error from non-unique codes
            all_stn = sorted(df["name"].drop_duplicates().tolist())
            for sn in all_stn:
                mdf[sn] = mdf["stations"].apply(lambda lst: 1 if sn in lst else 0)
            matrix = mdf.set_index("worker")[all_stn]
            fig_mx = px.imshow(
                matrix,
                color_continuous_scale=[[0, "#f8fafc"], [1, BLUE]],
                text_auto=False,
                aspect="auto",
            )
            fig_mx.update_coloraxes(showscale=False)
            fig_mx.update_layout(
                height=420,
                font=dict(family="-apple-system, sans-serif", size=11),
                plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                margin=dict(t=24, b=8, l=8, r=8),
                xaxis=dict(title="", side="top", tickfont=dict(size=9),
                           tickangle=-35),
                yaxis=dict(title="", tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_mx, width="stretch")

    # ── Coverage detail table ──────────────────────────────────────────────────
    section_label("Station coverage detail")
    display = df.copy()
    display["coverers"] = display["coverers"].apply(
        lambda x: ", ".join(x) if x else "None assigned"
    )
    display["Status"] = display["is_spof"].apply(
        lambda x: "At risk" if x else "Covered"
    )
    display = display[["code", "name", "primary_worker",
                        "coverage_count", "coverers", "Status"]]
    display.columns = ["Code", "Station", "Primary Operator",
                       "Operators", "Who Can Cover", "Status"]

    def _status_style(v):
        if v == "At risk": return "color:#dc2626; font-weight:600"
        return "color:#16a34a; font-weight:500"

    def _row_bg(row):
        bg = "background-color:#fff5f5" if row["Status"] == "At risk" else ""
        return [bg] * len(row)

    st.dataframe(
        display.style.apply(_row_bg, axis=1).map(_status_style, subset=["Status"]),
        width="stretch", hide_index=True,
    )

    # ── Absence cascade risk ───────────────────────────────────────────────────
    section_label("Absence cascade risk — select a worker to see affected projects")
    worker_names = sorted(set(mdf["worker"].tolist())) if matrix_rows else []
    sel_worker   = st.selectbox("Worker:", worker_names, key="wc_worker_sel")
    risk_rows = query("""
        MATCH (w:Worker {name: $wname})-[:PRIMARY_AT|CAN_COVER]->(s:Station)
        MATCH (pe:ProductionEntry)-[:AT_STATION]->(s)
        MATCH (p:Project)-[:HAS_ENTRY]->(pe)
        RETURN DISTINCT
               p.project_id                     AS project_id,
               p.project_name                   AS project_name,
               collect(DISTINCT s.station_name) AS at_risk_stations,
               round(sum(pe.planned_hours), 1)  AS hours_at_risk
        ORDER BY hours_at_risk DESC
    """, {"wname": sel_worker})
    if risk_rows:
        rdf = pd.DataFrame(risk_rows)
        rdf["at_risk_stations"] = rdf["at_risk_stations"].apply(
            lambda x: ", ".join(sorted(x))
        )
        rdf.columns = ["ID", "Project", "Stations Affected", "Planned hrs at Risk"]

        def _risk_style(v):
            if v > 200: return "color:#dc2626; font-weight:600"
            if v > 100: return "color:#d97706"
            return "color:#374151"

        st.dataframe(
            rdf.style.map(_risk_style, subset=["Planned hrs at Risk"]),
            width="stretch", hide_index=True,
        )
        total_risk = rdf["Planned hrs at Risk"].sum()
        st.caption(
            f"If **{sel_worker}** is absent, {len(rdf)} project(s) face operator gaps — "
            f"{total_risk:.0f} planned hours are exposed across the stations above."
        )
    else:
        st.caption(f"{sel_worker} is not the primary or cover operator at any station.")


# ── Page 5 — Self-Test ────────────────────────────────────────────────────────

def run_checks():
    driver = get_driver()
    results = []

    try:
        with driver.session() as s:
            s.run("RETURN 1")
        results.append(("Neo4j connection is alive", True, 3))
    except Exception as e:
        results.append((f"Neo4j connection failed — {e}", False, 3))
        return results

    with driver.session() as s:
        c = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        results.append((f"{c} nodes in graph (minimum 50)", c >= 50, 3))

        c = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        results.append((f"{c} relationships in graph (minimum 100)", c >= 100, 3))

        c = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        results.append((f"{c} distinct node labels (minimum 6)", c >= 6, 3))

        c = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN count(relationshipType) AS c"
        ).single()["c"]
        results.append((f"{c} distinct relationship types (minimum 8)", c >= 8, 3))

        rows = [dict(r) for r in s.run("""
            MATCH (p:Project)-[:HAS_ENTRY]->(pe:ProductionEntry)-[:AT_STATION]->(s:Station)
            WHERE pe.actual_hours > pe.planned_hours * 1.1
            RETURN p.project_name   AS project,
                   s.station_name   AS station,
                   pe.planned_hours AS planned,
                   pe.actual_hours  AS actual
            LIMIT 10
        """)]
        results.append((
            f"Variance query returned {len(rows)} result{'s' if len(rows) != 1 else ''}",
            len(rows) > 0, 5
        ))

    return results


def page_self_test():
    page_title(
        "Self-Test",
        "Six automated checks against the live Neo4j graph. All checks must pass for full marks.",
    )

    if st.button("Run checks", type="primary"):
        with st.spinner("Querying Neo4j..."):
            results = run_checks()

        earned, total = 0, 0
        html = ""

        for label, passed, pts in results:
            total += pts
            if passed:
                earned += pts
                mark, score, cls = "&#10003;", f"{pts}/{pts}", "check-pass"
            else:
                mark, score, cls = "&#10007;", f"0/{pts}", "check-fail"

            html += (
                f'<div class="check-row {cls}">'
                f'<span><strong>{mark}</strong>&nbsp;&nbsp;{label}</span>'
                f'<span class="check-score">{score} pts</span>'
                f'</div>'
            )

        pct = int(earned / total * 100) if total else 0
        if   pct == 100: score_cls, label = "score-full", "All checks passed"
        elif pct >= 60:  score_cls, label = "score-part", "Partial pass"
        else:            score_cls, label = "score-low",  "Checks failed"

        html += (
            f'<div class="score-total {score_cls}">'
            f'<span>{label}</span>'
            f'<span>{earned} / {total} pts</span>'
            f'</div>'
        )

        st.markdown(html, unsafe_allow_html=True)


# ── Navigation ────────────────────────────────────────────────────────────────

PAGES = {
    "Project Overview": page_project_overview,
    "Station Load":     page_station_load,
    "Capacity Tracker": page_capacity_tracker,
    "Worker Coverage":  page_worker_coverage,
    "Self-Test":        page_self_test,
}


def main():
    with st.sidebar:
        st.markdown("### Factory Intelligence")
        st.caption("VSAB Steel Fabrication  \n8 projects · 9 stations · 13 workers")
        st.divider()
        page = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        st.caption("Level 6 · Shubham Kumar · Neo4j + Streamlit")

    PAGES[page]()


if __name__ == "__main__":
    main()
