# Factory Production Knowledge Graph + Dashboard

A Neo4j-powered Streamlit dashboard for analyzing Swedish steel fabrication factory production data.

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Neo4j instance (Aura Free or Docker)

### 2. Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Neo4j

Create `.env` file:
```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

**Get Neo4j Aura Free:** https://neo4j.io/aura

### 4. Seed the Graph

```bash
python seed_graph.py
```

Expected output:
```
🚀 Starting graph seeding...

✓ Constraints created
✓ 8 projects created
✓ 7 products created
✓ 9 stations created
✓ 2 etapps + 3 BOPs created
✓ Production relationships created
✓ Weeks created
✓ Capacity relationships created
✓ Workers and relationships created

✅ Seeding complete! Nodes: 60, Relationships: 156
```

### 5. Run Dashboard

```bash
streamlit run app.py
```

Open http://localhost:8501

## Pages

1. **Project Overview** — All 8 projects with planned/actual hours and variance metrics
2. **Station Load** — Interactive chart of hours per station across weeks, highlights overloaded stations
3. **Capacity Tracker** — Weekly capacity vs demand, deficit highlighting
4. **Worker Coverage** — Matrix showing worker certifications, identifies single points of failure
5. **Self-Test** — Automated graph validation (20 pts)

## Deployment to Streamlit Cloud

### Step 1: Push to GitHub

```bash
git add seed_graph.py app.py requirements.txt .env.example README.md
git commit -m "level-6: Factory Graph Dashboard"
git push origin main
```

### Step 2: Deploy

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repo
4. Choose branch: `main`
5. Set main file: `app.py`
6. Click Deploy

### Step 3: Add Secrets

Once deployed, go to app **Settings → Secrets** and add (TOML format):

```toml
NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
```

### Step 4: Save URL

Once deployed, save your URL:

```bash
echo "https://your-name-factory-dashboard.streamlit.app" > DASHBOARD_URL.txt
```

## Data Files

Located in `challenges/data/` (relative to repo root):
- `factory_production.csv` — 68 rows of production schedule
- `factory_workers.csv` — 13 workers with certifications
- `factory_capacity.csv` — 8 weeks of capacity data

## Graph Schema

**Nodes:** Project, Product, Station, Worker, Week, Etapp, BOP, Capacity

**Relationships:**
- `Project -[:PRODUCES]-> Product` {qty, unit_factor}
- `Project -[:SCHEDULED_AT]-> Station` {planned_hours, actual_hours, week}
- `Project -[:PART_OF]-> Etapp`
- `Worker -[:WORKS_AT]-> Station`
- `Worker -[:CAN_COVER]-> Station` {certifications}
- `Week -[:HAS_CAPACITY]-> Capacity` {own_staff, hired_staff, deficit}

See `../level5/schema.md` for complete schema.

## Troubleshooting

### Connection fails
- Check `.env` file exists and credentials are correct
- Verify Neo4j instance is running (Aura console)
- For local Neo4j: ensure Docker container or Neo4j Desktop is running

### No data appears
- Run `python seed_graph.py` again
- Check Neo4j Browser: `MATCH (n) RETURN count(n)` should return 60+

### Streamlit won't start
- Kill existing processes: `lsof -i :8501 | awk '{print $2}' | xargs kill -9`
- Check Python version: `python --version` (needs 3.8+)

### Self-test shows failed checks
- Verify Neo4j has data: `MATCH (n) RETURN count(n)`
- Check relationship names match schema: `MATCH ()-[r]->() RETURN r LIMIT 1`

## Scoring (100 pts)

| Component | Points |
|-----------|--------|
| Self-Test (all 6 checks green) | 20 |
| Project Overview page | 10 |
| Station Load interactive chart | 10 |
| Capacity Tracker page | 10 |
| Worker Coverage matrix | 10 |
| Navigation (tabs/sidebar) | 5 |
| Deployed on Streamlit Cloud | 15 |
| Code quality (no creds, idempotent seed) | 10 |

**Pass: 45+ pts**  
**Strong: 70+ pts**  
**Excellence: 85+ pts**

---

**Deployed Dashboard:** (Add URL here or in DASHBOARD_URL.txt)

See `../level5/` folder for Level 5 answers.
