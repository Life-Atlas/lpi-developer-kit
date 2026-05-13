import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import plotly.express as px

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.set_page_config(
    page_title="Factory Graph Dashboard",
    layout="wide"
)

st.title(" Factory Production Knowledge Graph Dashboard")


def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [dict(record) for record in result]


# -------------------------------
# KPI SECTION
# -------------------------------

st.header("Factory KPIs")

capacity_query = """
MATCH (c:Capacity)
RETURN
sum(c.total_capacity) as capacity,
sum(c.total_planned) as planned,
sum(c.deficit) as deficit
"""

capacity_data = run_query(capacity_query)[0]

col1, col2, col3 = st.columns(3)

col1.metric("Total Capacity Hours", capacity_data["capacity"])
col2.metric("Total Planned Hours", capacity_data["planned"])
col3.metric("Net Deficit", capacity_data["deficit"])
# -------------------------------
# EXECUTIVE SUMMARY
# -------------------------------

st.header("Executive Summary")

summary_query = """
MATCH (p:Project)-[r:GOES_THROUGH]->(s:Station)
WHERE r.actual_hours > r.planned_hours
RETURN
count(DISTINCT p) AS overloaded_projects,
max(r.actual_hours - r.planned_hours) AS max_overrun
"""

summary = run_query(summary_query)[0]

c1, c2 = st.columns(2)

c1.metric(
    "Overloaded Projects",
    summary["overloaded_projects"]
)

c2.metric(
    "Max Overrun Hours",
    summary["max_overrun"]
)

# -------------------------------
# BOTTLENECK ANALYSIS
# -------------------------------

st.header("Station Bottleneck Analysis")

bottleneck_query = """
MATCH (p:Project)-[r:GOES_THROUGH]->(s:Station)
RETURN
s.name as station,
sum(r.planned_hours) as planned,
sum(r.actual_hours) as actual
ORDER BY actual DESC
"""

bottleneck = pd.DataFrame(run_query(bottleneck_query))

fig = px.bar(
    bottleneck,
    x="station",
    y=["planned", "actual"],
    barmode="group",
    title="Planned vs Actual Hours by Station"
)

st.plotly_chart(fig, use_container_width=True)


# -------------------------------
# WORKER COVERAGE
# -------------------------------

st.header("Worker Coverage")

worker_query = """
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN
w.name as worker,
collect(s.code) as stations
"""

workers = run_query(worker_query)

for worker in workers:
    st.write(f"**{worker['worker']}** → {', '.join(worker['stations'])}")

# -------------------------------
# WORKER COVERAGE HEATMAP
# -------------------------------

st.header("Worker Coverage Heatmap")

coverage_query = """
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN
s.code AS station,
count(w) AS worker_count
ORDER BY station
"""

coverage_df = pd.DataFrame(run_query(coverage_query))

if not coverage_df.empty:

    fig = px.bar(
        coverage_df,
        x="station",
        y="worker_count",
        title="Certified Worker Coverage by Station"
    )

    st.plotly_chart(fig, use_container_width=True)

    weak = coverage_df[
        coverage_df["worker_count"] <= 1
    ]

    if not weak.empty:
        st.error("Single Point Failure Stations")
        st.dataframe(weak)

# -------------------------------
# PROJECT OVERLOAD
# -------------------------------

st.header("Overloaded Projects")

overload_query = """
MATCH (p:Project)-[r:GOES_THROUGH]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN
p.name as project,
s.name as station,
r.planned_hours as planned,
r.actual_hours as actual
"""

overloaded = pd.DataFrame(run_query(overload_query))

st.dataframe(overloaded, use_container_width=True)
if not overloaded.empty:

    sample = overloaded.iloc[0]

    st.info(
        f"""
Why flagged?

Project: {sample['project']}
Station: {sample['station']}

Planned Hours: {sample['planned']}
Actual Hours: {sample['actual']}

Reason:
Actual effort exceeded planned threshold by >10%.
Operational overload detected.
"""
    )



# -------------------------------
# RISK ANALYSIS
# -------------------------------

st.header("Operational Risk Analysis")

if not overloaded.empty:

    overloaded["variance_percent"] = (
        (overloaded["actual"] - overloaded["planned"])
        / overloaded["planned"]
    ) * 100

    def classify_risk(v):
        if v >= 30:
            return "HIGH"
        elif v >= 15:
            return "MEDIUM"
        return "LOW"

    overloaded["risk_level"] = overloaded["variance_percent"].apply(classify_risk)

    st.dataframe(
        overloaded[
            ["project", "station", "planned", "actual", "variance_percent", "risk_level"]
        ],
        use_container_width=True
    )

    high_risk_count = len(
        overloaded[overloaded["risk_level"] == "HIGH"]
    )

    medium_risk_count = len(
        overloaded[overloaded["risk_level"] == "MEDIUM"]
    )

    low_risk_count = len(
        overloaded[overloaded["risk_level"] == "LOW"]
    )

    c1, c2, c3 = st.columns(3)

    c1.error(f"HIGH RISK: {high_risk_count}")
    c2.warning(f"MEDIUM RISK: {medium_risk_count}")
    c3.success(f"LOW RISK: {low_risk_count}")


# -------------------------------
# STATION SEARCH TOOL
# -------------------------------

st.header("Station Search")

station_code = st.text_input("Enter Station Code")

if station_code:
    query = f"""
    MATCH (w:Worker)-[:CAN_COVER]->(s:Station {{code: '{station_code}'}})
    RETURN w.name as worker, w.role as role
    """

    results = pd.DataFrame(run_query(query))

    if not results.empty:
        st.dataframe(results)
    else:
        st.warning("No workers found")


driver.close()
