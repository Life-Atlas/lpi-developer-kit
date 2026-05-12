# Level 6: Factory Knowledge Graph Dashboard

This project is a Streamlit dashboard powered by a Neo4j knowledge graph. It replaces a 46-sheet Excel workbook for a steel fabrication company.

## Files Included:
- `seed_graph.py`: Standalone, idempotent script used to parse CSV data and populate the Neo4j Aura cloud database.
- `app.py`: The Streamlit application containing the dashboard UI and Cypher queries. 
- `DASHBOARD_URL.txt`: Contains the public link to the deployed Streamlit Cloud dashboard.

## Dashboard Features:
- Project Overview
- Station Load Visualization
- Capacity Tracker
- Worker Coverage Matrix
- Automated Self-Test Page
