"""Page 4 — Worker Coverage"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query


def render():
    st.markdown('<div class="page-title">Worker Coverage</div>', unsafe_allow_html=True)
    st.markdown("Station coverage matrix — SPOF (Single Point of Failure) stations highlighted in red.")

    # Coverage query
    coverage_rows = run_query("""
        MATCH (s:Station)
        OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
        WITH s,
             collect(DISTINCT w.name)  AS coverers,
             count(DISTINCT w)         AS coverage_count
        OPTIONAL MATCH (wo:WorkOrder)-[:AT_STATION]->(s)
        OPTIONAL MATCH (p:Project)-[:HAS_WORKORDER]->(wo)
        WITH s, coverers, coverage_count,
             collect(DISTINCT p.project_name) AS active_projects
        RETURN
            s.station_code   AS station_code,
            s.station_name   AS station_name,
            coverers,
            coverage_count,
            active_projects,
            CASE WHEN coverage_count <= 1 THEN true ELSE false END AS is_spof
        ORDER BY coverage_count ASC
    """)

    if not coverage_rows:
        st.error("No data returned. Run seed_graph.py first.")
        return

    df = pd.DataFrame(coverage_rows)

    # ── Summary metrics ────────────────────────────────────────────────────────
    spof_count = int((df["is_spof"] == True).sum())
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="label">Total Stations</div><div class="value">{len(df)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="label">SPOF Stations</div><div class="value" style="color:#f87171">{spof_count}</div></div>', unsafe_allow_html=True)
    with col3:
        avg_cov = round(df["coverage_count"].mean(), 1)
        st.markdown(f'<div class="metric-card"><div class="label">Avg Coverage per Station</div><div class="value">{avg_cov}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Station table ──────────────────────────────────────────────────────────
    st.markdown("**STATION COVERAGE MATRIX**")
    for _, row in df.iterrows():
        spof_html = '<span class="spof-badge">CRITICAL</span>' if row["is_spof"] else '<span class="ok-badge">OK</span>'
        workers_str = ", ".join(row["coverers"]) if row["coverers"] else "—"
        projects_str = ", ".join(row["active_projects"][:4]) if row["active_projects"] else "—"
        cert_count = len(row["coverers"])  # proxy

        with st.expander(f"**{row['station_code']}** — {row['station_name']}   {spof_html}", expanded=row["is_spof"]):
            c1, c2, c3 = st.columns([2, 2, 3])
            with c1:
                st.metric("Coverage Count", int(row["coverage_count"]))
            with c2:
                st.metric("Active Projects", len(row["active_projects"]))
            with c3:
                st.markdown(f"**Workers who can cover:** {workers_str}")
            st.markdown(f"**Dependent projects:** {projects_str}")
            if row["is_spof"]:
                st.error(f"SPOF ALERT: Only {int(row['coverage_count'])} worker(s) cover this station. "
                         f"Projects at risk: {projects_str}")

    st.markdown("---")

    # ── SPOF downstream risk ───────────────────────────────────────────────────
    st.markdown("**SPOF DOWNSTREAM RISK (VIA FEEDS\_INTO)**")
    spof_downstream = run_query("""
        MATCH (s:Station)
        WHERE NOT EXISTS { MATCH (w:Worker)-[:CAN_COVER]->(s) }
           OR 1 >= size([(w:Worker)-[:CAN_COVER]->(s) | w])
        MATCH path = (s)-[:FEEDS_INTO*1..5]->(ds:Station)
        MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)-[:AT_STATION]->(ds)
        RETURN
            s.station_code  AS spof_station,
            s.station_name  AS spof_name,
            ds.station_code AS downstream_station,
            ds.station_name AS downstream_name,
            collect(DISTINCT p.project_name) AS at_risk_projects
        LIMIT 30
    """)

    if spof_downstream:
        df_down = pd.DataFrame(spof_downstream)
        df_down.columns = ["SPOF Station","SPOF Name","Downstream Station","Downstream Name","At-Risk Projects"]
        df_down["At-Risk Projects"] = df_down["At-Risk Projects"].apply(lambda x: ", ".join(x))
        st.dataframe(df_down, use_container_width=True, hide_index=True)
    else:
        st.info("No downstream risk paths found.")

    st.markdown("---")
    st.markdown("**ALL WORKERS**")
    workers_rows = run_query("""
        MATCH (w:Worker)
        OPTIONAL MATCH (w)-[:CERTIFIED_IN]->(c:Certification)
        RETURN
            w.worker_id      AS worker_id,
            w.name           AS name,
            w.role           AS role,
            w.type           AS type,
            w.hours_per_week AS hours_pw,
            collect(c.name)  AS certifications
        ORDER BY w.worker_id
    """)
    wdf = pd.DataFrame(workers_rows)
    wdf["certifications"] = wdf["certifications"].apply(lambda x: ", ".join(x) if x else "—")
    wdf.columns = ["ID","Name","Role","Type","hrs/wk","Certifications"]
    st.dataframe(wdf, use_container_width=True, hide_index=True)
