# Level 6: Factory Flow Graph Dashboard

This dashboard visualizes Project Overview", Station Load, Capacity Tracker and Worker Coverage using a Neo4j graph database backend. It includes a predictive analytics engine (Bonus C) that forecasts Week 9 station load using linear regression.

## Deployed App
[View the Live Dashboard Here](https://factory-flow-graph-dashboard-ananyaa-m.streamlit.app/)

## Local Setup
1. Clone the repository and navigate to this folder.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your Neo4j credentials (see `.env.example`).
4. Seed the database: `python seed_graph.py`
5. Run the dashboard: `streamlit run app.py`