# Level 6 — Factory Knowledge Graph Dashboard

**Shubham Kumar** | Neo4j + Streamlit

Live dashboard: see `DASHBOARD_URL.txt`

> **Access password:** `level-6shubham`
> The dashboard is password-protected to safeguard Life Atlas client data and internal project interests. Use the password above to log in.

---

## What This Is

A Neo4j knowledge graph built from real Swedish steel factory data (8 projects, 9 stations, 13 workers, 8 weeks), visualized as a 5-page Streamlit dashboard.

---

## Setup

### 1. Neo4j Aura

1. Create a free instance at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura)
2. Save the URI, username, and password

### 2. Python environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 3. Credentials

```bash
cp .env.example .env
# Edit .env and fill in your Neo4j URI + password
```

### 4. Seed the graph (run once)

```bash
python seed_graph.py
```

Expected output:
```
✓ Constraints created
✓ Production: 68 entries | 8 projects | 9 stations | 7 products | 8 weeks
✓ Workers: 14 loaded
✓ Capacity: 8 weeks loaded

✅ Graph ready — 131+ nodes | 320+ relationships | 9 node labels | 11 relationship types
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

---

## Dashboard Pages

| Page | What it shows |
|------|--------------|
| Project Overview | Planned vs actual hours, variance %, products and unit output for all 8 projects |
| Station Load | Variance heatmap (stations × weeks) + interactive drill-down bar chart |
| Capacity Tracker | Capacity vs demand line chart, deficit weeks highlighted, workforce breakdown |
| Worker Coverage | SPOF detection — stations with 1 or fewer certified operators flagged |
| Self-Test | 6 automated checks against the live Neo4j graph, score out of 20 |

---

## Graph Schema

- **9 node labels:** Project, ProductionEntry, Station, Product, Week, Worker, Certification, CapacitySnapshot, Etapp
- **11 relationship types:** HAS_ENTRY, AT_STATION, FOR_PRODUCT, IN_WEEK, USES_PRODUCT, IN_ETAPP, HAS_CAPACITY, PRIMARY_AT, CAN_COVER, HAS_CERT, REQUIRES_CERT

---

## Deploying to Streamlit Cloud

1. Push this folder to your GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select `app.py`
3. In **Settings → Secrets**, add:

```toml
NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
```

4. Deploy → copy the URL into `DASHBOARD_URL.txt`
