# Level 6 — Build It: Factory Graph + Dashboard

**Type:** Python build → deployed Streamlit app  
**Deadline:** Tuesday May 13, 2026 23:59 UTC  
**Submission:** PR to `lpi-developer-kit` → `submissions/<your-github-username>/level6/`  
**PR title:** `level-6: Your Name`  
**Time:** 6-10 hours over the weekend  
**Scoring:** We visit your deployed URL and click "Self-Test"

---

## Why This Matters

After this challenge, you start real stream work (May 16). The skills here are non-negotiable:
- **Neo4j** → every stream uses knowledge graphs (matching, factory data, datacenter relationships)
- **Streamlit** → VSAB team builds the client dashboard in Streamlit
- **Deployment** → if you can't ship to a URL, you can't contribute to a team

This is your audition. Ship it.

---

## The Mission

A Swedish steel fabrication company manages 8 construction projects across 9 production stations in a 46-sheet Excel workbook. Your job: turn their CSV data into a **Neo4j knowledge graph** and build a **Streamlit dashboard** that makes the data useful.

One deployment. One URL. We visit it, we see your work, we see your score.

---

## Setup

### Neo4j (pick one)

| Option | Best for | Setup |
|--------|----------|-------|
| **Neo4j Aura Free** | Everyone (recommended) | [neo4j.io/aura](https://neo4j.io/aura) → Free instance |
| **Neo4j Desktop** | Slow internet | [neo4j.com/download](https://neo4j.com/download) → Local |
| **Docker** | If you know Docker | `docker run -p7474:7474 -p7687:7687 neo4j:5` |

Save creds in `.env` — **never commit this file.**

### Python
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install streamlit neo4j python-dotenv pandas plotly
```

### Data
Copy the 3 CSV files from `challenges/data/` into your project:
- `factory_production.csv` — 68 rows: 8 projects × stations × weeks (planned vs actual hours)
- `factory_workers.csv` — 13 workers with stations, certifications, coverage
- `factory_capacity.csv` — 8 weeks of workforce capacity vs demand

---

## What You Build

### 1. `seed_graph.py` — Populate the Graph (20 pts)

Standalone script. Run once, graph is ready.

```bash
python seed_graph.py
```

Must:
- Connect to your Neo4j instance
- Create uniqueness constraints
- Parse all 3 CSVs into nodes and relationships
- Be **idempotent** (use `MERGE`, not `CREATE` — safe to run twice)

**Minimum graph:**

| Node Label | Source | Min Count |
|------------|--------|-----------|
| Project | production.csv → project_id/name | 8 |
| Product | production.csv → product_type | 7 (IQB, IQP, SB, SD, SP, SR, HSQ) |
| Station | production.csv → station_code/name | 9 |
| Worker | workers.csv | 13 |
| Week | production/capacity.csv | 8 |
| Etapp | production.csv → etapp | 2+ |

Minimum relationships: 8 types, 100+ total. Examples:
- `(Project)-[:PRODUCES {qty, unit_factor}]->(Product)`
- `(Project)-[:SCHEDULED_AT {week, planned_hours, actual_hours}]->(Station)`
- `(Worker)-[:WORKS_AT]->(Station)`
- `(Worker)-[:CAN_COVER]->(Station)`
- `(Week)-[:HAS_CAPACITY {own, hired, overtime, deficit}]->()`

You decide the exact schema. Q5 from Level 5 is your blueprint.

### 2. `app.py` — Streamlit Dashboard (45 pts)

Your main deliverable. Must have **4+ pages/tabs**:

#### Page 1: Project Overview (10 pts)
Show all 8 projects with key metrics. For each project: total planned hours, total actual hours, variance %, products involved.

#### Page 2: Station Load (10 pts)
Visualize hours per station across weeks. Must use an **interactive chart** (Plotly recommended). Highlight stations where actual > planned.

#### Page 3: Capacity Tracker (10 pts)
Show weekly capacity (own + hired + overtime) vs total planned demand. Color-code deficit weeks red.

#### Page 4: Worker Coverage (10 pts)
Matrix or table showing which workers can cover which stations. Highlight single-point-of-failure stations (only 1 worker certified).

#### Navigation (5 pts)
Sidebar or tabs. User can switch between pages without reloading.

**All data must come from Neo4j queries, not raw CSV reads.** This proves the graph is actually useful.

### 3. Self-Test Page (20 pts)

Add a page called **"Self-Test"** to your Streamlit app. This page runs automated checks and displays your score.

The self-test must check:

```
CHECK 1 (3 pts): Neo4j connection alive
CHECK 2 (3 pts): Node count >= 50
CHECK 3 (3 pts): Relationship count >= 100
CHECK 4 (3 pts): 6+ distinct node labels
CHECK 5 (3 pts): 8+ distinct relationship types
CHECK 6 (5 pts): Query "projects with variance > 10%" returns results
```

Display as a **green/red checklist** with total score. Example:

```
✅ Neo4j connected                    3/3
✅ 87 nodes (min: 50)                 3/3
✅ 156 relationships (min: 100)       3/3
✅ 7 node labels (min: 6)             3/3
✅ 9 relationship types (min: 8)      3/3
✅ Variance query: 5 results          5/5
─────────────────────────────────────
SELF-TEST SCORE: 20/20
```

Here's the check code to include in your self-test page:

```python
def run_self_test(driver):
    checks = []
    
    # Check 1: Connection
    try:
        with driver.session() as s:
            s.run("RETURN 1")
        checks.append(("Neo4j connected", True, 3))
    except:
        checks.append(("Neo4j connected", False, 3))
        return checks  # Can't continue
    
    with driver.session() as s:
        # Check 2: Node count
        result = s.run("MATCH (n) RETURN count(n) AS c").single()
        count = result["c"]
        checks.append((f"{count} nodes (min: 50)", count >= 50, 3))
        
        # Check 3: Relationship count
        result = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
        count = result["c"]
        checks.append((f"{count} relationships (min: 100)", count >= 100, 3))
        
        # Check 4: Node labels
        result = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()
        count = result["c"]
        checks.append((f"{count} node labels (min: 6)", count >= 6, 3))
        
        # Check 5: Relationship types
        result = s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()
        count = result["c"]
        checks.append((f"{count} relationship types (min: 8)", count >= 8, 3))
        
        # Check 6: Variance query
        result = s.run("""
            MATCH (p:Project)-[r]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            RETURN p.name AS project, s.name AS station,
                   r.planned_hours AS planned, r.actual_hours AS actual
            LIMIT 10
        """)
        rows = [dict(r) for r in result]
        checks.append((f"Variance query: {len(rows)} results", len(rows) > 0, 5))
    
    return checks
```

**Adapt the Cypher to match YOUR schema.** The relationship/property names must match what your `seed_graph.py` creates.

### 4. Deploy on Streamlit Cloud (15 pts)

1. Push your code to a GitHub repo (your fork or a new repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → Deploy
4. Add Neo4j secrets in **Settings → Secrets** (TOML format):
   ```toml
   NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your-password"
   ```
5. Save your deployed URL in `DASHBOARD_URL.txt`

---

## Submission Structure

```
submissions/<your-github-username>/level6/
├── seed_graph.py        # CSV → Neo4j (run once)
├── app.py               # Streamlit dashboard + self-test
├── requirements.txt     # streamlit neo4j python-dotenv pandas plotly
├── .env.example         # Template (no real creds!)
├── README.md            # How to run + deployed URL
└── DASHBOARD_URL.txt    # One line: https://your-app.streamlit.app
```

---

## How We Score You

1. **Visit your `DASHBOARD_URL.txt`** (30 seconds)
2. **Click "Self-Test" page** → read the score (20 pts auto)
3. **Browse dashboard pages** → score quality (45 pts)
4. **Glance at code** in PR → no creds, clean, README works (15 pts)

| Component | Points | How |
|-----------|--------|-----|
| Self-Test all green | 20 | Auto (we just read your page) |
| Project Overview page | 10 | Visual check |
| Station Load page + interactive chart | 10 | Visual check |
| Capacity Tracker page | 10 | Visual check |
| Worker Coverage page | 10 | Visual check |
| Navigation (sidebar/tabs) | 5 | Visual check |
| Deployed on Streamlit Cloud | 15 | URL loads |
| No creds in code, README, idempotent seed | 15 | Code glance |
| **Total** | **100** | |

**Pass: 45** (deployed + self-test green + 1 page working)  
**Strong: 70+** (all pages + self-test green)  
**Excellence: 85+** (polished, interactive, clean code)

---

## Timeline (starts Friday May 9)

| Day | What you should have |
|-----|---------------------|
| **Fri May 9** | Neo4j Aura instance created, `seed_graph.py` started, first nodes loading |
| **Sat May 10** | Graph populated, verified in Neo4j Browser, first Streamlit page rendering |
| **Sun May 11** | Deploy to Streamlit Cloud (even if ugly — deploy EARLY) |
| **Mon May 12** | 4 pages working, self-test passing, polish charts |
| **Tue May 13** | Final push, verify deployed URL works, submit PR |
| **Tue May 13 23:59 UTC** | **DEADLINE. No extensions.** |

**Deploy on day 3, not day 5.** If you wait until Tuesday to deploy, you'll spend all of Tuesday debugging deployment instead of building features.

---

## Stream Bonus (Optional, +15 pts)

After completing the base challenge, pick ONE bonus aligned to your stream:

### Bonus A: People Graph (Boardy stream)
Model 5 intern profiles as a knowledge graph (we'll provide sample data). Create Person nodes with HAS_SKILL, HAS_INTEREST, and ASSIGNED_TO relationships. Write one Cypher query: "Find two people with complementary skills who aren't on the same team." (+15 pts)

### Bonus B: Spatial Layout (3D stream)
Add a 5th dashboard page showing a factory floor plan (simple rectangles for 9 stations, positioned in a grid). Color-code by load (green/yellow/red). Click a station → show its projects. Any viz approach accepted. (+15 pts)

### Bonus C: Forecast (VSAB/DataPro+ stream)
Add a page that answers: "Given current trajectory, which station will be overloaded in week 9?" Extrapolate from the 8 weeks using simple linear trend. Show forecast on a chart with confidence band. (+15 pts)

---

## Tips

1. **Level 5 Q5 IS your schema.** Don't redesign from scratch.
2. **Neo4j Browser** (built into Aura console) is your best debugging tool. Run queries there first.
3. **Start ugly, ship early.** A working Streamlit app with `st.dataframe()` is better than a beautiful app that crashes.
4. **Plotly Express** is your friend for fast interactive charts: `import plotly.express as px; fig = px.bar(df, x="station", y="hours")`
5. **Streamlit secrets** work differently from `.env`. Read: [docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
6. **If Aura signup is slow**, use Neo4j Desktop locally for development, switch to Aura for deployment.

---

## FAQ

**Q: Can I add more pages than 4?**  
A: Yes. Extra pages don't earn extra points (unless it's a Stream Bonus) but show initiative.

**Q: Can I use matplotlib instead of Plotly?**  
A: Plotly preferred (interactive). Matplotlib accepted but costs 2 pts on Station Load.

**Q: What if Streamlit Cloud is slow?**  
A: Free tier cold-starts in 30-60s. Fine. We're patient.

**Q: Can I change the CSV data?**  
A: No. Everyone uses the same data. Your schema and visualization choices are what differentiate you.

**Q: Can I work with someone?**  
A: Discuss approaches, yes. Identical code = both get 0.

**Q: Do I need to do L5 before L6?**  
A: Strongly recommended. L5 Q5 is literally your L6 blueprint. Same deadline so you submit both together.
