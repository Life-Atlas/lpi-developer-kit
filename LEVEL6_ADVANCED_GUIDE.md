# Level 6 Implementation Guide & Advanced Topics

## Deployment Steps

### Option 1: Streamlit Cloud (Recommended)

1. **Push to GitHub**
   ```bash
   git add seed_graph.py app.py requirements.txt .env.example README.md
   git commit -m "level-6: Factory Graph Dashboard"
   git push origin level6-implementation
   ```

2. **Create Streamlit account**: https://share.streamlit.io

3. **Deploy app**
   - Click "New app"
   - Select your GitHub repo
   - Choose branch: `main`
   - Set main file: `app.py`
   - Click Deploy

4. **Add secrets**
   - Go to app Settings → Secrets
   - Add TOML:
     ```toml
     NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
     NEO4J_USER = "neo4j"
     NEO4J_PASSWORD = "your-actual-password"
     ```

5. **Save URL**
   ```bash
   echo "https://your-name-factory-dashboard.streamlit.app" > DASHBOARD_URL.txt
   ```

### Option 2: Local with Neo4j Aura

```bash
# 1. Create Aura instance at neo4j.io/aura
# 2. Download credentials (save in .env)
# 3. Run:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Seed the graph
python seed_graph.py

# 5. Launch dashboard
streamlit run app.py
```

### Option 3: Docker (Advanced)

```bash
# Run Neo4j locally
docker run -d \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test1234 \
  neo4j:5

# Update .env
echo "NEO4J_URI=neo4j://localhost:7687" > .env
echo "NEO4J_USER=neo4j" >> .env
echo "NEO4J_PASSWORD=test1234" >> .env

# Seed & run
python seed_graph.py
streamlit run app.py
```

---

## Common Issues & Solutions

### Issue 1: "Neo4j connection failed"

**Symptoms:** 
- `Unable to connect to bolt://localhost:7687`
- Neo4j connected: False

**Solutions:**
- Check Neo4j is running: `nc -zv localhost 7687` (local) or visit Aura console
- Verify credentials in `.env`
- For Aura: use `neo4j+s` URI (not `neo4j://`)
- Check firewall/VPN settings

### Issue 2: "Nodes/relationships not loading"

**Symptoms:**
- Self-test shows 0 nodes or 0 relationships
- Dashboard shows empty tables

**Solutions:**
- Run `python seed_graph.py` again
- Check for errors in seed output
- Verify CSV files are at `challenges/data/factory_*.csv`
- Check Neo4j Browser: `MATCH (n) RETURN count(n)`
- If 0 nodes, check constraints didn't fail

### Issue 3: "Streamlit cold start is slow"

**Symptoms:**
- First load takes 30-60 seconds
- Message: "This app is being called from a remote address"

**Solutions:**
- Normal on free tier - be patient
- Use `@st.cache_resource` decorator (already in code)
- Pre-warm the app with a scheduled visit

### Issue 4: "Self-test shows failed queries"

**Symptoms:**
- Check 6 fails: "Variance query: 0 results"
- Relationship properties don't match

**Solutions:**
- Update the variance query to match YOUR schema
- Check property names: `planned_hours` vs `plannedHours` (case matters)
- Verify relationships exist: `MATCH ()-[r:SCHEDULED_AT]->() RETURN r LIMIT 1`

---

## Optimization Tips

### Query Performance

```cypher
// ❌ Slow: Implicit cartesian product
MATCH (p:Project)
MATCH (s:Station)
MATCH (p)-[r:SCHEDULED_AT]->(s)
RETURN p.name, s.code, r.week

// ✅ Fast: Explicit path
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN p.name, s.code, r.week
```

### Caching Strategy

```python
# ❌ Refetches every widget load
results = run_query(driver, query)

# ✅ Cache per session
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_project_overview():
    return run_query(driver, query)

results = get_project_overview()
```

### Charts

```python
# ❌ Slow: matplotlib
import matplotlib.pyplot as plt
plt.bar(df['station'], df['hours'])
plt.show()

# ✅ Fast: Plotly (interactive + Streamlit native)
import plotly.express as px
px.bar(df, x='station', y='hours')
```

---

## Extension Ideas (Bonus Points)

### Bonus A: People Graph (Boardy stream)

Model intern profiles as graph and find complementary pairs:

