"""
app.py — Factory Knowledge Graph Dashboard
Streamlit application with 6 pages powered by Neo4j.
"""

import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from dotenv import load_dotenv
import statsmodels.api as sm

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Factory Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* KPI metric cards */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        color: #f1f5f9;
        border-left: 4px solid;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .kpi-card h3 { margin: 0 0 0.3rem 0; font-size: 0.85rem; color: #94a3b8; font-weight: 500; }
    .kpi-card .value { font-size: 1.8rem; font-weight: 700; }
    .kpi-card .sub { font-size: 0.75rem; color: #64748b; margin-top: 0.2rem; }
    .kpi-blue   { border-color: #3b82f6; }
    .kpi-green  { border-color: #22c55e; }
    .kpi-red    { border-color: #ef4444; }
    .kpi-amber  { border-color: #f59e0b; }

    /* Self-test items */
    .check-pass { color: #22c55e; font-weight: 600; }
    .check-fail { color: #ef4444; font-weight: 600; }

    /* Section dividers */
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #e2e8f0;
        border-bottom: 2px solid #334155; padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* Hide default Streamlit footer */
    footer { visibility: hidden; }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #cbd5e1 !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ── Neo4j connection ─────────────────────────────────────────────────────────

@st.cache_resource
def get_driver():
    """Connect to Neo4j — supports both st.secrets (Cloud) and .env (local)."""
    try:
        uri      = st.secrets["NEO4J_URI"]
        user     = st.secrets["NEO4J_USER"]
        password = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        load_dotenv()
        uri      = os.getenv("NEO4J_URI")
        user     = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, password))


def query_to_df(cypher: str) -> pd.DataFrame:
    """Run a Cypher query and return the results as a DataFrame."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher)
        return pd.DataFrame([dict(r) for r in result])


# ── Sidebar navigation ──────────────────────────────────────────────────────

st.sidebar.markdown("## Factory Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", [
    "Project Overview",
    "Station Load",
    "Capacity Tracker",
    "Worker Coverage",
    "Load Forecast",
    "Self-Test",
])
st.sidebar.markdown("---")
st.sidebar.caption("Level 6 · Touqeer Hamdani")


# ── Helper: render a KPI card ────────────────────────────────────────────────

def kpi(label, value, sub="", color="blue"):
    st.markdown(f"""
    <div class="kpi-card kpi-{color}">
        <h3>{label}</h3>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Project Overview
# ══════════════════════════════════════════════════════════════════════════════

def page_project_overview():
    st.header("Project Overview")
    st.caption("All 8 factory projects with planned vs actual hours and variance analysis.")

    df = query_to_df("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH p,
             sum(r.planned_hours) AS planned,
             sum(r.actual_hours)  AS actual
        OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
        RETURN p.project_id   AS ID,
               p.project_name AS Project,
               planned        AS PlannedHours,
               actual         AS ActualHours,
               CASE 
                 WHEN planned = 0 THEN 0.0 
                 ELSE round((actual - planned) / planned * 100, 1) 
               END AS VariancePct,
               collect(DISTINCT prod.product_type) AS Products
        ORDER BY p.project_id
    """)

    if df.empty:
        st.warning("No data found. Has `seed_graph.py` been run?")
        return

    # KPI cards
    total_planned = df["PlannedHours"].sum()
    total_actual  = df["ActualHours"].sum()
    avg_var       = round((total_actual - total_planned) / total_planned * 100, 1)
    overrun_count = len(df[df["VariancePct"] > 0])

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Projects", len(df), "active in schedule", "blue")
    with c2: kpi("Total Planned Hours", f"{total_planned:,.0f} h", "across all stations", "green")
    with c3: kpi("Total Actual Hours", f"{total_actual:,.0f} h", f"{'+' if total_actual > total_planned else '-'} vs plan", "amber")
    with c4: kpi("Average Plan Variance", f"{avg_var:+.1f}%", f"{overrun_count} projects over plan", "red" if avg_var > 0 else "green")

    st.markdown("")

    # Format products column for display
    display_df = df.copy()
    display_df["Products"] = display_df["Products"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    display_df["VariancePct"] = display_df["VariancePct"].apply(lambda v: f"{v:+.1f}%")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID":           st.column_config.TextColumn("ID", width="small"),
            "Project":      st.column_config.TextColumn("Project"),
            "PlannedHours": st.column_config.NumberColumn("Planned (h)", format="%.1f"),
            "ActualHours":  st.column_config.NumberColumn("Actual (h)", format="%.1f"),
            "VariancePct":  st.column_config.TextColumn("Variance"),
            "Products":     st.column_config.TextColumn("Products"),
        },
    )

    # Bar chart: planned vs actual per project
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Planned", x=df["Project"], y=df["PlannedHours"],
                         marker_color="#3b82f6"))
    fig.add_trace(go.Bar(name="Actual",  x=df["Project"], y=df["ActualHours"],
                         marker_color=["#22c55e" if a <= p else "#ef4444"
                                       for a, p in zip(df["ActualHours"], df["PlannedHours"])]))
    fig.update_layout(
        barmode="group", template="plotly_dark",
        title="Planned vs Actual Hours by Project",
        xaxis_title="Project", yaxis_title="Hours",
        height=420, margin=dict(t=50, b=40),
        legend_title="Metric", showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Station Load
# ══════════════════════════════════════════════════════════════════════════════

def page_station_load():
    st.header("Station Load")
    st.caption("Hours per station across weeks. Red = actual exceeds planned.")

    df = query_to_df("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.station_code AS StationCode,
               s.station_name AS Station,
               r.week         AS Week,
               sum(r.planned_hours) AS Planned,
               sum(r.actual_hours)  AS Actual
        ORDER BY s.station_code, r.week
    """)

    if df.empty:
        st.warning("No data found.")
        return

    df["Overloaded"] = df["Actual"] > df["Planned"]
    df["Label"] = df["StationCode"] + " " + df["Station"]

    # Week filter
    weeks = sorted(df["Week"].unique())
    selected_weeks = st.multiselect("Filter by week", weeks, default=weeks)
    filtered = df[df["Week"].isin(selected_weeks)]

    # Grouped bar chart
    filtered = filtered.copy()
    filtered["Label_Week"] = filtered["Label"] + " - " + filtered["Week"].astype(str)

    tick_text = [
        f'<span style="color: {"#ef4444" if row["Overloaded"] else "#e2e8f0"}">{row["Label_Week"]}</span>'
        for _, row in filtered.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Planned", x=filtered["Label_Week"],
        y=filtered["Planned"], marker_color="#3b82f6",
    ))
    fig.add_trace(go.Bar(
        name="Actual", x=filtered["Label_Week"],
        y=filtered["Actual"],
        marker_color=["#ef4444" if o else "#22c55e" for o in filtered["Overloaded"]],
    ))
    fig.update_layout(
        barmode="group", template="plotly_dark",
        title="Station Load: Planned vs Actual",
        yaxis_title="Hours",
        height=500, margin=dict(t=50, b=80),
        legend_title="Metric", showlegend=True,
        xaxis=dict(
            title="Station - Week",
            tickmode="array",
            tickvals=filtered["Label_Week"],
            ticktext=tick_text
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    with st.expander("Detailed data"):
        st.dataframe(filtered[["StationCode", "Station", "Week", "Planned", "Actual", "Overloaded"]],
                      use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Capacity Tracker
# ══════════════════════════════════════════════════════════════════════════════

def page_capacity_tracker():
    st.header("Capacity Tracker")
    st.caption("Weekly capacity (own + hired + overtime) vs planned demand. Deficit weeks in red.")

    df = query_to_df("""
        MATCH (w:Week)-[r:HAS_CAPACITY]->(f:Factory)
        RETURN w.week_id       AS Week,
               r.own_hours     AS Own,
               r.hired_hours   AS Hired,
               r.overtime_hours AS Overtime,
               r.own_hours + r.hired_hours + r.overtime_hours AS TotalCapacity,
               r.total_planned AS PlannedDemand,
               r.deficit       AS Deficit
        ORDER BY w.week_id
    """)

    if df.empty:
        st.warning("No data found.")
        return

    deficit_weeks = len(df[df["Deficit"] < 0])
    total_deficit = df[df["Deficit"] < 0]["Deficit"].sum()

    c1, c2, c3 = st.columns(3)
    with c1: kpi("Deficit Weeks", f"{deficit_weeks} / {len(df)}", "weeks over capacity", "red")
    with c2: kpi("Cumulative Capacity Deficit", f"{total_deficit:+,.0f} h", "cumulative shortfall", "red")
    with c3: kpi("Maximum Weekly Deficit", f"{df['Deficit'].min():+,.0f} h", f"in {df.loc[df['Deficit'].idxmin(), 'Week']}", "amber")

    st.markdown("")

    # Color x-axis labels red for deficit weeks (used on the bottom chart)
    tick_text = [
        f'<span style="color: {"#ef4444" if row["Deficit"] < 0 else "#e2e8f0"}">{row["Week"]}</span>'
        for _, row in df.iterrows()
    ]

    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1,
        row_heights=[0.75, 0.25]
    )

    # Top Chart: Stacked bar (capacity components) + line (demand)
    fig.add_trace(go.Bar(name="Own Staff",  x=df["Week"], y=df["Own"],      marker_color="#3b82f6"), row=1, col=1)
    fig.add_trace(go.Bar(name="Hired",      x=df["Week"], y=df["Hired"],    marker_color="#8b5cf6"), row=1, col=1)
    fig.add_trace(go.Bar(name="Overtime",   x=df["Week"], y=df["Overtime"], marker_color="#f59e0b"), row=1, col=1)

    fig.add_trace(go.Scatter(
        name="Planned Demand", x=df["Week"], y=df["PlannedDemand"],
        mode="lines+markers", line=dict(color="#ef4444", width=3, dash="dot"),
        marker=dict(size=8),
    ), row=1, col=1)

    # Bottom Chart: Surplus/Deficit Bar
    fig.add_trace(go.Bar(
        name="Surplus / Deficit", x=df["Week"], y=df["Deficit"],
        marker_color=["#ef4444" if d < 0 else "#22c55e" for d in df["Deficit"]],
        text=[f"{d:+.0f}" for d in df["Deficit"]],
        textposition="outside",
        showlegend=False,
        hovertemplate="Variance: %{y:+.0f}h<extra></extra>"
    ), row=2, col=1)

    fig.update_layout(
        barmode="stack", template="plotly_dark",
        title="Weekly Capacity vs Demand",
        height=600, margin=dict(t=50, b=40),
        legend=dict(title="Capacity Type", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Hours", row=1, col=1)
    fig.update_yaxes(title_text="Variance", row=2, col=1)
    fig.update_xaxes(
        title="Week", tickmode="array", 
        tickvals=df["Week"], ticktext=tick_text, 
        row=2, col=1
    )
    st.plotly_chart(fig, use_container_width=True)

    # Data table
    with st.expander("Detailed data"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Worker Coverage
# ══════════════════════════════════════════════════════════════════════════════

def page_worker_coverage():
    st.header("Worker Coverage Matrix")
    st.caption("Which workers can cover which stations. SPOF stations (≤ 1 unique worker) flagged in red.")

    # Coverage data
    df = query_to_df("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN s.station_code AS StationCode,
               s.station_name AS Station,
               collect(w.name) AS Workers,
               count(w) AS WorkerCount
        ORDER BY WorkerCount ASC
    """)

    if df.empty:
        st.warning("No data found.")
        return

    spof = df[df["WorkerCount"] <= 1]
    c1, c2 = st.columns(2)
    with c1: kpi("Total Stations", len(df), "with assigned coverage", "blue")
    with c2: kpi("SPOF Stations", len(spof),
                 ", ".join(spof["Station"].tolist()) if len(spof) > 0 else "None",
                 "red" if len(spof) > 0 else "green")

    st.markdown("")

    # -------------------------------------------------------------------------
    # Heatmap Matrix
    # -------------------------------------------------------------------------
    st.markdown('<div class="section-header">Worker Certification Matrix</div>', unsafe_allow_html=True)
    st.caption("A visual overview of certifications. Blue indicates a worker is certified for that station.")
    
    matrix_df = query_to_df("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        RETURN w.name AS Worker, s.station_code AS StationCode, s.station_name AS Station
    """)

    if not matrix_df.empty:
        pivot = matrix_df.pivot_table(
            index=["StationCode", "Station"],
            columns="Worker",
            aggfunc="size",
            fill_value=0,
        )
        pivot = pivot.clip(upper=1)
        pivot = pivot.sort_index()
        pivot = pivot[sorted(pivot.columns)]
        
        y_labels = [f"{idx[0]} - {idx[1]}" for idx in pivot.index]
        
        # Hover text matrix
        hover_text = []
        for s, row in zip(y_labels, pivot.values):
            hover_row = []
            for w, val in zip(pivot.columns, row):
                status = "Certified" if val == 1 else "Uncertified"
                hover_row.append(f"Worker: {w}<br>Station: {s}<br>Status: {status}")
            hover_text.append(hover_row)
            
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=y_labels,
            colorscale=[[0, "rgba(255, 255, 255, 0.05)"], [1, "#3b82f6"]],
            showscale=False,
            xgap=2, ygap=2,
            hoverinfo="text",
            text=hover_text
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(t=10, b=80, l=180, r=20),
            xaxis=dict(tickangle=-45, side="bottom"),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig, use_container_width=True)

    # Detailed Coverage Table (satisfies the "table" requirement cleanly without horizontal scroll issues)
    st.markdown('<div class="section-header">Station Coverage Details</div>', unsafe_allow_html=True)
    display_df = df.copy()
    display_df["Workers"] = display_df["Workers"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else x
    )

    def highlight_spof(row):
        if row["WorkerCount"] <= 1:
            return ["background-color: rgba(239,68,68,0.15)"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_df.style.apply(highlight_spof, axis=1),
        use_container_width=True, hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Load Forecast
# ══════════════════════════════════════════════════════════════════════════════

def page_load_forecast():
    st.header("Load Forecast (Week 9)")
    st.caption("Predictive analysis identifying where production load will exceed station capacity in the coming week.")

    # 1. Get Historical Load + Variance
    load_df = query_to_df("""
        MATCH (s:Station)-[l:LOADED_IN]->(w:Week)
        RETURN s.station_code AS StationCode,
               s.station_name AS Station,
               toInteger(substring(w.week_id, 1)) AS WeekNum,
               l.total_actual AS ActualLoad,
               l.total_planned AS PlannedLoad,
               CASE WHEN l.total_planned > 0 
                    THEN round((l.total_actual - l.total_planned) / l.total_planned * 100, 1) 
                    ELSE 0.0 END AS VariancePct
        ORDER BY StationCode, WeekNum
    """)
    
    # 2. Get Graph-Aware Capacity
    cap_df = query_to_df("""
        MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
        WITH w, s
        MATCH (w)-[:CAN_COVER]->(all_s:Station)
        WITH w, s, count(all_s) AS total_coverage
        RETURN s.station_code AS StationCode,
               s.station_name AS Station,
               sum(toFloat(w.hours_per_week) / total_coverage) AS Capacity
        ORDER BY StationCode
    """)

    if load_df.empty or cap_df.empty:
        st.warning("No data found. Ensure the graph is seeded.")
        return
        
    load_df["Load"] = load_df["ActualLoad"].fillna(load_df["PlannedLoad"])

    # 3. Process Forecasts
    forecasts = []
    
    # Iterate over all known stations from both load and capacity queries
    all_stations = sorted(list(set(load_df["StationCode"]).union(set(cap_df["StationCode"]))))
    
    for station_code in all_stations:
        station_data = load_df[load_df["StationCode"] == station_code]
        cap_series = cap_df[cap_df["StationCode"] == station_code]
        
        station_name = station_data["Station"].iloc[0] if not station_data.empty else cap_series["Station"].iloc[0]
        cap = cap_series["Capacity"].iloc[0] if not cap_series.empty else 0.0
        
        if len(station_data) > 1:
            X = sm.add_constant(station_data["WeekNum"])
            model = sm.OLS(station_data["Load"], X).fit()
            pred_9 = model.predict([1, 9])[0]
        elif len(station_data) == 1:
            pred_9 = station_data["Load"].iloc[0]
        else:
            pred_9 = 0
            
        pred_9 = max(0, pred_9)
        
        util_pct = (pred_9 / cap * 100) if cap > 0 else (float('inf') if pred_9 > 0 else 0)
            
        forecasts.append({
            "StationCode": station_code,
            "Station": station_name,
            "Week9_Forecast": pred_9,
            "Capacity": cap,
            "UtilPct": util_pct
        })
        
    forecast_df = pd.DataFrame(forecasts)
    forecast_df["Status"] = forecast_df.apply(lambda x: "OVERLOAD" if x["Week9_Forecast"] > x["Capacity"] else "SAFE", axis=1)
    
    # KPIs
    overloaded_count = len(forecast_df[forecast_df["Status"] == "OVERLOAD"])
    avg_util = forecast_df["UtilPct"].mean()

    c1, c2, c3 = st.columns(3)
    with c1: kpi("Average Factory Utilization", f"{avg_util:.1f}%", "projected for week 9", "blue")
    with c2: kpi("Critical Stations", overloaded_count, "over capacity in week 9", "red" if overloaded_count > 0 else "green")
    with c3: kpi("Highest Load", f"{forecast_df['UtilPct'].max():.0f}%", f"at {forecast_df.loc[forecast_df['UtilPct'].idxmax(), 'StationCode']}", "amber")

    st.markdown('<div class="section-header">Global Forecast: Load vs. Capacity (Week 9)</div>', unsafe_allow_html=True)
    
    # Global comparison chart
    fig_global = go.Figure()
    fig_global.add_trace(go.Bar(
        name="Projected Load", x=forecast_df["StationCode"], y=forecast_df["Week9_Forecast"],
        marker_color=["#ef4444" if s == "OVERLOAD" else "#3b82f6" for s in forecast_df["Status"]],
        hovertemplate="Load: %{y:.1f}h<extra></extra>"
    ))
    fig_global.add_trace(go.Scatter(
        name="Station Capacity", x=forecast_df["StationCode"], y=forecast_df["Capacity"],
        mode="markers", marker=dict(color="#ffffff", size=12, symbol="line-ew-open", line=dict(width=3)),
        hovertemplate="Capacity: %{y:.1f}h<extra></extra>"
    ))
    fig_global.update_layout(
        template="plotly_dark", height=350, margin=dict(t=20, b=40, l=10, r=10),
        xaxis_title="Station Code", yaxis_title="Hours", barmode="group",
        legend=dict(title="Metric", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_global, use_container_width=True)

    # 4. Station Deep-Dive
    st.markdown('<div class="section-header">Station Deep-Dive</div>', unsafe_allow_html=True)
    
    selected_st = st.selectbox("Select a station to see trend details", 
                              options=forecast_df["StationCode"].tolist(),
                              format_func=lambda x: f"{x} - {forecast_df[forecast_df['StationCode']==x]['Station'].iloc[0]}")
    
    sd = forecast_df[forecast_df["StationCode"] == selected_st].iloc[0]
    hist = load_df[load_df["StationCode"] == selected_st]
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        fig_detail = go.Figure()
        
        # OLS logic
        if len(hist) > 1:
            X = sm.add_constant(hist["WeekNum"])
            model = sm.OLS(hist["Load"], X).fit()
            x_range = list(range(1, 10))
            y_range = model.predict(sm.add_constant(x_range))
            preds = model.get_prediction(sm.add_constant(x_range))
            ci = preds.conf_int(alpha=0.1) # 90% confidence
            y_lower, y_upper = ci[:, 0], ci[:, 1]
            
            # Confidence Band
            fig_detail.add_trace(go.Scatter(
                x=x_range + x_range[::-1], y=list(y_upper) + list(y_lower)[::-1],
                fill='toself', fillcolor='rgba(59, 130, 246, 0.1)',
                line=dict(color='rgba(255,255,255,0)'), name="90% Confidence Interval"
            ))
            # Trend
            fig_detail.add_trace(go.Scatter(x=x_range, y=y_range, mode="lines", 
                                          line=dict(color="#3b82f6", dash="dash"), name="Trendline"))
        
        # Capacity line
        fig_detail.add_hline(y=sd["Capacity"], line_dash="dot", line_color="#ef4444", 
                            annotation_text="CAPACITY LIMIT", annotation_position="top left")
        
        # Historical
        fig_detail.add_trace(go.Scatter(x=hist["WeekNum"], y=hist["Load"], mode="lines+markers", 
                                      marker=dict(color="#ffffff", size=10), name="Historical Load"))
        
        # Week 9 Target Point
        fig_detail.add_trace(go.Scatter(x=[9], y=[sd["Week9_Forecast"]], mode="markers", 
                                      marker=dict(color="#ef4444" if sd["Status"]=="OVERLOAD" else "#22c55e", size=14, symbol="star"),
                                      name="W9 Projection"))

        fig_detail.update_layout(
            template="plotly_dark", height=400, title=f"Load Trend Analysis: {selected_st}",
            xaxis=dict(title="Week", tickmode="linear", range=[0.5, 9.5]),
            yaxis=dict(title="Hours"), showlegend=True,
            legend=dict(title="Metric", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_detail, use_container_width=True)
        st.caption("💡 **Note**: The shaded area represents the 90% confidence interval of the OLS prediction, indicating the expected range of variance based on historical data.")

        # Variance Trend Chart
        if not hist.empty and len(hist) > 1:
            fig_var = px.line(hist, x="WeekNum", y="VariancePct", markers=True,
                             title=f"Historical Plan Variance (%): {selected_st}",
                             labels={"VariancePct": "Variance %", "WeekNum": "Week"},
                             template="plotly_dark", height=200)
            fig_var.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
            fig_var.update_traces(line_color="#f59e0b")
            fig_var.update_layout(margin=dict(t=30, b=20, l=10, r=10))
            st.plotly_chart(fig_var, use_container_width=True)
        else:
            st.info("Insufficient data to show variance trend.")

    with c2:
        st.markdown(f"### {sd['Status']}")
        st.write(f"Station **{selected_st}** is projected to reach **{sd['Week9_Forecast']:.1f} hours** in Week 9.")
        st.write(f"Current capacity limit is **{sd['Capacity']:.1f} hours**.")
        
        avg_v = hist["VariancePct"].mean() if not hist.empty else 0.0
        st.metric("Avg Historical Variance", f"{avg_v:+.1f}%", 
                  help="Positive means actual hours consistently exceed planned hours.")
        
        util_color = "red" if sd["UtilPct"] > 100 else "green"
        util_display = f"{sd['UtilPct']:.1f}%" if sd["UtilPct"] != float('inf') else "∞%"
        delta_display = f"{sd['UtilPct']-100:.1f}%" if sd["UtilPct"] > 100 and sd["UtilPct"] != float('inf') else None
        
        st.metric("Projected Utilization", util_display, 
                  delta=delta_display,
                  delta_color="inverse")
        
        if sd["Status"] == "OVERLOAD":
            st.error(f"Action Required: Station will exceed capacity by {sd['Week9_Forecast'] - sd['Capacity']:.1f} hours.")
        else:
            st.success("No immediate capacity action required.")

    # 5. Global Action Recommendations
    overloads = forecast_df[forecast_df["Status"] == "OVERLOAD"]
    healthy = forecast_df[forecast_df["Status"] == "SAFE"].copy()
    healthy["Surplus"] = healthy["Capacity"] - healthy["Week9_Forecast"]
    healthy = healthy[healthy["Surplus"] >= 5].sort_values("Surplus", ascending=False)

    if not overloads.empty:
        st.markdown('<div class="section-header" style="color: #ef4444; margin-top: 3rem;">⚠️ Action Recommendations</div>', unsafe_allow_html=True)
        st.error(f"**{len(overloads)} Stations are projected to exceed capacity in Week 9.** Immediate action is required.")
        
        # Get worker coverage map to make smart, graph-aware recommendations
        coverage_df = query_to_df("""
            MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
            WHERE w.role <> 'Foreman'
            RETURN w.name AS Worker, s.station_code AS StationCode
        """)
        
        for _, row in overloads.iterrows():
            target_station = row["StationCode"]
            deficit = row["Week9_Forecast"] - row["Capacity"]
            suggestion = f"- **{row['Station']} ({target_station}):** Short by **{deficit:.1f} hours**."
            
            # 1. Find workers certified for this overloaded station
            capable_workers = coverage_df[coverage_df["StationCode"] == target_station]["Worker"].unique()
            
            # 2. Find which of these workers are currently at surplus stations
            reassignment_options = []
            for worker in capable_workers:
                # Other stations this worker covers
                other_stations = coverage_df[
                    (coverage_df["Worker"] == worker) & 
                    (coverage_df["StationCode"] != target_station)
                ]["StationCode"].tolist()
                
                # Check if any of these 'other' stations have a surplus
                worker_surplus_stations = healthy[healthy["StationCode"].isin(other_stations)]
                if not worker_surplus_stations.empty:
                    # Sort by highest surplus and take the best one for this worker
                    best_station = worker_surplus_stations.sort_values("Surplus", ascending=False).iloc[0]
                    reassignment_options.append(f"**{worker}** (from {best_station['Station']})")
            
            # 3. Format and display
            if reassignment_options:
                # Show top 3 candidates to keep the UI clean
                suggestion += f" *Suggestion: Reassign {', '.join(reassignment_options[:3])}*"
            else:
                suggestion += f" *No cross-trained line workers available at stations with surplus.*"
                
            st.markdown(suggestion)
    else:
        st.markdown('<div class="section-header" style="color: #22c55e; margin-top: 3rem;">✅ System Healthy</div>', unsafe_allow_html=True)
        st.success("All stations are projected to be safely within capacity limits for Week 9.")

    with st.expander("Full Forecast Data Table"):
        st.dataframe(forecast_df.sort_values("UtilPct", ascending=False), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — Self-Test
# ══════════════════════════════════════════════════════════════════════════════

def run_self_test():
    """Run the 6 automated checks and return a list of (description, passed, points)."""
    driver = get_driver()
    checks = []

    # Check 1: Connection
    try:
        with driver.session() as s:
            s.run("RETURN 1").single()
        checks.append(("Neo4j connected", True, 3))
    except Exception:
        checks.append(("Neo4j connected", False, 3))
        return checks  # can't continue

    with driver.session() as s:
        # Check 2: Node count >= 50
        count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        checks.append((f"{count} nodes (min: 50)", count >= 50, 3))

        # Check 3: Relationship count >= 100
        count = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        checks.append((f"{count} relationships (min: 100)", count >= 100, 3))

        # Check 4: 6+ distinct node labels
        count = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        checks.append((f"{count} node labels (min: 6)", count >= 6, 3))

        # Check 5: 8+ distinct relationship types
        count = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"
        ).single()["c"]
        checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))

        # Check 6: Variance query returns results
        result = s.run("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.project_name AS project, s.station_name AS station,
                   r.planned_hours AS planned, r.actual_hours AS actual
            LIMIT 10
        """)
        rows = [dict(r) for r in result]
        checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))

    return checks


def page_self_test():
    st.header("Self-Test")
    st.caption("Automated verification of graph requirements.")

    if st.button("Run Self-Test", type="primary"):
        with st.spinner("Running checks…"):
            checks = run_self_test()

        total = 0
        max_total = 0

        for desc, passed, pts in checks:
            max_total += pts
            earned = pts if passed else 0
            total += earned
            icon = "PASS" if passed else "FAIL"
            css  = "check-pass" if passed else "check-fail"
            st.markdown(
                f'<span class="{css}">{icon} {desc}</span> — **{earned}/{pts}**',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        color = "check-pass" if total == max_total else "check-fail"
        st.markdown(
            f'<h3 class="{color}">SELF-TEST SCORE: {total}/{max_total}</h3>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Click the button above to run the self-test checks.")


# ══════════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════════

if page == "Project Overview":
    page_project_overview()
elif page == "Station Load":
    page_station_load()
elif page == "Capacity Tracker":
    page_capacity_tracker()
elif page == "Worker Coverage":
    page_worker_coverage()
elif page == "Load Forecast":
    page_load_forecast()
elif page == "Self-Test":
    page_self_test()
