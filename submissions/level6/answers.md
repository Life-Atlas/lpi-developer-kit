Level 6 — Factory Graph + Dashboard
Name: Khushi Garg
GitHub: g-khushi
Stream: VSAB Dashboard

 Deployed URL
 https://factory-workforce-dashboard-s383xodqomi3kpmriiesim.streamlit.app

Project Overview
A Swedish steel fabrication company manages 8 construction projects across 9 production stations in a 46-sheet Excel workbook. This project turns their CSV data into a Neo4j knowledge graph and a Streamlit dashboard that makes the data useful and interactive.
What's Built

Neo4j Knowledge Graph — 102 nodes, 279+ relationships across 8 labels and 9 relationship types
5-page Streamlit Dashboard — Project Overview, Station Load, Capacity Tracker, Worker Coverage, Self-Test
All dashboard data comes from Neo4j queries — no raw CSV reads in the app


File Structure
level6/
├── seed_graph.py        # CSV → Neo4j (run once, idempotent)
├── app.py               # Streamlit dashboard + self-test page
├── queries.py           # All Cypher queries (imported by app.py)
├── requirements.txt     # Python dependencies
├── .env.example         # Credentials template (no real creds!)
├── README.md            # This file
└── DASHBOARD_URL.txt    # Deployed Streamlit URL

Graph Schema
Node LabelSourceCountProjectproduction.csv8Productproduction.csv7Stationproduction.csv9Workerworkers.csv14Weekcapacity.csv8Etappproduction.csv2BOPproduction.csv3
RelationshipDescriptionPRODUCESProject → Product (with qty, unit_factor)SCHEDULED_ATProject → Station (per week, planned/actual hours)WORKS_ATWorker → Station (primary assignment)CAN_COVERWorker → Station (certified backup)IN_ETAPPProject → EtappIN_BOPProject → BOPHAS_SCHEDULEWeek → Station (aggregated hours)HAS_CAPACITYWeek → Week (capacity/deficit data)

Dashboard Pages
Page 1: Project Overview

KPI strip: total projects, planned hours, actual hours, over-budget count
Color-coded variance table (green = on budget, yellow = slight overrun, red = >10%)
Grouped bar chart: planned vs actual per project
Weekly hours line chart per project

Page 2: Station Load

Heatmap: actual hours by station × week
Interactive filtered bar chart: planned vs actual per station per week
Overloaded station-weeks table (actual > planned)
Station totals comparison chart

Page 3: Capacity Tracker

KPI strip: deficit weeks, worst deficit, cumulative gap
Stacked bar: own + hired + overtime hours vs planned demand line
Weekly deficit/surplus waterfall chart (red = deficit, green = surplus)
Detailed weekly capacity table

Page 4: Worker Coverage

Coverage matrix heatmap (Worker × Station) with SPOF columns highlighted orange
Single-point-of-failure stations table
Worker directory with roles and certifications
Workers-per-station bar chart with SPOF threshold line

Page 5: Self-Test

Runs 6 automated checks against live Neo4j graph
Displays green/red checklist with points
Shows total score out of 20


 How to Run Locally
1. Prerequisites

Python 3.9+
Neo4j Aura account (free tier) or Neo4j Desktop

2. Clone and Install
bashgit clone https://github.com/g-khushi/Factory-Workforce-Dashboard.git
cd Factory-Workforce-Dashboard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
3. Configure Neo4j Credentials
bashcp .env.example .env
# Edit .env with your Neo4j credentials
Your .env should look like:
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
4. Seed the Graph
bashpython seed_graph.py
Expected output:
 Connected
 Constraints created
 Production nodes/relationships done
 Worker nodes/relationships done
 Capacity data done
── Graph summary ─────────────────────────
  Nodes         : 102
  Relationships : 279
  Labels        : [Project, Station, Worker, Week, Product, Etapp, BOP]
  Rel types     : [PRODUCES, SCHEDULED_AT, WORKS_AT, CAN_COVER, ...]
5. Run the App
bashstreamlit run app.py
Opens at http://localhost:8501

Streamlit Cloud Deployment
Secrets are configured in Streamlit Cloud Settings → Secrets (TOML format):
tomlNEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"

Dependencies
streamlit>=1.35
neo4j>=5.0
python-dotenv>=1.0
pandas>=2.0
plotly>=5.0
