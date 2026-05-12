# Level 5 - Graph Thinking
**Shubham Kumar | Submission**

---

## Q1. Model It (20 pts)

See `schema.md` for the full diagram. Schema image: [`schema.png`](schema.png)

### Summary

**8 Node Labels:** `Project`, `ProductionEntry`, `Station`, `Product`, `Week`, `Worker`, `Certification`, `CapacitySnapshot`

**10 Relationship Types:**

| Relationship | Direction | Properties |
|---|---|---|
| `HAS_ENTRY` | Project → ProductionEntry | — |
| `AT_STATION` | ProductionEntry → Station | — |
| `FOR_PRODUCT` | ProductionEntry → Product | — |
| `IN_WEEK` | ProductionEntry → Week | **`planned_hours`, `actual_hours`, `completed_units`** |
| `HAS_CAPACITY` | Week → CapacitySnapshot | — |
| `PRIMARY_AT` | Worker → Station | — |
| `CAN_COVER` | Worker → Station | — |
| `HAS_CERT` | Worker → Certification | — |
| `REQUIRES_CERT` | Station → Certification | — |
| `USES_PRODUCT` | Project → Product | **`quantity`, `unit_factor`** |

**Design decision:** `ProductionEntry` is an intermediate node (not just a relationship) because each production run has its own measured state (planned vs actual hours, completed units) that needs to be queried independently of the project or station.

---

## Q2. Why Not Just SQL? (20 pts)

**Query:** *"Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is on vacation, and which projects would be affected?"*

> Note: The dataset has `Per Hansen` (W07) as the primary operator at Station 016 (Gjutning).

### SQL Version

```sql
-- Step 1: Find covering workers (excluding Per Hansen)
SELECT
    w.name,
    w.role,
    w.certifications
FROM workers w
WHERE w.worker_id != 'W07'
  AND '016' = ANY(string_to_array(w.can_cover_stations, ','));

-- Step 2: Find affected projects
SELECT DISTINCT
    p.project_id,
    p.project_name
FROM production_runs pr
JOIN projects p ON pr.project_id = p.project_id
WHERE pr.station_code = '016';

-- Step 3: Combined (requires CROSS JOIN)
SELECT
    w.name        AS covering_worker,
    w.certifications,
    p.project_name AS affected_project
FROM workers w
CROSS JOIN (
    SELECT DISTINCT project_id
    FROM production_runs
    WHERE station_code = '016'
) affected
JOIN projects p ON affected.project_id = p.project_id
WHERE w.worker_id != 'W07'
  AND '016' = ANY(string_to_array(w.can_cover_stations, ','));
```

### Cypher Version

```cypher
MATCH (s:Station {station_code: '016'})
MATCH (w:Worker)-[:CAN_COVER]->(s)
WHERE w.name <> 'Per Hansen'
MATCH (pe:ProductionEntry)-[:AT_STATION]->(s)
MATCH (p:Project)-[:HAS_ENTRY]->(pe)
OPTIONAL MATCH (w)-[:HAS_CERT]->(c:Certification)
RETURN
    w.name                          AS covering_worker,
    collect(DISTINCT c.name)        AS certifications,
    collect(DISTINCT p.project_name) AS affected_projects
```

**Result from actual data:**
- Covering worker: **Victor Elm** (W11, Foreman) — the only worker who can cover station 016 besides Per Hansen
- Affected projects: **P03** (Lagerhall Jönköping, w2), **P05** (Sjukhus Linköping ET2, w2), **P07** (Idrottshall Västerås, w2), **P08** (Bro E6 Halmstad, w3)

### What Graph Makes Obvious

In SQL, the relationship between "who can cover" and "which projects are at risk" lives in completely separate tables — you have to manually write a CROSS JOIN to bridge them. In the graph, the path `(Worker)-[:CAN_COVER]->(Station)<-[:AT_STATION]-(ProductionEntry)<-[:HAS_ENTRY]-(Project)` is a single pattern traversal: the risk chain is structural, not computed. Most critically, the SQL result doesn't immediately surface that **Victor Elm is a single point of failure** for all 4 projects — the graph makes it obvious because there's only one path through station 016 and it leads to one person.

---

## Q3. Spot the Bottleneck (20 pts)

### 1. Overloaded Projects and Stations (from actual CSV data)

**Deficit weeks (from factory_capacity.csv):**

| Week | Capacity | Planned | Deficit |
|------|----------|---------|---------|
| w1 | 480 hrs | 612 hrs | **-132** |
| w2 | 520 hrs | 645 hrs | **-125** |
| w4 | 500 hrs | 550 hrs | -50 |
| w6 | 440 hrs | 520 hrs | -80 |
| w7 | 520 hrs | 600 hrs | -80 |

**Stations causing >10% overrun (from factory_production.csv):**

