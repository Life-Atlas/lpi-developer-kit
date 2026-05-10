# Factory Graph Dashboard

A Neo4j knowledge graph + Streamlit dashboard for a Swedish steel fabrication company.
Replaces a 46-sheet Excel workbook with an interactive graph-powered dashboard.

## Live Dashboard
https://factory-graph-shourya.streamlit.app/

## Setup

### Requirements
- Python 3.10+
- Neo4j Aura instance (free tier works)

### Install
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

### Configure
Copy .env.example to .env and fill in your Neo4j credentials.

### Seed the graph
    python seed_graph.py

### Run locally
    streamlit run app.py

## Dashboard Pages
- Project Overview — 8 projects with planned vs actual hours and variance
- Station Load — interactive bar chart of hours per station, overloaded weeks highlighted
- Capacity Tracker — weekly capacity vs demand, deficit weeks in red
- Worker Coverage — which workers cover which stations, single points of failure flagged
- Self-Test — automated checks, scores 20/20

## Stack
- Neo4j Aura (graph database)
- Streamlit (dashboard)
- Plotly (interactive charts)
- Python neo4j driver