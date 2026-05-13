# Factory Knowledge Graph Dashboard — Level 6

A **Neo4j knowledge graph** + **Streamlit dashboard** for a Swedish steel fabrication company managing 8 construction projects across 10 production stations.

##  Quick Start

### 1. Prerequisites
- Python 3.10+
- A Neo4j instance (recommended: [Neo4j Aura Free](https://neo4j.io/aura))

### 2. Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 3. Configure credentials
Copy `.env.example` → `.env` and fill in your Neo4j credentials:
```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### 4. Seed the graph (run once)
```bash
python seed_graph.py
```

### 5. Launch the dashboard
```bash
streamlit run app.py
```

##  Dashboard Pages

| Page | Description |
|------|-------------|
| **Project Overview** | All 8 projects with planned/actual hours, variance %, and products |
| **Station Load** | Interactive bar chart — hours per station per week, overloads in red |
| **Capacity Tracker** | Stacked capacity bars + demand line, deficit weeks highlighted |
| **Worker Coverage** | Coverage matrix + SPOF (single-point-of-failure) station detection |
| **Self-Test** | Automated 6-check verification (20 pts) |

## Project Structure

```
l6-factory-dashboard/
├── seed_graph.py        # CSV → Neo4j (idempotent, uses MERGE)
├── app.py               # Streamlit dashboard (5 pages)
├── requirements.txt
├── .env.example
├── README.md
├── DASHBOARD_URL.txt
└── data/
    ├── factory_production.csv
    ├── factory_workers.csv
    └── factory_capacity.csv
```

##  Deployed URL

See `DASHBOARD_URL.txt`.

##  Author

**Touqeer Hamdani** — Level 6 submission, May 2026.
