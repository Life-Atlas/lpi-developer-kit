# Level 5 — Graph Thinking: Answers

**Student:** Sanskriti  
**Deadline:** May 13, 2026  
**Time Spent:** 2-3 hours  

---

## Q1: Model It (20 pts)

### Graph Schema Design

**Node Labels (8):**
1. **Project** — Construction projects (P01-P08)
2. **Product** — Product types (IQB, IQP, SB, SD, SP, SR, HSQ)
3. **Station** — Production stations (011-021)
4. **Worker** — Employees (W01-W14)
5. **Week** — Time periods (w1-w8)
6. **Etapp** — Project phases (ET1, ET2)
7. **BOP** — Bill of process (BOP1, BOP2, BOP3)
8. **Capacity** — Weekly capacity aggregate

**Relationship Types (9+):**

| Type | From | To | Properties | Meaning |
|------|------|-----|-----------|---------|
| `PRODUCES` | Project | Product | `{quantity, unit_factor}` | What products does project produce? |
| `SCHEDULED_AT` | Project | Station | `{week, planned_hours, actual_hours, completed_units}` | When/where is work scheduled? |
| `PART_OF` | Project | Etapp | — | Which phase is project in? |
| `FOLLOWS_BOP` | Project | BOP | — | Which bill-of-process? |
| `WORKS_AT` | Worker | Station | — | Primary work station |
| `CAN_COVER` | Worker | Station | `{certifications}` | Backup capability |
| `IN_STATION` | Station | BOP | — | Which BOP does station belong to? |
| `HAS_CAPACITY` | Week | Capacity | `{own_staff, hired_staff, overtime, total, planned, deficit}` | Weekly capacity |
| `USES_WEEK` | Project | Week | — | Which weeks active? |

---

## Q2: Why Not Just SQL? (20 pts)

### Question
*"Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is on vacation, and which projects would be affected?"*

### SQL Version

```sql
SELECT 
    w.worker_id,
    w.name,
    w.certifications,
    p.project_id,
    p.project_name,
    ps.planned_hours,
    ps.actual_hours
FROM workers w
JOIN worker_certifications wc ON w.worker_id = wc.worker_id
JOIN stations s ON wc.station_code = s.station_code
LEFT JOIN project_stations ps ON s.station_code = ps.station_code
LEFT JOIN projects p ON ps.project_id = p.project_id
WHERE s.station_code = '016'
  AND w.worker_id != 'W07'  -- Per Hansen
  AND wc.is_certified = 1
ORDER BY w.name, p.project_name;
```

**Problems:**
- Multiple JOINs needed to navigate relationships
- Hard to add more conditions (what if X is also on vacation?)
- Implicit relationships hidden in table structure
- Query logic obscures business intent

### Cypher Version (Graph Query)

```cypher
MATCH (perHansen:Worker {name: "Per Hansen"})-[:CAN_COVER]->(station:Station {code: "016"})
WITH station
MATCH (replacement:Worker)-[:CAN_COVER]->(station)
WHERE replacement.name <> "Per Hansen"
MATCH (projects:Project)-[:SCHEDULED_AT]->(station)
RETURN 
    replacement.name AS cover_worker,
    replacement.role AS role,
    collect(distinct projects.name) AS affected_projects,
    count(distinct projects) AS project_count
ORDER BY replacement.name
```

### What Graph Makes Obvious

1. **Direct Path Visibility:** The `:CAN_COVER` relationship immediately shows who can cover whom. SQL requires looking up join tables + understanding the schema.

2. **Transitive Closure:** Easy to ask "who can cover if X AND Y are on vacation?" by chaining: `()-[:CAN_COVER]->()-[:CAN_COVER]->()`

3. **Impact Scope:** Worker → Station → Project relationships are *explicit*. SQL requires multiple LEFT JOINs and NULL handling to avoid missing rows.

4. **Business Language:** Cypher reads like the actual business question. SQL reads like database access logic.

**Winner: Graph** ✓

---

## Q3: Spot the Bottleneck (20 pts)

### Capacity Analysis

From `factory_capacity.csv`:

| Week | Own | Hired | Overtime | Total | Planned | Deficit |
|------|-----|-------|----------|-------|---------|---------|
| w1 | 400 | 80 | 0 | 480 | 612 | **-132** ⚠️ |
| w2 | 400 | 80 | 40 | 520 | 645 | **-125** ⚠️ |
| w3 | 400 | 80 | 0 | 480 | 398 | +82 ✓ |
| w4 | 400 | 80 | 20 | 500 | 550 | **-50** ⚠️ |
| w5 | 400 | 80 | 30 | 510 | 480 | +30 ✓ |
| w6 | 360 | 80 | 0 | 440 | 520 | **-80** ⚠️ |
| w7 | 400 | 80 | 40 | 520 | 600 | **-80** ⚠️ |
| w8 | 400 | 80 | 20 | 500 | 470 | +30 ✓ |