```python
# Create sample interns
interns = [
    {"id": "I01", "name": "Alice", "skills": ["Python", "Neo4j"], "interests": ["AI", "Data"]},
    {"id": "I02", "name": "Bob", "skills": ["React", "TypeScript"], "interests": ["Frontend"]},
    {"id": "I03", "name": "Carol", "skills": ["Product", "UX"], "interests": ["Design"]},
]

# Load into graph
for intern in interns:
    driver.execute_write(lambda tx, i=intern: tx.run(
        "MERGE (p:Person {id: $id}) SET p.name = $name",
        id=i['id'], name=i['name']
    ))

# Query: Find people with complementary skills
query = """
MATCH (p1:Person)-[:HAS_SKILL]->(s1:Skill),
      (p2:Person)-[:HAS_SKILL]->(s2:Skill)
WHERE p1.id < p2.id  // Avoid duplicates
  AND NOT (p1)-[:ASSIGNED_TO]->()-[:HAS_TEAM_MEMBER]->(p2)
  AND s1 <> s2  // Different skills = complementary
RETURN p1.name, p2.name, 
       collect(distinct s1.name) AS skills1,
       collect(distinct s2.name) AS skills2
LIMIT 5
"""

# Add to Streamlit as 5th bonus page
st.header("🤝 Intern Matching")
# ... display results
```

### Bonus B: Spatial Layout (3D stream)

Create factory floor visualization:

```python
import plotly.graph_objects as go

# Station positions (grid layout)
stations_pos = {
    "011": (0, 0),    # FS IQB - top-left
    "012": (1, 0),    # Förmontering - top-middle
    "013": (2, 0),    # Montering - top-right
    "014": (3, 0),    # Svets - top-far
    "015": (0, 1),    # Montering IQP - middle-left
    "016": (1, 1),    # Gjutning - middle
    "017": (2, 1),    # Målning - middle-right
    "018": (0, 2),    # SB B/F-hall - bottom-left
    "019": (1, 2),    # SP B/F-hall - bottom-middle
    "021": (2, 2),    # SR B/F-hall - bottom-right
}

# Color by load (green/yellow/red)
fig = go.Figure()

for station_code, (x, y) in stations_pos.items():
    # Get load percentage
    load_pct = get_station_load_pct(station_code)  # 0-100
    
    if load_pct < 80:
        color = "green"
    elif load_pct < 100:
        color = "yellow"
    else:
        color = "red"
    
    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode='markers+text',
        marker=dict(size=40, color=color),
        text=f"{station_code}<br>{load_pct:.0f}%",
        textposition="middle center"
    ))

st.plotly_chart(fig, use_container_width=True)
```

### Bonus C: Forecast (VSAB/DataPro+ stream)

Predict future bottlenecks:

```python
import numpy as np
from scipy import stats

def forecast_station_load(station_code, weeks_ahead=1):
    """Linear regression forecast"""
    # Get historical data
    query = f"""
    MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station {{code: '{station_code}'}})
    RETURN r.week, r.actual_hours
    ORDER BY r.week
    """
    
    results = run_query(driver, query)
    df = pd.DataFrame(results)
    df['week_num'] = df['week'].str.extract(r'(\d+)').astype(int)
    
    # Fit line
    x = df['week_num'].values
    y = df['actual_hours'].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Forecast
    future_weeks = np.arange(len(x), len(x) + weeks_ahead)
    forecast = slope * future_weeks + intercept
    
    return forecast, std_err

# Add to dashboard
st.header("🔮 Load Forecast")
forecast_data = {}
for station in get_stations():
    forecast, err = forecast_station_load(station, weeks_ahead=2)
    forecast_data[station] = {"mean": forecast, "std": err}

# Plot with confidence band
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=future_weeks,
    y=forecast_data['011']['mean'],
    fill='tozeroy',
    name='Station 011 Forecast'
))
st.plotly_chart(fig)
```

---

## Advanced Cypher Patterns

### Transitive Relationships

```cypher
// "Find all stations that can be reached through worker coverage"
MATCH (start:Station)<-[:WORKS_AT]-(w:Worker)-[:CAN_COVER]->(end:Station)
RETURN start.name, collect(distinct end.name) AS reachable_stations
```

### Path Finding

```cypher
// "What's the shortest path of projects using same stations?"
MATCH (p1:Project)-[:SCHEDULED_AT]->(s:Station)<-[:SCHEDULED_AT]-(p2:Project)
RETURN p1.name, p2.name, s.name
```

