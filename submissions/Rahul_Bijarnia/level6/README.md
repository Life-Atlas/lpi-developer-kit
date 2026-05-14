# Level 6 — Factory Graph Dashboard

A Neo4j knowledge graph + Streamlit dashboard for a Swedish steel fabrication company managing 8 projects across 9 production stations.

**Deployed URL:** *(add your Streamlit Cloud URL here and in `DASHBOARD_URL.txt`)*

---

## Quick Start (Local)

### 1. Clone & install
```bash
git clone <your-repo-url>
cd level6
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up credentials
```bash
cp .env.example .env
# Edit .env — add your Neo4j URI, user, password
```

### 3. Seed the graph (run once)
```bash
python seed_graph.py
```
This reads the 3 CSV files and populates Neo4j via `MERGE` (idempotent — safe to re-run).

### 4. Run the dashboard
```bash
streamlit run app.py
```
Open http://localhost:8501

---

## Streamlit Cloud Deployment

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → point at `app.py`
3. Under **Settings → Secrets**, add:
```toml
NEO4J_URI = "neo4j+s://xxxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
```
4. Deploy. Save the URL in `DASHBOARD_URL.txt`.

---

## Graph Schema

**Nodes:** Project, Product, Station, Worker, Week, Etapp, CapacityRecord

**Relationships:**
- `(Project)-[:SCHEDULED_AT {week, planned_hours, actual_hours, variance_pct}]->(Station)`
- `(Project)-[:PRODUCES {quantity, unit_factor}]->(Product)`
- `(Project)-[:IN_ETAPP]->(Etapp)`
- `(Worker)-[:WORKS_AT]->(Station)`
- `(Worker)-[:CAN_COVER]->(Station)`
- `(Week)-[:HAS_CAPACITY {total_capacity, deficit}]->(CapacityRecord)`
- `(Week)-[:NEXT_WEEK]->(Week)`

---

## Dashboard Pages

| Page | What it shows |
|------|--------------|
| 📊 Project Overview | All 8 projects, planned vs actual hours, variance %, products involved |
| ⚙️ Station Load | Interactive bar chart + heatmap of hours per station/week; overloaded stations highlighted |
| 📅 Capacity Tracker | Stacked bar: own/hired/overtime vs demand; deficit weeks in red |
| 👷 Worker Coverage | Worker × Station matrix; SPOF stations flagged |
| 🧪 Self-Test | 6 auto-checks against live Neo4j; shows score out of 20 |

---

## Files

```
level6/
├── seed_graph.py        # CSV → Neo4j (idempotent, MERGE-based)
├── app.py               # Streamlit dashboard (5 pages)
├── requirements.txt
├── .env.example         # Credential template (no real creds)
├── factory_production.csv
├── factory_workers.csv
├── factory_capacity.csv
├── README.md
└── DASHBOARD_URL.txt    # One line: https://your-app.streamlit.app
```