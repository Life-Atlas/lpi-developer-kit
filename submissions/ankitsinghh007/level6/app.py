"""
app.py — Factory Knowledge Graph Dashboard
Author: Ankit Kumar Singh (ankitsinghh007)
Level 6 — LifeAtlas Contributor Program

6 pages: Project Overview, Station Load, Capacity Tracker,
         Worker Coverage, Forecast (Bonus C), Self-Test

ALL data from Neo4j — no CSV reads in this file.

Run: streamlit run app.py
"""

import os, streamlit as st, pandas as pd, numpy as np
import plotly.express as px, plotly.graph_objects as go
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Factory Graph", page_icon="🏭", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
h1,h2,h3{font-family:'IBM Plex Mono',monospace;}
.stMetric label{font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:#8888aa;}
</style>
""", unsafe_allow_html=True)


# ── Neo4j connection ──────────────────────────────────────────

@st.cache_resource
def get_driver():
    try:
        uri = st.secrets["NEO4J_URI"]
        usr = st.secrets["NEO4J_USER"]
        pwd = st.secrets["NEO4J_PASSWORD"]
    except Exception:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        usr = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(usr, pwd))


def q(cypher, **params):
    with get_driver().session() as s:
        return [dict(r) for r in s.run(cypher, **params)]


# ── Sidebar ───────────────────────────────────────────────────

PAGES = ["🏗️ Project Overview","⚙️ Station Load",
         "📊 Capacity Tracker","👷 Worker Coverage",
         "📈 Forecast","🧪 Self-Test"]

with st.sidebar:
    st.markdown("### 🏭 Factory Graph")
    st.caption("ankitsinghh007 · Level 6")
    st.divider()
    page = st.radio("Page", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("All data from Neo4j")


# ─────────────────────────────────────────────────────────────
# PAGE 1 — PROJECT OVERVIEW
# ─────────────────────────────────────────────────────────────

if page == PAGES[0]:
    st.title("🏗️ Project Overview")
    st.caption("8 construction projects — planned vs actual hours and variance")

    rows = q("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH p, sum(r.planned_hours) AS tp, sum(r.actual_hours) AS ta,
             count(DISTINCT s) AS stations
        MATCH (p)-[:PRODUCES]->(pr:Product)
        WITH p, tp, ta, stations, collect(DISTINCT pr.type) AS products
        RETURN p.id AS id, p.name AS name, p.etapp AS etapp,
               tp AS total_planned, ta AS total_actual,
               round((ta-tp)/tp*100,1) AS variance_pct,
               stations, products
        ORDER BY p.id
    """)

    if not rows:
        st.error("No data. Run: python seed_graph.py")
        st.stop()

    df = pd.DataFrame(rows)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Projects", len(df))
    c2.metric("Total Planned", f"{df.total_planned.sum():.0f} h")
    c3.metric("Total Actual",  f"{df.total_actual.sum():.0f} h")
    over = (df.variance_pct > 10).sum()
    c4.metric("Over Budget >10%", int(over))
    st.divider()

    # Planned vs actual bar chart
    fig = go.Figure()
    fig.add_bar(x=df.name, y=df.total_planned, name="Planned", marker_color="#2d5a8e")
    fig.add_bar(x=df.name, y=df.total_actual,  name="Actual",  marker_color="#00d4aa")
    fig.update_layout(barmode="group", xaxis_tickangle=-25, height=380,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#ccccdd", title="Planned vs Actual by Project")
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # Project cards
    for _, r in df.iterrows():
        v = r.variance_pct
        badge = "🔴" if v>10 else ("🟡" if v>0 else "🟢")
        with st.expander(f"{badge} **{r.id}** — {r.name}  |  variance {v:+.1f}%"):
            a,b,c,d = st.columns(4)
            a.metric("Planned",  f"{r.total_planned:.0f} h")
            b.metric("Actual",   f"{r.total_actual:.0f} h")
            c.metric("Variance", f"{v:+.1f}%")
            d.metric("Stations", r.stations)
            st.write(f"**Products:** {', '.join(r.products)}  |  **Etapp:** {r.etapp}")


# ─────────────────────────────────────────────────────────────
# PAGE 2 — STATION LOAD
# ─────────────────────────────────────────────────────────────

elif page == PAGES[1]:
    st.title("⚙️ Station Load")
    st.caption("Actual hours per station × week — red = >10% over plan")

    rows = q("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.code AS code, s.name AS sname, r.week AS week,
               sum(r.planned_hours) AS planned,
               sum(r.actual_hours)  AS actual
        ORDER BY s.code, r.week
    """)

    if not rows:
        st.error("No data."); st.stop()

    df = pd.DataFrame(rows)
    df["label"]    = df["code"] + " " + df["sname"]
    df["variance"] = ((df["actual"] - df["planned"]) / df["planned"] * 100).round(1)

    # Heatmap
    wk = [f"w{i}" for i in range(1,9)]
    pivot = df.pivot_table(index="label", columns="week", values="actual", aggfunc="sum").fillna(0)
    pivot = pivot.reindex(columns=[w for w in wk if w in pivot.columns])

    fig = px.imshow(pivot,
        color_continuous_scale=[[0,"#0f1117"],[0.4,"#1a4a6b"],[0.75,"#e8a020"],[1,"#ff4b4b"]],
        title="Actual Hours Heatmap (station × week)", text_auto=".0f", aspect="auto")
    fig.update_layout(height=440, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#ccccdd")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Overruns — actual > planned by >10%")
    over = df[df["variance"] > 10].sort_values("variance", ascending=False)
    if over.empty:
        st.success("No overruns.")
    else:
        show = over[["code","sname","week","planned","actual","variance"]].copy()
        show.columns = ["Code","Station","Week","Planned h","Actual h","Variance %"]
        # Plain dataframe — no styling library needed
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Total load per station (all weeks)")
    tot = df.groupby("label").agg(planned=("planned","sum"), actual=("actual","sum")).reset_index()
    fig2 = go.Figure()
    fig2.add_bar(x=tot.label, y=tot.planned, name="Planned", marker_color="#2d5a8e")
    fig2.add_bar(x=tot.label, y=tot.actual,  name="Actual",  marker_color="#00d4aa")
    fig2.update_layout(barmode="group", xaxis_tickangle=-30, height=360,
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#ccccdd")
    st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE 3 — CAPACITY TRACKER
# ─────────────────────────────────────────────────────────────

elif page == PAGES[2]:
    st.title("📊 Capacity Tracker")
    st.caption("Weekly capacity vs demand — deficit weeks in red")

    rows = q("""
        MATCH (w:Week)-[r:HAS_CAPACITY]->(c:Capacity)
        RETURN w.id AS week, c.own_hours AS own, c.hired_hours AS hired,
               c.overtime_hours AS ot, c.total_capacity AS cap,
               c.total_planned AS planned, c.deficit AS deficit,
               c.own_staff AS own_staff, c.hired_staff AS hired_staff
        ORDER BY w.id
    """)

    if not rows:
        st.error("No capacity data."); st.stop()

    df = pd.DataFrame(rows)
    def_wks = df[df.deficit < 0]

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Deficit Weeks",  len(def_wks))
    c2.metric("Surplus Weeks",  len(df) - len(def_wks))
    c3.metric("Total Deficit",  f"{def_wks.deficit.sum():.0f} h")
    worst = df.loc[df.deficit.idxmin()]
    c4.metric("Worst Week", worst["week"], delta=f"{worst.deficit:.0f} h", delta_color="inverse")
    st.divider()

    # Stacked bar + demand line
    fig = go.Figure()
    fig.add_bar(x=df.week, y=df.own,    name="Own Staff",   marker_color="#2d5a8e")
    fig.add_bar(x=df.week, y=df.hired,  name="Hired Staff", marker_color="#1a6b3c")
    fig.add_bar(x=df.week, y=df.ot,     name="Overtime",    marker_color="#e8a020")
    fig.add_scatter(x=df.week, y=df.planned, mode="lines+markers",
                    name="Demand", line=dict(color="#ff4b4b", width=2.5, dash="dash"),
                    marker=dict(size=9))
    fig.update_layout(barmode="stack", title="Capacity vs Demand by Week",
                      height=400, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#ccccdd")
    st.plotly_chart(fig, use_container_width=True)

    # Deficit bar
    colors = ["#ff4b4b" if d < 0 else "#00d4aa" for d in df.deficit]
    fig2 = go.Figure(go.Bar(x=df.week, y=df.deficit, marker_color=colors,
                             text=[f"{d:+.0f}h" for d in df.deficit],
                             textposition="outside"))
    fig2.add_hline(y=0, line_color="#555577", line_dash="dot")
    fig2.update_layout(title="Deficit / Surplus per Week", height=300,
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#ccccdd")
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    df["Status"] = df.deficit.apply(lambda d: "🔴 Deficit" if d<0 else "🟢 Surplus")
    show = df[["week","own_staff","hired_staff","own","hired","ot","cap","planned","deficit","Status"]]
    show.columns = ["Week","Own","Hired","Own h","Hired h","OT h","Capacity","Planned","Deficit","Status"]
    st.dataframe(show, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────
# PAGE 4 — WORKER COVERAGE
# ─────────────────────────────────────────────────────────────

elif page == PAGES[3]:
    st.title("👷 Worker Coverage")
    st.caption("Coverage matrix — single-point-of-failure stations flagged")

    workers = q("""
        MATCH (w:Worker)
        OPTIONAL MATCH (w)-[:WORKS_AT]->(ps:Station)
        OPTIONAL MATCH (w)-[:CAN_COVER]->(cs:Station)
        WITH w, collect(DISTINCT ps.code) AS primary_s,
                collect(DISTINCT cs.code) AS cover_s
        RETURN w.id AS id, w.name AS name, w.role AS role,
               w.type AS wtype, w.hours_per_week AS hpw,
               primary_s, cover_s
        ORDER BY w.id
    """)

    stations = q("""
        MATCH (s:Station)
        OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
        WITH s, count(w) AS cover_count
        RETURN s.code AS code, s.name AS sname, cover_count
        ORDER BY s.code
    """)

    if not workers or not stations:
        st.error("No data."); st.stop()

    df_w = pd.DataFrame(workers)
    df_s = pd.DataFrame(stations)

    spf = df_s[df_s.cover_count <= 1]
    if not spf.empty:
        st.warning(f"⚠️ Single Point of Failure: "
                   f"{', '.join(spf.code + ' ' + spf.sname)}")
    st.divider()

    all_codes = sorted(df_s.code.unique())
    matrix = []
    for _, w in df_w.iterrows():
        row = {"Worker": w["name"], "Role": w["role"], "Type": w.wtype}
        for sc in all_codes:
            if sc in w.primary_s: row[sc] = "PRIMARY"
            elif sc in w.cover_s: row[sc] = "COVER"
            else:                 row[sc] = ""
        matrix.append(row)

    df_m = pd.DataFrame(matrix)

    st.subheader("Coverage Matrix")
    st.caption("PRIMARY = main station  |  COVER = can substitute  |  blank = not assigned")
    # Plain dataframe — works on all pandas/streamlit versions
    st.dataframe(df_m, use_container_width=True, hide_index=True)
    st.divider()

    fig = px.bar(df_s, x="code", y="cover_count",
                 color="cover_count",
                 color_continuous_scale=[[0,"#ff4b4b"],[0.3,"#e8a020"],[1,"#00d4aa"]],
                 title="Workers Who Can Cover Each Station", text="cover_count",
                 labels={"code":"Station","cover_count":"# Workers"})
    fig.add_hline(y=1, line_color="#ff4b4b", line_dash="dot",
                  annotation_text="SPF threshold")
    fig.update_layout(height=360, showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#ccccdd")
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE 5 — FORECAST (Bonus C)
# ─────────────────────────────────────────────────────────────

elif page == PAGES[4]:
    st.title("📈 Week 9 Forecast")
    st.caption("Bonus C — linear extrapolation from 8 weeks of actual station load")

    rows = q("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        RETURN s.code AS code, s.name AS sname,
               r.week AS week, sum(r.actual_hours) AS actual
        ORDER BY s.code, r.week
    """)

    if not rows:
        st.error("No data."); st.stop()

    df = pd.DataFrame(rows)
    df["wnum"] = df.week.str.replace("w","").astype(int)

    forecasts = []
    for sc in df.code.unique():
        sdf = df[df.code==sc].sort_values("wnum")
        sname = sdf.sname.iloc[0]
        x = sdf.wnum.values
        y = sdf.actual.values
        slope, intercept = np.polyfit(x, y, 1)
        w9 = max(0.0, slope*9 + intercept)
        resid = y - (slope*x + intercept)
        std   = float(np.std(resid))
        forecasts.append({"code":sc,"sname":sname,"slope":round(slope,2),
                           "w9":round(w9,1),"lower":round(max(0,w9-std),1),
                           "upper":round(w9+std,1),
                           "trend":"📈" if slope>2 else ("📉" if slope<-2 else "➡️")})

    df_f = pd.DataFrame(forecasts).sort_values("w9", ascending=False)
    at_risk = df_f[df_f.w9 > 50]

    c1,c2 = st.columns(2)
    c1.metric("Stations at Risk (>50h forecast)", len(at_risk))
    top = df_f.iloc[0]
    c2.metric("Highest Forecast", f"{top.w9:.0f} h — {top.code}")
    st.divider()

    colors = ["#ff4b4b" if v>50 else ("#e8a020" if v>30 else "#00d4aa")
              for v in df_f.w9]
    fig = go.Figure()
    fig.add_bar(x=df_f.code, y=df_f.w9,
                error_y=dict(type="data",
                             array=(df_f.upper-df_f.w9).tolist(),
                             arrayminus=(df_f.w9-df_f.lower).tolist(),
                             visible=True),
                marker_color=colors,
                text=df_f.w9.apply(lambda v: f"{v:.0f}h"),
                textposition="outside")
    fig.add_hline(y=50, line_color="#ff4b4b", line_dash="dot",
                  annotation_text="Risk threshold")
    fig.update_layout(title="Forecast Station Load — Week 9", height=400,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#ccccdd")
    st.plotly_chart(fig, use_container_width=True)

    show = df_f[["code","sname","slope","w9","lower","upper","trend"]].copy()
    show.columns = ["Code","Station","Slope h/wk","W9 Forecast","Lower","Upper","Trend"]
    st.dataframe(show, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Historical trends + projection to week 9")
    fig2 = go.Figure()
    palette = px.colors.qualitative.Set2
    for i, sc in enumerate(df.code.unique()):
        sdf = df[df.code==sc].sort_values("wnum")
        col = palette[i % len(palette)]
        sn  = sdf.sname.iloc[0]
        fig2.add_scatter(x=sdf.wnum, y=sdf.actual, mode="lines+markers",
                         name=f"{sc} {sn}", line=dict(color=col))
        xs   = list(sdf.wnum) + [9]
        slp, icp = np.polyfit(sdf.wnum, sdf.actual, 1)
        ys   = [slp*xi + icp for xi in xs]
        fig2.add_scatter(x=xs, y=ys, mode="lines", showlegend=False,
                         line=dict(color=col, dash="dot", width=1))

    fig2.add_vline(x=8.5, line_dash="dash", line_color="#555577",
                   annotation_text="w9 →")
    fig2.update_layout(
        xaxis=dict(tickvals=list(range(1,10)),
                   ticktext=[f"w{i}" for i in range(1,10)]),
        title="Station load trends (actual + w9 projection)",
        height=450, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font_color="#ccccdd")
    st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE 6 — SELF-TEST
# ─────────────────────────────────────────────────────────────

elif page == PAGES[5]:
    st.title("🧪 Self-Test")
    st.caption("6 automated checks against Neo4j — as specified in the Level 6 brief")

    def run_self_test(driver):
        checks = []
        try:
            with driver.session() as s:
                s.run("RETURN 1")
            checks.append(("Neo4j connected", True, 3))
        except Exception as e:
            checks.append((f"Neo4j connection failed: {e}", False, 3))
            return checks

        with driver.session() as s:
            c = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            checks.append((f"{c} nodes (min: 50)", c >= 50, 3))

            c = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            checks.append((f"{c} relationships (min: 100)", c >= 100, 3))

            c = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
            checks.append((f"{c} node labels (min: 6)", c >= 6, 3))

            c = s.run("CALL db.relationshipTypes() YIELD relationshipType "
                      "RETURN count(relationshipType) AS c").single()["c"]
            checks.append((f"{c} relationship types (min: 8)", c >= 8, 3))

            rows = [dict(r) for r in s.run("""
                MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
                WHERE r.actual_hours > r.planned_hours * 1.1
                RETURN p.name AS project, s.name AS station,
                       r.planned_hours AS planned, r.actual_hours AS actual
                LIMIT 10
            """)]
            checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))

        return checks

    if st.button("▶  Run Self-Test", type="primary", use_container_width=True):
        with st.spinner("Running checks..."):
            try:
                driver = get_driver()
                checks = run_self_test(driver)
            except Exception as e:
                st.error(f"Cannot connect: {e}"); st.stop()

        st.divider()
        total_pts  = 0
        total_max  = sum(c[2] for c in checks)

        for label, passed, pts in checks:
            icon = "✅" if passed else "❌"
            score = f"{pts}/{pts}" if passed else f"0/{pts}"
            st.markdown(f"`{icon} {label:<46} {score}`")
            if passed:
                total_pts += pts

        st.divider()
        pct = int(total_pts / total_max * 100)
        if total_pts == total_max:
            st.success(f"### SELF-TEST SCORE: {total_pts}/{total_max}  ✅  All checks passed!")
        else:
            st.warning(f"### SELF-TEST SCORE: {total_pts}/{total_max}  ({pct}%)")

        # Show graph stats
        st.divider()
        st.subheader("Graph contents")
        try:
            with get_driver().session() as s:
                labels = [r["label"] for r in
                          s.run("CALL db.labels() YIELD label RETURN label ORDER BY label")]
                rels   = [r["relationshipType"] for r in
                          s.run("CALL db.relationshipTypes() YIELD relationshipType "
                                "RETURN relationshipType ORDER BY relationshipType")]
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Node labels**")
                for l in labels: st.write(f"  `{l}`")
            with c2:
                st.write("**Relationship types**")
                for r in rels:   st.write(f"  `{r}`")
        except Exception:
            pass

    else:
        st.info("Click **Run Self-Test** to validate the graph.")
        st.markdown("""
| Check | Points |
|-------|--------|
| Neo4j connected | 3 |
| Node count ≥ 50 | 3 |
| Relationship count ≥ 100 | 3 |
| 6+ node labels | 3 |
| 8+ relationship types | 3 |
| Variance query returns results | 5 |
| **Total** | **20** |
        """)