| Station | Project | Week | Planned | Actual | Overrun |
|---------|---------|------|---------|--------|---------|
| 016 Gjutning | P03 Lagerhall Jönköping | w2 | 28h | 35h | **+25.0%** |
| 016 Gjutning | P05 Sjukhus Linköping | w2 | 35h | 40h | **+14.3%** |
| 016 Gjutning | P08 Bro E6 Halmstad | w3 | 22h | 25h | **+13.6%** |
| 018 SB B/F-hall | P04 Parkering Helsingborg | w1 | 19h | 22h | **+15.8%** |
| 018 SB B/F-hall | P06 Skola Uppsala | w2 | 16h | 18h | **+12.5%** |
| 018 SB B/F-hall | P07 Idrottshall Västerås | w1 | 16h | 18h | **+12.5%** |
| 014 Svets o montage | P03 Lagerhall Jönköping | w1 | 42h | 48h | **+14.3%** |

**Root cause:** Station 016 (Gjutning) is the worst bottleneck — it consistently exceeds plan by 13–25% across 4 different projects, and has only **1 certified operator** (Per Hansen, W07). The w1/w2 capacity crises are driven by all 8 projects running simultaneously, with stations 016 and 018 absorbing unplanned overtime.

### 2. Cypher Query — Overruns >10% Grouped by Station

```cypher
MATCH (p:Project)-[:HAS_ENTRY]->(pe:ProductionEntry)-[:AT_STATION]->(s:Station)
WHERE pe.actual_hours > pe.planned_hours * 1.1
RETURN
    s.station_code,
    s.station_name,
    collect(p.project_name)                                          AS affected_projects,
    round(avg((pe.actual_hours - pe.planned_hours)
              / pe.planned_hours * 100), 1)                         AS avg_overrun_pct,
    sum(pe.actual_hours - pe.planned_hours)                         AS total_excess_hours
ORDER BY avg_overrun_pct DESC
```

### 3. Modelling the Alert as a Graph Pattern

I'd add a `(:Bottleneck)` node linked to the station + week combination, rather than just a flag on the relationship:

```cypher
// Create bottleneck node when overrun exceeds threshold
MATCH (pe:ProductionEntry)-[:AT_STATION]->(s:Station)
MATCH (pe)-[:IN_WEEK]->(w:Week)
WHERE pe.actual_hours > pe.planned_hours * 1.1
MERGE (b:Bottleneck {station_code: s.station_code, week_id: w.week_id})
  SET b.overrun_pct = round((pe.actual_hours - pe.planned_hours) / pe.planned_hours * 100, 1),
      b.excess_hours = pe.actual_hours - pe.planned_hours
MERGE (s)-[:HAS_BOTTLENECK]->(b)
MERGE (w)-[:HAS_BOTTLENECK]->(b)
```

Why a node rather than a property: bottlenecks are queryable objects — you can ask "show me all current bottlenecks", "which worker is assigned to a bottlenecked station", or "which projects are at risk because of this bottleneck" using graph traversal. A property would require scanning all `IN_WEEK` relationships to find them.

---

## Q4. Vector + Graph Hybrid (20 pts)

### 1. What to Embed

I would embed **project description strings** constructed from: `project_name + product_type + quantity + station_sequence`. For example:

```
"Sjukhus Linköping ET2 — IQB 1200m + IQP 150pcs + SB 50pcs + SR 20pcs — stations 011,012,013,014,015,018,021"
```

This captures:
- **What** is being built (product types + quantities)
- **How** it flows through the factory (station sequence)
- **Context** (hospital, school, bridge — affects complexity and timeline)

Worker skills are also worth embedding separately for a coverage/staffing search.

### 2. Hybrid Query — Vector Similarity + Graph Filter

```cypher
// $query_embedding = embedding of the new project request text
CALL db.index.vector.queryNodes('project_embeddings', 10, $query_embedding)
YIELD node AS similar_project, score

// Graph filter: only projects where variance < 5% AND used the same station set
MATCH (similar_project)-[:HAS_ENTRY]->(pe:ProductionEntry)-[:AT_STATION]->(s:Station)
WITH similar_project, score,
     collect(DISTINCT s.station_code) AS used_stations,
     avg(toFloat(pe.actual_hours - pe.planned_hours) / pe.planned_hours * 100) AS avg_variance

WHERE avg_variance < 5.0

RETURN
    similar_project.project_name,
    similar_project.project_id,
    used_stations,
    round(avg_variance, 2) AS variance_pct,
    round(score, 3)        AS similarity_score
ORDER BY score DESC
LIMIT 5
```

### 3. Why This Beats Plain Filtering

Filtering by `product_type = 'IQB'` would return every IQB project regardless of scale, station mix, or execution quality. The hybrid query finds projects that are **semantically similar** (same scope, similar complexity, similar factory footprint) **AND** historically well-executed (variance < 5%). This is the difference between "projects that used the same material" and "projects that are actually comparable benchmarks". For the new hospital request, it would surface P05 (Sjukhus Linköping, also a hospital) as the best reference — not because of a string match, but because the description vector lands nearby AND P05 ran within tolerance.

