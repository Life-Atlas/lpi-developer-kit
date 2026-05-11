# Factory Knowledge Graph Dashboard

A Swedish steel fabrication company manages 8 construction projects across 9 production stations in a 46-sheet Excel workbook. This project converts the provided factory CSV datasets into a Neo4j knowledge graph and builds a Streamlit dashboard to make the data useful.

## Data Pipeline

```text
factory_production.csv
factory_workers.csv
factory_capacity.csv
        ↓
seed_graph.py
        ↓
Neo4j Knowledge Graph
        ↓
Streamlit Dashboard
```

All dashboard visualizations and analytics are powered through Neo4j Cypher queries instead of directly reading CSV files.

---

## Features

- 📁 Project Overview
  - Planned vs actual hours
  - Variance percentage
  - Project metrics dashboard

- 🏗 Station Load Analysis
  - Interactive Plotly charts
  - Overloaded stations highlighted

- 📈 Capacity Tracker
  - Capacity vs planned demand
  - Deficit weeks highlighted in red

- 👷 Worker Coverage Matrix
  - Worker-to-station mapping
  - Single Point Of Failure (SPOF) detection

- 🧪 Self-Test Dashboard
  - Automated Neo4j validation checks
  - Displays score out of 20

---

## Tech Stack

- Neo4j Aura
- Streamlit
- Plotly
- Pandas
- Python
- python-dotenv

---

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example`:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

Seed the graph database:

```bash
python seed_graph.py
```

Run the Streamlit dashboard:

```bash
streamlit run app.py
```

---

## Dashboard Pages

1. Project Overview
2. Station Load
3. Capacity Tracker
4. Worker Coverage
5. Self-Test

---

## Deployment

The application is deployed using Streamlit Cloud.

The deployed dashboard URL is available in:

```text
DASHBOARD_URL.txt
```