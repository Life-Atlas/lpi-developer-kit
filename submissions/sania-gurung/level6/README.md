# Level 6 — Factory Graph + Dashboard
**Sania Gurung**

A Neo4j knowledge graph + Streamlit dashboard for a Swedish steel fabrication company.  
8 projects · 10 stations · 14 workers · 8 weeks.

## Live Dashboard

See `DASHBOARD_URL.txt`

---

## Local Setup

### 1. Neo4j
Sign up at [neo4j.io/aura](https://neo4j.io/aura) (free tier) and create an instance.  
Save your connection URI, username, and password.

### 2. Python environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Credentials
```bash
cp .env.example .env
# Edit .env and fill in your Neo4j credentials
```

### 4. Seed the graph (run once)
```bash
python seed_graph.py
```
This is idempotent — safe to run multiple times.

### 5. Run the dashboard
```bash
streamlit run app.py
```

---

## Graph Schema

### Node Labels (8)
| Label | Source | Count |
|-------|--------|-------|
| Project | factory_production.csv | 8 |
| Product | factory_production.csv | 7 |
| Station | factory_production.csv | 10 |
| Worker | factory_workers.csv | 14 |
| Week | factory_capacity.csv | 8 |
| Etapp | factory_production.csv | 2 |
| Certification | factory_workers.csv | 23 |
| Bottleneck | derived | 3 |

### Relationship Types (10)
| Relationship | Description |
|---|---|
| `(Project)-[:HAS_PRODUCT]->(Product)` | Project produces this product type |
| `(Project)-[:USES_STATION]->(Station)` | Project is processed at this station |
| `(Project)-[:SCHEDULED_AT {week, planned_hours, actual_hours}]->(Station)` | Per-week production fact |
| `(Project)-[:IN_ETAPP]->(Etapp)` | Project belongs to this construction phase |
| `(Worker)-[:ASSIGNED_TO]->(Station)` | Worker's primary station |
| `(Worker)-[:CAN_COVER]->(Station)` | Worker is qualified to cover this station |
| `(Worker)-[:HAS_CERTIFICATION]->(Certification)` | Worker holds this certification |
| `(Station)-[:REQUIRES_CERT]->(Certification)` | Station mandates this cert |
| `(Product)-[:PROCESSED_AT]->(Station)` | Product type is processed at this station |
| `(Station)-[:HAS_BOTTLENECK]->(Bottleneck)` | Station has chronic overrun (2+ events) |

---

## Dashboard Pages

1. **Project Overview** — 8 projects with planned/actual hours, variance %, and products
2. **Station Load** — Interactive Plotly chart of hours per station per week, overloaded sessions highlighted
3. **Capacity Tracker** — Weekly capacity vs demand, deficit weeks colored red
4. **Worker Coverage** — Coverage matrix, SPOF alerts, bottleneck stations
5. **Self-Test** — Automated 6-check graph verification (20 pts)

---

## Deployment (Streamlit Cloud)

1. Push this directory to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) → connect repo → deploy `app.py`
3. In **Settings → Secrets**, add:
```toml
NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
```