### Aggregation & Statistics

```cypher
// "Average variance per project"
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN p.name,
       ROUND(AVG(r.actual_hours / r.planned_hours - 1) * 100, 1) AS avg_variance_pct,
       COUNT(*) AS station_count
ORDER BY avg_variance_pct DESC
```

### Conditional Logic

```cypher
// "Projects at risk" (actual > planned + has single point of failure)
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours
WITH p, s
MATCH (w:Worker)-[:CAN_COVER]->(s)
WITH p, s, COUNT(w) AS worker_count
WHERE worker_count <= 1
RETURN p.name, s.name, worker_count
```

---

## Testing Checklist

- [ ] seed_graph.py runs without errors
- [ ] Graph has 60+ nodes
- [ ] Graph has 150+ relationships
- [ ] All 8 projects present
- [ ] All 9 stations present
- [ ] All 13 workers present
- [ ] Project Overview page loads
- [ ] Station Load chart is interactive
- [ ] Capacity Tracker shows deficits
- [ ] Worker Coverage matrix displays
- [ ] Self-Test page all checks green
- [ ] Navigation between pages works
- [ ] No `.env` file in git
- [ ] README has setup instructions
- [ ] Deployed URL accessible
- [ ] No Python errors in Streamlit logs

---

## Submission Checklist

```
submissions/<your-github-username>/level6/
├── seed_graph.py                    ✓ Idempotent, uses MERGE
├── app.py                           ✓ 5 pages, all from Neo4j
├── requirements.txt                 ✓ All dependencies listed
├── .env.example                     ✓ Template only, no real creds
├── README.md                        ✓ Setup + deployment instructions
├── DASHBOARD_URL.txt                ✓ One line: https://your-app.streamlit.app
└── (optional) streaming_bonus/      ✓ For +15 pts (if doing bonus)
    ├── people_graph.py
    ├── spatial_layout.py
    └── forecast.py
```

---

## Scoring Breakdown (100 pts)

| Item | Points | Verification |
|------|--------|------|
| Self-Test: All 6 checks green | 20 | Visit "Self-Test" page |
| Project Overview page | 10 | Data loads, metrics visible |
| Station Load interactive chart | 10 | Plotly interactive, overload highlighted |
| Capacity Tracker | 10 | Deficit weeks shown |
| Worker Coverage matrix | 10 | Matrix displays, SPOF flagged |
| Navigation works | 5 | Sidebar/tabs, no reload |
| Deployed on Streamlit Cloud | 15 | URL loads, app runs |
| Code quality | 10 | No creds, README works, idempotent |
| Bonus (optional) | 15 | People/Spatial/Forecast |
| **TOTAL** | **100** | |

**Passing score: 45+ (deployed + self-test + 1 page)**  
**Strong: 70+**  
**Excellence: 85+**

---

## Timeline Recommendation

| Day | Task | Time |
|-----|------|------|
| **Fri May 9** | Setup Neo4j Aura, start seed_graph.py | 1-2 hrs |
| **Sat May 10** | Finish seed_graph.py, verify in Neo4j Browser | 2-3 hrs |
| **Sat May 10 PM** | Build Project Overview page, test queries | 2-3 hrs |
| **Sun May 11** | Build Station Load, Capacity Tracker pages | 3-4 hrs |
| **Sun May 11 PM** | Build Worker Coverage, deploy to Streamlit | 2-3 hrs |
| **Mon May 12** | Self-Test page, polish, fix bugs | 2-3 hrs |
| **Tue May 13** | Final touches, verify URL works, submit PR | 1-2 hrs |

**Total: 15-20 hours** (fits in weekend + Mon)

---

## FAQ

**Q: Can I use SQL instead of Neo4j?**  
A: No. The whole point is to learn graph databases. SQL = 0 pts.

**Q: Can I modify the CSV data?**  
A: No. Everyone uses same data. Modifications = automatic fail.

**Q: Can I skip pages?**  
A: 4 pages required. Skipping = missing 10+ pts each.

**Q: What if I can't deploy to Streamlit Cloud?**  
A: Run locally and record a video + show screenshots. Still pass but lose 15 pts.

**Q: Can I work with a friend?**  
A: Discuss yes. Identical code = both get 0. Individual submissions only.

**Q: Do I need to do L5 first?**  
A: Strongly recommended. L5 Q5 IS your L6 blueprint.

---

**Good luck! 🚀**