**Boardy parallel:** Replace "projects" with "people". A new user's needs embed close to someone else's offerings (vector), AND they're in the same industry graph community (graph). That's the matching engine.

---

## Q5. My L6 Blueprint (20 pts)

### Node Labels → CSV Column Mappings

| Node | CSV | Mapped Columns |
|------|-----|----------------|
| `(:Project)` | factory_production.csv | `project_id`, `project_number`, `project_name`, `etapp`, `bop` |
| `(:Station)` | factory_production.csv | `station_code`, `station_name` |
| `(:Product)` | factory_production.csv | `product_type`, `unit`, `unit_factor` |
| `(:Week)` | both | `week` (w1–w8) |
| `(:ProductionEntry)` | factory_production.csv | `planned_hours`, `actual_hours`, `completed_units` (one node per row) |
| `(:Worker)` | factory_workers.csv | `worker_id`, `name`, `role`, `hours_per_week`, `type` |
| `(:Certification)` | factory_workers.csv | split `certifications` by comma → one node per cert |
| `(:CapacitySnapshot)` | factory_capacity.csv | `own_staff_count`, `hired_staff_count`, `own_hours`, `hired_hours`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit` |

### Relationship Types and What Creates Them

| Relationship | Created By |
|---|---|
| `(Project)-[:HAS_ENTRY]->(ProductionEntry)` | Group rows by `project_id` |
| `(ProductionEntry)-[:AT_STATION]->(Station)` | `station_code` column |
| `(ProductionEntry)-[:FOR_PRODUCT]->(Product)` | `product_type` column |
| `(ProductionEntry)-[:IN_WEEK {planned_hours, actual_hours, completed_units}]->(Week)` | `week` column |
| `(Week)-[:HAS_CAPACITY]->(CapacitySnapshot)` | `week` column join with factory_capacity.csv |
| `(Worker)-[:PRIMARY_AT]->(Station)` | `primary_station` column |
| `(Worker)-[:CAN_COVER]->(Station)` | Split `can_cover_stations` by comma |
| `(Worker)-[:HAS_CERT]->(Certification)` | Split `certifications` by comma |
| `(Station)-[:REQUIRES_CERT]->(Certification)` | Derived from worker cert overlap per station (see factory_workers.csv) |
| `(Project)-[:USES_PRODUCT {quantity, unit_factor}]->(Product)` | `product_type` + `quantity` + `unit_factor` |

### 3 Streamlit Dashboard Panels

#### Panel 1 — Project Overview

All 8 projects with planned vs actual hours and % variance.

```cypher
MATCH (p:Project)-[:HAS_ENTRY]->(pe:ProductionEntry)
RETURN p.project_id, p.project_name,
       sum(pe.planned_hours)  AS total_planned,
       sum(pe.actual_hours)   AS total_actual,
       round(sum(pe.actual_hours) / sum(pe.planned_hours) * 100, 1) AS completion_efficiency_pct,
       sum(pe.completed_units) AS total_units_completed
ORDER BY p.project_id
```

Displayed as: horizontal bar chart (planned vs actual), table below with variance % highlighted red if > 10%.

#### Panel 2 — Station Load by Week

Interactive heatmap of station load across weeks, with overloaded cells highlighted.

```cypher
MATCH (pe:ProductionEntry)-[:AT_STATION]->(s:Station)
MATCH (pe)-[:IN_WEEK]->(w:Week)
RETURN s.station_code, s.station_name, w.week_id,
       sum(pe.planned_hours) AS planned,
       sum(pe.actual_hours)  AS actual,
       round((sum(pe.actual_hours) - sum(pe.planned_hours))
             / sum(pe.planned_hours) * 100, 1) AS variance_pct
ORDER BY s.station_code, w.week_id
```

Displayed as: Plotly heatmap (stations × weeks), cells red where variance_pct > 10%.

#### Panel 3 — Capacity Tracker

Weekly capacity vs demand with deficit weeks flagged.

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:CapacitySnapshot)
RETURN w.week_id,
       c.total_capacity,
       c.total_planned,
       c.deficit,
       c.overtime_hours
ORDER BY w.week_id
```

Displayed as: line chart (capacity vs planned), deficit bars below axis shown in red. Tooltip shows overtime hours.

#### Panel 4 — Worker Coverage Matrix (SPOF detection)

Which stations are covered by how many workers — single points of failure flagged.

```cypher
MATCH (s:Station)
OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
WITH s,
     collect(DISTINCT w.name)   AS all_coverers,
     count(DISTINCT w)          AS coverage_count
RETURN s.station_code, s.station_name,
       all_coverers,
       coverage_count,
       CASE WHEN coverage_count <= 1 THEN true ELSE false END AS is_spof
ORDER BY coverage_count ASC
```

Displayed as: table with red badge on SPOF stations. Clicking a station shows which projects depend on it (second Cypher query drilled down on click).
