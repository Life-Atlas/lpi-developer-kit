# 🏭 Factory Graph Dashboard — Level 6

> A Neo4j knowledge graph + Streamlit dashboard built on real production data from a Swedish steel fabrication company. Replaces a 46-sheet Excel workbook with a queryable graph database and an interactive visual dashboard.

**Live Demo →** [https://jf5vhmhr9fwrymrjj2lnkk.streamlit.app/]

---

## What This Does

- Parses **3 CSV files** (8 projects, 9 stations, 13 workers, 8 weeks) into a **Neo4j graph database**
- Exposes the graph through a **4-page Streamlit dashboard** with interactive Plotly charts
- Includes a **Self-Test page** that runs live Cypher checks and auto-scores the graph

---

## Project Structure

```
level6/
├── seed_graph.py       # One-time CSV → Neo4j loader (idempotent, safe to re-run)
├── app.py              # Streamlit dashboard — 5 pages including Self-Test
├── requirements.txt    # Python dependencies
├── .env.example        # Credential template (safe to commit)
├── .env                # Your real credentials (never commit this)
├── DASHBOARD_URL.txt   # Deployed Streamlit URL
└── README.md
```

---

## Setup & Run

### 1. Neo4j Aura (free cloud DB)

1. Go to [console.neo4j.io](https://console.neo4j.io) → create a free instance
2. Save the **URI, username, and password** when shown — shown only once

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
# then edit .env with your actual Neo4j values
```

### 4. Seed the graph

```bash
python seed_graph.py
```

Expected output:
```
=== Seeding Neo4j ===
Creating Project nodes...     8 projects.
Creating Station nodes...     9 stations.
Creating Product nodes...     7 products.
Creating Week nodes...        8 weeks.
Creating Worker nodes...      13 workers.
Creating SCHEDULED_AT...      68 relationships.
...
✅ Graph seeded successfully!
```

Safe to run multiple times — uses `MERGE` throughout, never creates duplicates.

### 5. Run locally

```bash
streamlit run app.py
```

---

## Dashboard Pages

| Page | What it shows |
|------|---------------|
| 📊 **Project Overview** | Planned vs actual hours per project, variance %, drill-down by project |
| 🏗️ **Station Load** | Variance heatmap (station × week), week-by-week bar chart, overrun table |
| 📅 **Capacity Tracker** | Stacked capacity vs demand, deficit/surplus per week, staffing table |
| 👷 **Worker Coverage** | Coverage matrix, single-point-of-failure stations, certifications |
| 🧪 **Self-Test** | 6 live Cypher checks against Neo4j, auto-scored out of 20 |

---

## Graph Schema

### Nodes

| Label | Count | Key Property |
|-------|-------|--------------|
| `Project` | 8 | `id` (P01–P08) |
| `Station` | 9 | `code` (011–021) |
| `Product` | 7 | `type` (IQB, IQP, SB…) |
| `Worker` | 13 | `id` (W01–W13) |
| `Week` | 8 | `id` (w1–w8) |
| `Certification` | varies | `name` |

### Relationships

| Type | From → To | Properties |
|------|-----------|------------|
| `SCHEDULED_AT` | Project → Station | `planned_hours`, `actual_hours`, `week`, `etapp`, `bop` |
| `PRODUCES` | Project → Product | `quantity`, `unit` |
| `ACTIVE_IN` | Project → Week | — |
| `WORKS_AT` | Worker → Station | — |
| `CAN_COVER` | Worker → Station | — |
| `HAS_CERTIFICATION` | Worker → Certification | — |
| `LOADED_IN` | Station → Week | `planned_hours`, `actual_hours` |
| `REPORTS_TO` | Worker → Worker | — |

---

## Key Cypher Queries

**Projects overrunning by >10%:**
```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN p.name, s.name, r.week,
       round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1) AS variance_pct
ORDER BY variance_pct DESC
```

**Single-point-of-failure stations:**
```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
WITH s, collect(w.name) AS workers, count(w) AS cnt
WHERE cnt = 1
RETURN s.name, workers[0] AS only_worker
```

**Deficit weeks:**
```cypher
MATCH (w:Week) WHERE w.deficit < 0
RETURN w.id, w.deficit ORDER BY w.deficit ASC
```