**Deficit weeks:** w1, w2, w4, w6, w7 (5 weeks overloaded)

### Bottleneck Identification (from factory_production.csv)

**Week W1 (Deficit: -132 hours)**
- P01 @ Station 014 (Svets): 35 planned → 38.2 actual (+3.2 over)
- P03 @ Station 014: 42 planned → 48 actual (+6 over) ← **Main bottleneck**
- P04 @ Station 014: Not scheduled
- P08 @ Station 014: 40 planned → 44 actual (+4 over)

**Week W2 (Deficit: -125 hours)**
- P01 @ Station 011: 48 planned → 50 actual (+2 over)
- P03 @ Station 012: 48 planned → 52 actual (+4 over)
- P08 @ Station 011: 65 planned → 68 actual (+3 over)

**Root Cause:** Station 014 (Svets o montage) consistently over budget

### Cypher Query for Bottleneck Detection

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1  // More than 10% over
RETURN 
    s.code AS station_code,
    s.name AS station_name,
    p.name AS project_name,
    r.week AS week,
    r.planned_hours AS planned,
    r.actual_hours AS actual,
    ROUND((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1) AS variance_pct
ORDER BY variance_pct DESC, s.code, r.week
```

### Graph Pattern for Alerting

```cypher
// Create Bottleneck nodes when variance > 10%
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
MERGE (b:Bottleneck {week: r.week, station_code: s.code})
CREATE (b)-[:OVERLOAD {project: p.name, variance_pct: ROUND((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1)}]->(p)

// Query all bottlenecks
MATCH (b:Bottleneck)-[rel:OVERLOAD]->(p:Project)
RETURN b.week AS week, b.station_code, collect(p.name) AS affected_projects
ORDER BY b.week
```

---

## Q4: Vector + Graph Hybrid (20 pts)

### New Project Request
> "450 meters of IQB beams for a hospital extension in Linköping, similar scope to previous hospital projects, tight timeline"

### What to Embed

1. **Project descriptions** (primary) — enables semantic "similar scope" search
2. **Product specifications** — material properties, tolerances
3. **Historical project summaries** — past hospital projects, timelines
4. **Station capabilities** — what each station specializes in

### Hybrid Query Pattern

```cypher
WITH 
    $request_embedding AS req_emb,  // Vector from LLM embedding
    ["011", "012", "013", "014"] AS critical_stations
CALL db.index.vector.queryNodes('project_embeddings', 10, req_emb) 
YIELD node AS similar_project, score
MATCH (similar_project)-[:SCHEDULED_AT]->(s:Station)
WHERE s.code IN critical_stations
  AND similar_project.variance_pct < 5.0  // Tight variance only
RETURN 
    similar_project.name AS past_project,
    score AS similarity_score,
    collect(s.name) AS stations_used,
    similar_project.timeline_days AS duration,
    similar_project.crew_size AS team_needed
ORDER BY score DESC
LIMIT 5
```

### Why More Useful Than Product-Type Filtering

1. **Semantic Understanding:** Matches based on *meaning*, not just product code
   - Past water treatment plants have IQB but different scope
   - Vector finds: "Other hospital extensions with similar scope"

2. **Historical Precedent:** Surfaces critical context
   - "Your new hospital project uses same stations as the past hospital project that ran 12 days over"
   - Product-type query would miss this

3. **Risk Identification:** 
   - Bottleneck prediction: "High-risk — same overloaded stations"
   - Staffing: "Need crew experienced with hospital projects"

4. **Team Assignment:**
   - Query: "Find crew that delivered similar hospital projects with variance < 5%"
   - Graph relationship: `(crew)-[:DELIVERED]->(past_hospital)-[:SIMILAR_TO]->(new_project)`

### Boardy Connection
In Boardy (people matching), same pattern finds "people with complementary skills [vector] who aren't on same team [graph]". **This is the secret sauce.**

---

## Q5: Your L6 Plan (20 pts)

### 1. Node Labels & CSV Mappings

| Node Label | CSV Source | Properties | Count |
|-----------|----------|-----------|-------|
| `Project` | factory_production.project_id, project_name | id, number, name | 8 |
| `Product` | factory_production.product_type | type, unit | 7 |
| `Station` | factory_production.station_code, station_name | code, name | 9 |
| `Worker` | factory_workers.worker_id, name | id, name, role, hours_per_week, type | 13 |
| `Week` | factory_production.week + factory_capacity.week | week, week_num | 8 |
| `Etapp` | factory_production.etapp | id | 2 |
| `BOP` | factory_production.bop | id | 3 |
| `Capacity` | factory_capacity.csv (aggregate) | id | 1 |

### 2. Relationship Types & Creation Logic

| Type | From → To | Properties | Source |
|------|-----------|-----------|--------|
| `PRODUCES` | Project → Product | quantity, unit_factor | production.csv row |
| `SCHEDULED_AT` | Project → Station | week, planned_hours, actual_hours, completed_units | production.csv row |
| `PART_OF` | Project → Etapp | — | production.csv.etapp |
| `FOLLOWS_BOP` | Project → BOP | — | production.csv.bop |
| `WORKS_AT` | Worker → Station | — | workers.csv.primary_station |
| `CAN_COVER` | Worker → Station | certifications | workers.csv.can_cover_stations |
| `HAS_CAPACITY` | Week → Capacity | own_staff, hired_staff, overtime, total, deficit | capacity.csv row |
| `IN_STATION` | Station → BOP | — | production.csv mapping |

### 3. Streamlit Dashboard Panels

#### Page 1: Project Overview (10 pts)
**Query:**
```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN p.name, 
       sum(r.planned_hours) AS total_planned,
       sum(r.actual_hours) AS total_actual,
       ROUND((sum(r.actual_hours) - sum(r.planned_hours)) / sum(r.planned_hours) * 100, 1) AS variance_pct,
       count(distinct s) AS station_count
GROUP BY p.name
ORDER BY variance_pct DESC
```
**Display:** Table with all 8 projects, metrics visible

#### Page 2: Station Load - Interactive Chart (10 pts)
**Query:**
```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN s.code, s.name, r.week, 
       sum(r.planned_hours) AS planned_hours,
       sum(r.actual_hours) AS actual_hours
GROUP BY s.code, s.name, r.week
ORDER BY s.code, r.week
```
**Display:** Plotly grouped bar chart (Week × Station, Planned vs Actual)

#### Page 3: Capacity Tracker (10 pts)
**Query:**
```cypher
MATCH (w:Week)-[c:HAS_CAPACITY]->(cap:Capacity)
RETURN w.week, w.week_num,
       c.own_staff + c.hired_staff + c.overtime_hours AS total_capacity,
       c.total_planned AS total_planned,
       c.deficit AS deficit
ORDER BY w.week_num
```
**Display:** Line chart (Capacity vs Demand), deficit weeks highlighted red

#### Page 4: Worker Coverage Matrix (10 pts)
**Query:**
```cypher
MATCH (w:Worker), (s:Station)
OPTIONAL MATCH (w)-[:CAN_COVER]->(s)
RETURN w.name, s.code, s.name,
       CASE WHEN w-[:CAN_COVER]->(s) THEN 1 ELSE 0 END AS coverage
ORDER BY w.name, s.code
```
**Display:** Heatmap (Workers × Stations), flag SPOF (single point of failure)

#### Page 5: Navigation (5 pts)
- Sidebar with `st.radio()` to select page
- Tabs with `st.tabs()` as alternative
- No page reload when switching

#### Page 6 (Bonus): Self-Test (20 pts)
- Check 1: Neo4j connection alive
- Check 2: Node count ≥ 50
- Check 3: Relationship count ≥ 100
- Check 4: 6+ distinct node labels
- Check 5: 8+ distinct relationship types
- Check 6: Variance query returns results
- Display: Green/red checklist with total score

### 4. Cypher Queries Powering Each Panel

| Page | Query Purpose | Cypher |
|------|--------------|--------|
| Overview | Project metrics | `MATCH (p:Project)-[r:SCHEDULED_AT]` |
| Station Load | Hours per station/week | `MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)` |
| Capacity | Weekly capacity vs demand | `MATCH (w:Week)-[c:HAS_CAPACITY]` |
| Workers | Coverage matrix | `MATCH (w:Worker)-[:CAN_COVER]->(s:Station)` |
| Bottleneck | Variance > 10% | `MATCH (p:Project)-[r:SCHEDULED_AT] WHERE r.actual_hours > r.planned_hours * 1.1` |

---

## Summary

**Graph Blueprint for L6:**
- **Nodes:** 8 labels, 60+ total instances
- **Relationships:** 8 types, 150+ total
- **Dashboard:** 5 pages + self-test
- **Queries:** All from Neo4j (no CSV reads)
- **Deployment:** Streamlit Cloud

**Expected L6 Score:** 85-100 pts

---

**END OF LEVEL 5 ANSWERS**
