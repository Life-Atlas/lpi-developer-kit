"""
app.py — Streamlit factory knowledge graph dashboard.
All data queried live from Neo4j — no CSV reads at runtime.

Pages:
  1. Project Overview   — 8 projects, planned/actual hours, variance, products
  2. Station Load       — interactive Plotly chart, overloaded sessions highlighted
  3. Capacity Tracker   — weekly capacity vs demand, deficit weeks red
  4. Worker Coverage    — matrix + SPOF alerts
  5. Self-Test          — automated 6-check graph verification (20 pts)
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Factory Dashboard",
    page_icon=":material/factory:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Font Awesome injection ────────────────────────────────────────────────────

st.markdown(
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)

# ── Icon helper ───────────────────────────────────────────────────────────────

def _fa(cls, color="inherit", size="1em"):
    return f'<i class="fa-solid {cls}" style="color:{color};font-size:{size};margin-right:8px"></i>'


def page_title(fa_cls, label, color="#1e293b"):
    st.markdown(
        f'<h1 style="display:flex;align-items:center;gap:4px;margin-bottom:0">'
        f'{_fa(fa_cls, color)}{label}</h1>',
        unsafe_allow_html=True,
    )
    st.write("")   # spacing


def section(fa_cls, label, level=3, color="#64748b"):
    tag = f"h{level}"
    st.markdown(
        f'<{tag} style="margin-top:0.5rem">{_fa(fa_cls, color)}{label}</{tag}>',
        unsafe_allow_html=True,
    )


# ── Neo4j connection ──────────────────────────────────────────────────────────

def _get_creds():
    try:
        return (
            st.secrets["NEO4J_URI"],
            st.secrets.get("NEO4J_USER", "neo4j"),
            st.secrets["NEO4J_PASSWORD"],
        )
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        return (
            os.getenv("NEO4J_URI"),
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD"),
        )


@st.cache_resource
def get_driver():
    uri, user, pwd = _get_creds()
    return GraphDatabase.driver(uri, auth=(user, pwd))


def run_query(cypher, params=None):
    driver = get_driver()
    with driver.session() as session:
        return [dict(r) for r in session.run(cypher, params or {})]


# ── Self-test logic ───────────────────────────────────────────────────────────

def run_self_test():
    """Run 6 automated checks. Returns list of (label, passed, max_pts)."""
    checks = []
    driver = get_driver()

    # CHECK 1: Connection
    try:
        with driver.session() as s:
            s.run("RETURN 1")
        checks.append(("Neo4j connected", True, 3))
    except Exception as exc:
        checks.append((f"Neo4j connected — FAILED: {str(exc)[:60]}", False, 3))
        return checks

    with driver.session() as s:
        # CHECK 2: Node count
        c = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        checks.append((f"{c} nodes (min: 50)", c >= 50, 3))

        # CHECK 3: Relationship count
        c = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        checks.append((f"{c} relationships (min: 100)", c >= 100, 3))

        # CHECK 4: Distinct node labels
        c = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        checks.append((f"{c} node labels (min: 6)", c >= 6, 3))

        # CHECK 5: Distinct relationship types
        c = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN count(relationshipType) AS c"
        ).single()["c"]
        checks.append((f"{c} relationship types (min: 8)", c >= 8, 3))

        # CHECK 6: Variance query — projects/stations where actual > 110% of planned
        rows = s.run("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.project_name  AS project,
                   s.station_name  AS station,
                   r.planned_hours AS planned,
                   r.actual_hours  AS actual
            LIMIT 10
        """).data()
        checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))

    return checks


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.markdown(
    f'<h2 style="margin:0">{_fa("fa-industry", "#3b82f6", "1.1em")}Factory Dashboard</h2>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("Swedish Steel Fabrication Co.")
st.sidebar.divider()

PAGE = st.sidebar.radio(
    "Navigation",
    [
        "Project Overview",
        "Station Load",
        "Capacity Tracker",
        "Worker Coverage",
        "Self-Test",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Data source: Neo4j Knowledge Graph")
st.sidebar.caption("8 projects · 10 stations · 14 workers")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Project Overview
# ═══════════════════════════════════════════════════════════════════════════════

if PAGE == "Project Overview":
    page_title("fa-chart-bar", "Project Overview", color="#3b82f6")
    st.markdown(
        "All 8 Swedish steel construction projects — planned vs actual hours "
        "and variance summary."
    )

    proj_rows = run_query("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN p.project_id                          AS project_id,
               p.project_number                     AS project_number,
               p.project_name                       AS project_name,
               round(sum(r.planned_hours), 1)        AS total_planned,
               round(sum(r.actual_hours),  1)        AS total_actual
        ORDER BY p.project_id
    """)

    prod_rows = run_query("""
        MATCH (p:Project)-[:HAS_PRODUCT]->(prod:Product)
        RETURN p.project_id AS project_id,
               collect(prod.product_type) AS products
    """)
    prod_map = {r["project_id"]: ", ".join(sorted(r["products"])) for r in prod_rows}

    df = pd.DataFrame(proj_rows)
    df["variance_pct"] = (
        (df["total_actual"] - df["total_planned"]) / df["total_planned"] * 100
    ).round(1)
    df["products"] = df["project_id"].map(prod_map).fillna("")
    df["status"] = df["variance_pct"].apply(
        lambda v: "Over" if v > 5 else ("Slight Over" if v > 0 else "On Track")
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projects", len(df))
    c2.metric("Total Planned hrs", f"{df['total_planned'].sum():,.0f}")
    c3.metric("Total Actual hrs", f"{df['total_actual'].sum():,.0f}")
    avg_var = df["variance_pct"].mean()
    c4.metric("Avg Variance", f"{avg_var:+.1f}%")

    st.divider()

    section("fa-table-list", "Project Details")
    display = df[
        ["project_number", "project_name", "total_planned",
         "total_actual", "variance_pct", "products", "status"]
    ].copy()
    display.columns = [
        "Proj #", "Project Name", "Planned hrs",
        "Actual hrs", "Variance %", "Products", "Status",
    ]

    def _color_variance(val):
        if isinstance(val, (int, float)):
            if val > 5:
                return "color: #dc2626; font-weight: bold"
            if val > 0:
                return "color: #d97706"
            return "color: #16a34a"
        return ""

    def _color_status(val):
        if val == "Over":
            return "color: #dc2626; font-weight: bold"
        if val == "Slight Over":
            return "color: #d97706"
        return "color: #16a34a"

    st.dataframe(
        display.style
               .map(_color_variance, subset=["Variance %"])
               .map(_color_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    section("fa-chart-column", "Planned vs Actual Hours by Project")
    df_melt = df.melt(
        id_vars=["project_name"],
        value_vars=["total_planned", "total_actual"],
        var_name="Type",
        value_name="Hours",
    )
    df_melt["Type"] = df_melt["Type"].map(
        {"total_planned": "Planned", "total_actual": "Actual"}
    )
    fig = px.bar(
        df_melt,
        x="project_name", y="Hours", color="Type", barmode="group",
        color_discrete_map={"Planned": "#3b82f6", "Actual": "#ef4444"},
        labels={"project_name": "Project"},
    )
    fig.update_layout(xaxis_tickangle=-30, height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    section("fa-chart-area", "Variance % per Project")
    fig2 = px.bar(
        df, x="project_name", y="variance_pct",
        color="variance_pct",
        color_continuous_scale=["#16a34a", "#fbbf24", "#dc2626"],
        labels={"project_name": "Project", "variance_pct": "Variance %"},
        title="Variance % (positive = over plan)",
    )
    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.add_hline(y=5, line_dash="dot", line_color="orange",
                   annotation_text="5% threshold")
    fig2.update_layout(xaxis_tickangle=-30, height=380)
    st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Station Load
# ═══════════════════════════════════════════════════════════════════════════════

elif PAGE == "Station Load":
    page_title("fa-gear", "Station Load", color="#6366f1")
    st.markdown(
        "Hours per station across all 8 weeks — sessions where actual exceeds "
        "110% of planned are highlighted in red."
    )

    rows = run_query("""
        MATCH (proj:Project)-[r:SCHEDULED_AT]->(st:Station)
        RETURN st.station_code                      AS station_code,
               st.station_name                      AS station,
               r.week                               AS week,
               round(sum(r.planned_hours), 1)        AS planned,
               round(sum(r.actual_hours),  1)        AS actual
        ORDER BY st.station_code, r.week
    """)
    df = pd.DataFrame(rows)
    df["overloaded"]   = df["actual"] > df["planned"] * 1.10
    df["variance_pct"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)

    all_stations = sorted(df["station"].unique())
    selected = st.multiselect("Filter stations:", all_stations, default=all_stations)
    dff = df[df["station"].isin(selected)]

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("Stations shown", len(selected))
    c2.metric("Overloaded sessions", int(dff["overloaded"].sum()))
    avg_v = dff["variance_pct"].mean()
    c3.metric("Avg variance", f"{avg_v:+.1f}%")

    st.divider()

    section("fa-chart-column", "Planned vs Actual by Station & Week")
    df_melt = dff.melt(
        id_vars=["station", "week", "overloaded"],
        value_vars=["planned", "actual"],
        var_name="Type", value_name="Hours",
    )
    df_melt["Type"] = df_melt["Type"].map({"planned": "Planned", "actual": "Actual"})
    ncols = min(3, len(selected))
    fig = px.bar(
        df_melt, x="week", y="Hours", color="Type", barmode="group",
        facet_col="station",
        facet_col_wrap=ncols if ncols > 0 else 1,
        color_discrete_map={"Planned": "#3b82f6", "Actual": "#ef4444"},
        title="Station Load by Week",
    )
    fig.update_layout(height=max(400, 220 * ((len(selected) // ncols) + 1)) if ncols else 400)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    section("fa-fire", "Actual Hours Heatmap (Station x Week)")
    pivot = df.pivot_table(
        index="station", columns="week", values="actual", aggfunc="sum", fill_value=0
    )
    week_order = sorted(pivot.columns, key=lambda w: int(w[1:]))
    pivot = pivot[week_order]
    fig_heat = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn_r",
        title="Actual Hours Heatmap",
        labels=dict(color="Actual hrs"),
        aspect="auto",
    )
    fig_heat.update_layout(height=380)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    section("fa-circle-exclamation", "Overloaded Sessions (Actual > 110% of Planned)", color="#dc2626")
    over = df[df["overloaded"]][["station", "week", "planned", "actual", "variance_pct"]].copy()
    if not over.empty:
        over.columns = ["Station", "Week", "Planned hrs", "Actual hrs", "Variance %"]
        st.dataframe(
            over.style.map(lambda _: "background-color: #fee2e2", subset=["Variance %"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.success("No sessions overloaded beyond 110% of planned.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Capacity Tracker
# ═══════════════════════════════════════════════════════════════════════════════

elif PAGE == "Capacity Tracker":
    page_title("fa-chart-line", "Capacity Tracker", color="#f97316")
    st.markdown(
        "Weekly workforce capacity vs total planned demand — "
        "deficit weeks are highlighted in red."
    )

    rows = run_query("""
        MATCH (w:Week)
        RETURN w.week_id        AS week,
               w.own_hours      AS own_hours,
               w.hired_hours    AS hired_hours,
               w.overtime_hours AS overtime_hours,
               w.total_capacity AS capacity,
               w.total_planned  AS planned,
               w.deficit        AS deficit
        ORDER BY w.week_id
    """)
    df = pd.DataFrame(rows)
    df["status"] = df["deficit"].apply(lambda d: "Deficit" if d < 0 else "Surplus")

    deficit_weeks = int((df["deficit"] < 0).sum())
    worst_week    = df.loc[df["deficit"].idxmin(), "week"]
    worst_val     = int(df["deficit"].min())
    total_deficit = int(df[df["deficit"] < 0]["deficit"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deficit Weeks", f"{deficit_weeks} / 8")
    c2.metric("Total Deficit hrs", f"{abs(total_deficit):,}")
    c3.metric("Worst Week", worst_week)
    c4.metric("Worst Deficit", f"{worst_val:,} hrs")

    st.divider()

    section("fa-chart-line", "Total Capacity vs Planned Demand")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["week"], y=df["capacity"],
        mode="lines+markers", name="Total Capacity",
        line=dict(color="#3b82f6", width=3), marker=dict(size=9),
    ))
    fig.add_trace(go.Scatter(
        x=df["week"], y=df["planned"],
        mode="lines+markers", name="Planned Demand",
        line=dict(color="#f97316", width=3, dash="dash"), marker=dict(size=9),
    ))
    for _, row in df[df["deficit"] < 0].iterrows():
        fig.add_vrect(
            x0=row["week"], x1=row["week"],
            fillcolor="rgba(239,68,68,0.18)", line_width=0,
        )
    fig.update_layout(
        xaxis_title="Week", yaxis_title="Hours",
        height=400, legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    section("fa-layer-group", "Capacity Composition per Week")
    fig2 = px.bar(
        df, x="week",
        y=["own_hours", "hired_hours", "overtime_hours"],
        barmode="stack",
        color_discrete_map={
            "own_hours": "#3b82f6",
            "hired_hours": "#10b981",
            "overtime_hours": "#f59e0b",
        },
        labels={"value": "Hours", "variable": "Source"},
        title="Capacity: Own / Hired / Overtime",
    )
    fig2.add_scatter(
        x=df["week"], y=df["planned"],
        mode="lines+markers", name="Planned Demand",
        line=dict(color="#dc2626", width=2, dash="dot"),
        marker=dict(symbol="diamond", size=8),
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    section("fa-scale-balanced", "Deficit / Surplus per Week")
    fig3 = px.bar(
        df, x="week", y="deficit",
        color="status",
        color_discrete_map={"Deficit": "#ef4444", "Surplus": "#22c55e"},
        labels={"deficit": "Deficit/Surplus hrs", "week": "Week"},
        title="Weekly Capacity Balance",
    )
    fig3.add_hline(y=0, line_color="black", line_width=1)
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    section("fa-table", "Week-by-Week Detail")
    display = df[
        ["week", "own_hours", "hired_hours", "overtime_hours",
         "capacity", "planned", "deficit", "status"]
    ].copy()
    display.columns = [
        "Week", "Own hrs", "Hired hrs", "Overtime hrs",
        "Total Capacity", "Planned Demand", "Deficit/Surplus", "Status",
    ]

    def _color_status(val):
        if val == "Deficit":
            return "color: #dc2626; font-weight: bold"
        if val == "Surplus":
            return "color: #16a34a; font-weight: bold"
        return ""

    st.dataframe(
        display.style.map(_color_status, subset=["Status"]),
        use_container_width=True, hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Worker Coverage
# ═══════════════════════════════════════════════════════════════════════════════

elif PAGE == "Worker Coverage":
    page_title("fa-helmet-safety", "Worker Coverage Matrix", color="#10b981")
    st.markdown(
        "Which workers can cover each station.  "
        "**SPOF** = only 1 certified worker available — one absence stops the line."
    )

    cov_rows = run_query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN s.station_code       AS station_code,
               s.station_name       AS station,
               collect(w.name)      AS workers,
               count(w)             AS worker_count
        ORDER BY s.station_code
    """)
    df_cov = pd.DataFrame(cov_rows)
    df_cov["risk"] = df_cov["worker_count"].apply(
        lambda n: "SPOF" if n == 1 else ("Low" if n <= 2 else "OK")
    )
    df_cov["workers_list"] = df_cov["workers"].apply(lambda ws: ", ".join(sorted(ws)))

    spof  = int((df_cov["worker_count"] == 1).sum())
    low   = int((df_cov["worker_count"] == 2).sum())
    avg_w = df_cov["worker_count"].mean()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Stations", len(df_cov))
    c2.metric("SPOF Stations", spof)
    c3.metric("Low Coverage (2 workers)", low)
    c4.metric("Avg Workers / Station", f"{avg_w:.1f}")

    st.divider()

    section("fa-shield-halved", "Station Coverage Detail")
    display_cov = df_cov[
        ["station_code", "station", "worker_count", "workers_list", "risk"]
    ].copy()
    display_cov.columns = ["Code", "Station Name", "# Workers", "Covered By", "Risk"]

    def _highlight_risk(row):
        if row["Risk"] == "SPOF":
            return ["background-color: #fee2e2"] * len(row)
        if row["Risk"] == "Low":
            return ["background-color: #fef9c3"] * len(row)
        return [""] * len(row)

    def _color_risk(val):
        if val == "SPOF":
            return "color: #dc2626; font-weight: bold"
        if val == "Low":
            return "color: #d97706; font-weight: bold"
        return "color: #16a34a"

    st.dataframe(
        display_cov.style
                   .apply(_highlight_risk, axis=1)
                   .map(_color_risk, subset=["Risk"]),
        use_container_width=True, hide_index=True,
    )

    st.divider()

    section("fa-table-cells", "Coverage Heatmap (Worker x Station)")
    heat_rows = run_query("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN w.name AS worker, s.station_code AS station_code
        ORDER BY w.worker_id, s.station_code
    """)
    all_workers_q = run_query(
        "MATCH (w:Worker) RETURN w.name AS name ORDER BY w.worker_id"
    )
    all_stations_q = run_query(
        "MATCH (s:Station) RETURN s.station_code + ': ' + s.station_name AS label, "
        "s.station_code AS code ORDER BY s.station_code"
    )
    all_workers    = [r["name"] for r in all_workers_q]
    all_stations   = [r["code"] for r in all_stations_q]
    station_labels = {r["code"]: r["label"] for r in all_stations_q}

    df_heat = pd.DataFrame(heat_rows)
    if not df_heat.empty:
        df_heat["covers"] = 1
        pivot = df_heat.pivot_table(
            index="worker", columns="station_code", values="covers", fill_value=0
        )
        pivot = pivot.reindex(index=all_workers, columns=all_stations, fill_value=0)
        pivot.columns = [station_labels.get(c, c) for c in pivot.columns]
        fig_h = px.imshow(
            pivot,
            color_continuous_scale=["#f1f5f9", "#2563eb"],
            title="Worker x Station Coverage (blue = can cover)",
            aspect="auto",
            labels=dict(color="Covers"),
        )
        fig_h.update_layout(height=420)
        st.plotly_chart(fig_h, use_container_width=True)

    st.divider()

    section("fa-triangle-exclamation", "Bottleneck Stations", color="#dc2626")
    bn_rows = run_query("""
        MATCH (st:Station)-[:HAS_BOTTLENECK]->(b:Bottleneck)
        RETURN st.station_code     AS code,
               st.station_name     AS station,
               b.avg_overrun_pct   AS avg_overrun_pct,
               b.severity          AS severity,
               b.overrun_count     AS overrun_count,
               b.overrun_weeks     AS overrun_weeks
        ORDER BY b.avg_overrun_pct DESC
    """)
    if bn_rows:
        df_bn = pd.DataFrame(bn_rows)
        df_bn.columns = [
            "Code", "Station", "Avg Overrun %", "Severity",
            "Overrun Events", "Weeks Affected",
        ]
        st.dataframe(df_bn, use_container_width=True, hide_index=True)
    else:
        st.info("No bottleneck stations flagged.")

    st.divider()

    section("fa-id-card", "Worker Details")
    wkr_rows = run_query("""
        MATCH (w:Worker)
        OPTIONAL MATCH (w)-[:HAS_CERTIFICATION]->(c:Certification)
        RETURN w.worker_id        AS id,
               w.name             AS name,
               w.role             AS role,
               w.type             AS type,
               w.hours_per_week   AS hrs_pw,
               w.primary_station  AS primary_station,
               collect(c.name)    AS certifications
        ORDER BY w.worker_id
    """)
    df_wkr = pd.DataFrame(wkr_rows)
    df_wkr["certifications"] = df_wkr["certifications"].apply(
        lambda cs: ", ".join(sorted(cs))
    )
    df_wkr.columns = [
        "ID", "Name", "Role", "Type", "Hrs/Week", "Primary Station", "Certifications"
    ]
    st.dataframe(df_wkr, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Self-Test
# ═══════════════════════════════════════════════════════════════════════════════

elif PAGE == "Self-Test":
    page_title("fa-circle-check", "Self-Test", color="#16a34a")
    st.markdown(
        "Automated verification of the Neo4j knowledge graph.  "
        "Click **Run Self-Test** to score the graph."
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run = st.button("Run Self-Test", type="primary", use_container_width=True)
    with col_info:
        st.info(
            "Checks: connection · node count · relationship count · "
            "node labels · relationship types · variance query"
        )

    if run:
        with st.spinner("Running checks..."):
            checks = run_self_test()

        st.divider()
        total   = 0
        maximum = 0

        for label, passed, pts in checks:
            maximum += pts
            if passed:
                total += pts
                st.success(f"PASS — {label} &emsp; **{pts}/{pts}**")
            else:
                st.error(f"FAIL — {label} &emsp; **0/{pts}**")

        st.divider()
        pct = round(total / maximum * 100) if maximum else 0

        if total == maximum:
            st.balloons()
            st.success(f"## SELF-TEST SCORE: {total}/{maximum} ({pct}%)")
        elif pct >= 70:
            st.warning(f"## SELF-TEST SCORE: {total}/{maximum} ({pct}%)")
        else:
            st.error(f"## SELF-TEST SCORE: {total}/{maximum} ({pct}%)")

        st.divider()
        section("fa-list-check", "Score Breakdown")
        breakdown = [
            {
                "Check": lbl,
                "Result": "PASS" if ok else "FAIL",
                "Score": f"{pts}/{pts}" if ok else f"0/{pts}",
            }
            for lbl, ok, pts in checks
        ]
        df_br = pd.DataFrame(breakdown)

        def _result_color(val):
            return "color: #16a34a; font-weight: bold" if val == "PASS" \
                else "color: #dc2626; font-weight: bold"

        st.dataframe(
            df_br.style.map(_result_color, subset=["Result"]),
            use_container_width=True, hide_index=True,
        )

    else:
        st.markdown("""
### Check Description

| # | Check | Points |
|---|-------|--------|
| 1 | Neo4j connection alive | 3 |
| 2 | Node count >= 50 | 3 |
| 3 | Relationship count >= 100 | 3 |
| 4 | 6+ distinct node labels | 3 |
| 5 | 8+ distinct relationship types | 3 |
| 6 | Variance query returns results | 5 |
| | **Total** | **20** |

### Graph Schema

**Node labels (8):** Project · Product · Station · Worker · Week · Etapp · Certification · Bottleneck

**Relationship types (10):**
`HAS_PRODUCT` · `USES_STATION` · `SCHEDULED_AT` · `IN_ETAPP` ·
`ASSIGNED_TO` · `CAN_COVER` · `HAS_CERTIFICATION` · `REQUIRES_CERT` ·
`PROCESSED_AT` · `HAS_BOTTLENECK`
        """)
