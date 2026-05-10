# Level 6 — Factory Knowledge Graph Dashboard
**Harshit Kumar | GitHub: hrk0503**

A Neo4j knowledge graph + Streamlit dashboard for a Swedish steel fabrication factory's production data.

## Deployed Dashboard

**Live URL:** https://lpi-developer-hrk0503.streamlit.app/

> Self-Test page: Click "🧪 Self-Test" in the sidebar → Run Tests

## What's Built

| File | Purpose |
|------|---------|
| `seed_graph.py` | Populates Neo4j from 3 CSV files (idempotent) |
| `app.py` | Streamlit dashboard with 5 pages |
| `requirements.txt` | Python dependencies |
| `.env.example` | Credential template (no real creds) |

## Dashboard Pages

1. **📊 Project Overview** — All 8 projects: planned vs actual hours, variance %, products involved
2. **🏗️ Station Load** — Heatmap of hours per station × week, highlights overloaded cells
3. **⚡ Capacity Tracker** — Stacked bar chart of own/hired/overtime vs demand, red deficit weeks
4. **👷 Worker Coverage** — Matrix of who covers which stations, highlights single-points-of-failure
5. **🧪 Self-Test** — Automated Neo4j health checks with score /20

## Graph Stats

| Metric | Value |
|--------|-------|
| Node labels | 8 (Project, Product, Station, Worker, Week, Etapp, BOP, Capacity) |
| Relationship types | 9 (SCHEDULED_AT, PRODUCES, WORKS_AT, CAN_COVER, HAS_CAPACITY, IN_WEEK, BELONGS_TO, PART_OF, BOTTLENECK) |
| Total nodes | ~58 |
| Total relationships | 160+ |

## Setup

### Prerequisites
- Python 3.10+
- Neo4j Aura Free account (neo4j.io/aura)
- This repo cloned locally

### Steps

```bash
# 1. Clone and enter the level6 directory
cd submissions/harshit-kumar/level6

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up credentials
cp .env.example .env
# Edit .env with your Neo4j Aura URI, username, and password

# 5. Seed the graph (run once — safe to re-run)
python seed_graph.py

# 6. Launch the dashboard
streamlit run app.py
```

### Streamlit Cloud Secrets (for deployment)

In your Streamlit Cloud app settings, add these secrets (TOML format):

```toml
NEO4J_URI = "neo4j+s://your-aura-id.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
```

## Data Sources

The 3 CSV files come from `challenges/data/` in this repo:
- `factory_production.csv` — 68 rows: 8 projects × stations × weeks (planned vs actual hours)
- `factory_workers.csv` — 13 workers with stations, certifications, roles
- `factory_capacity.csv` — 8 weeks of capacity vs demand

## Graph Schema

See `../level5/schema.md` for the full schema diagram and design rationale.

Key design: `SCHEDULED_AT {week, planned_hours, actual_hours, completed_units}` is the core fact relationship. All other relationships provide structural context.

## How Scoring Works

Visit the deployed URL → click **🧪 Self-Test** → click **Run Tests**.

Expected output:
```
✅ Neo4j connected            3/3
✅ 58 nodes (min: 50)         3/3
✅ 160+ relationships (min: 100)  3/3
✅ 8 node labels (min: 6)     3/3
✅ 9 relationship types (min: 8)  3/3
✅ Variance query: 8 results  5/5
─────────────────────────────────
SELF-TEST SCORE: 20/20
```

## Stream Alignment

This submission is aligned with the **VSAB Dashboard** stream:
- Same graph schema + Streamlit skills used with real client data (46-sheet Excel → graph)
- Plotly for interactive charts
- Neo4j Aura for hosted graph database
- Deployed on Streamlit Cloud (same infrastructure as client delivery)
