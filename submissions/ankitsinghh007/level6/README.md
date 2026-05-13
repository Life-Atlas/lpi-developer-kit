# Factory Knowledge Graph Dashboard — Level 6

**Author:** Ankit Kumar Singh · [ankitsinghh007](https://github.com/ankitsinghh007)  
**Level:** 6 — LifeAtlas Contributor Program  
**Deployed:** [DASHBOARD_URL.txt](DASHBOARD_URL.txt)

---

## What this is

A Neo4j knowledge graph + Streamlit dashboard built from real Swedish steel fabrication
factory data (8 projects, 9 stations, 13 workers, 8 weeks).

**Dashboard pages:**
1. **Project Overview** — all 8 projects, planned vs actual hours, variance
2. **Station Load** — heatmap and bar charts, overruns highlighted red
3. **Capacity Tracker** — stacked bar with deficit/surplus by week
4. **Worker Coverage** — matrix + single-point-of-failure detection
5. **Forecast (Bonus C)** — week 9 linear extrapolation with confidence band
6. **Self-Test** — 6 automated checks, total score displayed

---

## Setup

### 1. Neo4j — create a free Aura instance

1. Go to [neo4j.io/aura](https://neo4j.io/aura)
2. Create a free instance
3. Save the URI, username, and password

### 2. Environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Neo4j credentials
```

### 3. Copy data files

```bash
mkdir data
# Copy the 3 CSV files into data/
#   data/factory_production.csv
#   data/factory_workers.csv
#   data/factory_capacity.csv
```

### 4. Seed the graph (run once)

```bash
python seed_graph.py
# Output shows node/relationship counts
# Run again safely — uses MERGE everywhere (idempotent)

python seed_graph.py --verify  # check counts without re-seeding
```

### 5. Run the dashboard

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## Deploy to Streamlit Cloud

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → select `app.py`
4. **Settings → Secrets** → add (TOML format):
   ```toml
   NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your-password"
   ```
5. Deploy

---

## Graph Schema

**8 node labels:** Project, Product, Station, Worker, Week, Etapp, Certification, Capacity, Bottleneck

**10 relationship types:**
- `(Project)-[:PRODUCES {quantity, unit_factor}]->(Product)`
- `(Project)-[:SCHEDULED_AT {week, planned_hours, actual_hours, variance_pct}]->(Station)`
- `(Project)-[:IN_ETAPP]->(Etapp)`
- `(Worker)-[:WORKS_AT {primary}]->(Station)`
- `(Worker)-[:CAN_COVER]->(Station)`
- `(Worker)-[:HAS_CERTIFICATION]->(Certification)`
- `(Week)-[:HAS_CAPACITY {deficit, total_capacity}]->(Capacity)`
- `(Product)-[:PROCESSED_AT]->(Station)`
- `(Bottleneck)-[:TRIGGERED_AT]->(Station)`

---

## Security

- `.env` is in `.gitignore` — credentials never in repo
- `seed_graph.py` uses `MERGE` throughout — idempotent, safe to re-run
- Streamlit secrets used for deployment — no hardcoded credentials
