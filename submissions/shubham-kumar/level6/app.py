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

    over   = int((df["variance_pct"] > 10).sum())
    avg_v  = df["variance_pct"].mean()
    sign   = "+" if avg_v >= 0 else ""

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Projects",   len(df))
    c2.metric("Over 10% Variance", over,
              delta=f"{over} projects" if over else "All within plan",
              delta_color="inverse" if over else "off")
    c3.metric("Average Variance",  f"{sign}{avg_v:.1f}%")
    c4.metric("Units Completed",   f"{int(df['total_units'].sum()):,}")

    section_label("Hours — planned vs actual by project")
    fig = go.Figure()
    fig.add_bar(x=df["label"], y=df["total_planned"], name="Planned",
                marker_color=BLUE, marker_line_width=0)
    fig.add_bar(x=df["label"], y=df["total_actual"], name="Actual",
                marker_color=RED, marker_line_width=0)
    fig.update_layout(
        _base_layout(
            barmode="group",
            yaxis_title="Hours",
            xaxis=dict(showgrid=False, linecolor="#e2e8f0",
                       tickangle=-14, tickfont=dict(size=10)),
        )
    )
    show_chart(fig, 400)

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


# ── Page 2 — Station Load ─────────────────────────────────────────────────────

def page_station_load():
    page_title(
        "Station Load",
        "Variance heatmap across all production stations by week. "
        "Red cells indicate actual hours exceeded the plan by more than 10%.",
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
    df["station"] = df["code"] + "  " + df["name"]

    worst     = df.loc[df["variance_pct"].idxmax()]
    overloaded = int((df.groupby("station")["variance_pct"].mean() > 0).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Stations Tracked", df["station"].nunique())
    c2.metric("Stations Over Plan", overloaded,
              delta=f"{overloaded} stations", delta_color="inverse" if overloaded else "off")
    c3.metric("Worst Single Overrun",
              f"+{worst['variance_pct']}%",
              delta=f"{worst['code']} — {worst['week']}",
              delta_color="inverse")

    section_label("Variance heatmap — station by week")
    pivot = df.pivot(index="station", columns="week", values="variance_pct").fillna(0)
    fig = px.imshow(
        pivot,
        color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
        color_continuous_midpoint=0,
        text_auto=".1f",
        aspect="auto",
    )
    fig.update_coloraxes(colorbar_title="Variance %",
                         colorbar_tickfont=dict(size=10))
    fig.update_layout(
        height=480,
        font=dict(family="-apple-system, sans-serif", size=11),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        margin=dict(t=16, b=40, l=8, r=64),
        xaxis=dict(title="", side="top", tickfont=dict(size=11)),
        yaxis=dict(title="", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, width="stretch")

    section_label("Station drill-down")
    stations = sorted(df["station"].unique().tolist())
    selected = st.selectbox("Select a station:", stations)
    sub = df[df["station"] == selected].sort_values("week")

    fig2 = go.Figure()
    fig2.add_bar(x=sub["week"], y=sub["planned"], name="Planned",
                 marker_color=BLUE, marker_line_width=0)
    fig2.add_bar(x=sub["week"], y=sub["actual"], name="Actual",
                 marker_color=RED, marker_line_width=0)
    fig2.update_layout(_base_layout(
        barmode="group", yaxis_title="Hours", xaxis_title="Week",
        title=f"{selected.strip()} — weekly hours",
    ))
    show_chart(fig2, 320)


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

    deficit_weeks  = int((df["deficit"] < 0).sum())
    worst_deficit  = int(df["deficit"].min())
    total_overtime = int(df["overtime_hours"].sum())
    surplus_weeks  = int((df["deficit"] >= 0).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deficit Weeks", deficit_weeks,
              delta=f"out of {len(df)} weeks",
              delta_color="inverse" if deficit_weeks else "off")
    c2.metric("Worst Deficit",   f"{worst_deficit} hrs", delta_color="inverse")
    c3.metric("Total Overtime",  f"{total_overtime} hrs")
    c4.metric("Surplus Weeks",   surplus_weeks)

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
    show_chart(fig, 400)

    section_label("Capacity breakdown by workforce type")
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
        "Which workers are qualified to operate each station. "
        "A station with only one certified operator is a single point of failure — "
        "if that person is absent, production stops.",
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

    c1, c2, c3 = st.columns(3)
    c1.metric("Single Points of Failure", spof_n,
              delta=f"{spof_n} stations at risk",
              delta_color="inverse" if spof_n else "off")
    c2.metric("Adequately Covered", covered_n,
              delta=f"{covered_n} stations with 2+ operators")
    c3.metric("Average Coverage", f"{avg_cover:.1f}",
              delta="operators per station")

    section_label("Operator count by station")
    df_sorted = df.sort_values("coverage_count")
    colors = [RED if v else GREEN for v in df_sorted["is_spof"]]
    fig = go.Figure()
    fig.add_bar(
        x=df_sorted["name"],
        y=df_sorted["coverage_count"],
        marker_color=colors,
        marker_line_width=0,
        text=df_sorted["coverage_count"],
        textposition="outside",
        textfont=dict(size=11, color="#374151"),
    )
    fig.update_layout(_base_layout(
        yaxis=dict(
            gridcolor="#f1f5f9", linecolor="#e2e8f0",
            tickfont=dict(size=11), range=[0, df["coverage_count"].max() + 2],
            title="Qualified operators",
        ),
        xaxis=dict(showgrid=False, linecolor="#e2e8f0",
                   tickangle=-14, tickfont=dict(size=10), title="Station"),
        showlegend=False,
    ))
    show_chart(fig, 360)

    section_label("Coverage detail")
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


def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("## Factory Intelligence")
    st.caption("Enter your access password to continue.")
    pwd = st.text_input("Password", type="password", placeholder="Enter password")
    if st.button("Enter", type="primary"):
        expected = ""
        try:
            expected = st.secrets["APP_PASSWORD"]
        except Exception:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            expected = os.getenv("APP_PASSWORD", "")
        if pwd == expected:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


def main():
    check_password()

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
