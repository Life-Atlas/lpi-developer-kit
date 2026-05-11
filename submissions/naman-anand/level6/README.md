# Level 6 — Factory Graph Dashboard

A Streamlit dashboard powered by a Neo4j knowledge graph, built from Swedish steel factory production data.

## Live Demo

See `DASHBOARD_URL.txt` for the deployed Streamlit Cloud URL.

## Setup

### 1. Create a Neo4j instance

- **Recommended:** [Neo4j Aura Free](https://neo4j.io/aura)
- Or run locally: `docker run -p7474:7474 -p7687:7687 neo4j:5`

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

### 3. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 4. Seed the graph

```bash
python seed_graph.py
```

This is idempotent — safe to run multiple times (uses `MERGE`).

### 5. Run the dashboard

```bash
streamlit run app.py
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Project Overview** | All 8 projects with planned/actual hours, variance %, and products |
| **Station Load** | Interactive bar chart + heatmap of station hours by week |
| **Capacity Tracker** | Weekly capacity vs demand with deficit weeks flagged red |
| **Worker Coverage** | Coverage matrix + single-point-of-failure station alerts |
| **Self-Test** | Automated 6-check validation (20 pts) |

## Graph Schema

- **8 node labels:** Project, Product, Station, Worker, Week, Capacity, Certification, Etapp, Bottleneck
- **9 relationship types:** PRODUCES, SCHEDULED_AT, WORKS_AT, CAN_COVER, HAS_CERT, COVERS, IN_ETAPP, REQUIRES_CERT, FLAGGED_AS
- **68 production records** across 8 projects, 9 stations, 8 weeks

## Tech Stack

- Python 3.10+
- Streamlit
- Neo4j (Aura Free)
- Plotly
- Pandas
