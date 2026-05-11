# Level 5 — Graph Thinking: answers.md

---

## Q1. Model It

> See `schema.md` for the full Mermaid diagram.

### Node Labels (9 total)

| Label | Mapped From | Key Properties |
|---|---|---|
| `Project` | factory_production.csv | project_id, project_number, project_name, etapp |
| `Product` | factory_production.csv | product_type, unit, unit_factor |
| `Station` | factory_production.csv | station_code, station_name |
| `Worker` | factory_workers.csv | worker_id, name, role, hours_per_week, type |
| `Week` | factory_capacity.csv | week_id |
| `CapacitySnapshot` | factory_capacity.csv | own_hours, hired_hours, overtime_hours, total_capacity, total_planned, deficit |
| `ProductionEntry` | factory_production.csv (one node per row) | entry_id, planned_hours, actual_hours, completed_units, quantity |
| `Certification` | factory_workers.csv (certifications column, split) | cert_id, name, issuing_body |
| `BOP` | factory_production.csv | bop_id, etapp |

`ProductionEntry` is the central junction node — it connects a Project, a Product, a Station, and a Week in one place, with hours data on the edges. `Week` and `CapacitySnapshot` are now separate nodes: `Week` is a lightweight time anchor, while `CapacitySnapshot` carries all the operational capacity figures for that week.

### Relationship Types (12 total)

| Relationship | From → To | Properties |
|---|---|---|
| `HAS_RUN` | Project → ProductionEntry | — |
| `USES_PRODUCT` | ProductionEntry → Product | — |
| `PROCESSED_AT` | ProductionEntry → Station | `planned_hours`, `actual_hours`, `completed_units` |
| `SCHEDULED_IN` | ProductionEntry → Week | `planned_hours`, `actual_hours` |
| `REQUIRES_STATION` | Project → Station | — |
| `STRUCTURED_BY` | Project → BOP | — |
| `PRIMARILY_AT` | Worker → Station | — |
| `CAN_COVER` | Worker → Station | — |
| `WORKED_ON` | Worker → ProductionEntry | — |
| `HOLDS` | Worker → Certification | — |
| `REQUIRES_CERT` | Station → Certification | — |
| `HAS_SNAPSHOT` | Week → CapacitySnapshot | — |

**Two relationships with data properties:**

```cypher
// Example 1 — production variance lives on the edge
(entry:ProductionEntry)-[:PROCESSED_AT {planned_hours: 28.0, actual_hours: 35.0, completed_units: 8}]->(s:Station {station_code: "016"})

// Example 2 — weekly scheduling data lives on the edge
(entry:ProductionEntry)-[:SCHEDULED_IN {planned_hours: 35.0, actual_hours: 40.0}]->(w:Week {week_id: "w2"})
```

---

## Q2. Why Not Just SQL?

### The question:
> *"Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is on vacation, and which projects would be affected?"*

---

### SQL Version

```sql
-- Step 1: find all workers who can cover station 016, excluding Per Hansen
SELECT
    w.worker_id,
    w.name,
    w.role,
    w.certifications
FROM workers w
WHERE w.primary_station = '016'
   OR w.worker_id IN (
       SELECT worker_id FROM worker_station_coverage
       WHERE station_code = '016'
   )
  AND w.name <> 'Per Hansen';

-- Step 2: find projects currently running through station 016
SELECT DISTINCT
    p.project_id,
    p.project_name,
    pr.week,
    pr.planned_hours,
    pr.actual_hours
FROM factory_production pr
JOIN projects p ON pr.project_id = p.project_id
WHERE pr.station_code = '016';

-- These are two separate queries. Joining them to get
-- "which qualified workers can cover which at-risk projects"
-- requires yet another join or a CTE.
```

The SQL answer requires at minimum **2 separate queries** (or a complex CTE) because the relationship between worker coverage capability and project risk runs through three different tables with no direct link.

---

### Cypher Version

```cypher
// Single traversal: coverage candidates + affected projects in one shot
MATCH (absent:Worker {name: "Per Hansen"})-[:PRIMARILY_AT]->(s:Station {station_code: "016"})
MATCH (cover:Worker)-[:CAN_COVER]->(s)
WHERE cover.name <> "Per Hansen"
MATCH (entry:ProductionEntry)-[:PROCESSED_AT]->(s)
MATCH (proj:Project)-[:HAS_RUN]->(entry)
RETURN
    cover.name        AS CoverageWorker,
    cover.role        AS Role,
    collect(DISTINCT proj.project_name) AS AffectedProjects
ORDER BY cover.role
```

---

### What the graph makes obvious that SQL hides

In the graph model, the path `(Worker)-[:CAN_COVER]->(Station)<-[:PROCESSED_AT]-(ProductionEntry)<-[:HAS_RUN]-(Project)` is a single traversal pattern — the question is literally the shape of the graph. SQL forces you to reconstruct that traversal manually via joins across normalized tables, and the intermediate relationships (who covers what, what runs at a station, what project owns that run) are all implicit in foreign keys rather than first-class connections. In a graph, the relationship *is* the data.

---

## Q3. Spot the Bottleneck

### Capacity analysis from `factory_capacity.csv`

| Week | Capacity | Planned | Deficit |
|------|----------|---------|---------|
| w1   | 480      | 612     | **-132** |
| w2   | 520      | 645     | **-125** |
| w3   | 480      | 398     | +82     |
| w4   | 500      | 550     | **-50** |
| w5   | 510      | 480     | +30     |
| w6   | 440      | 520     | **-80** |
| w7   | 520      | 600     | **-80** |
| w8   | 500      | 470     | +30     |

Weeks **w1, w2, w4, w6, w7** all show deficits. The largest crunch is w1–w2, which aligns with most projects starting simultaneously.

### Which stations/projects are causing overload?

Cross-referencing `factory_production.csv` for w1 and w2 — stations **011 (FS IQB)**, **014 (Svets o montage IQB)**, and **016 (Gjutning)** consistently show `actual_hours > planned_hours`:

- **Station 011**: All 8 projects run here in w1/w2; P03 runs 75h actual vs 72h planned, P05 runs 98h vs 95h, P08 runs 68h vs 65h.
- **Station 014**: P03 runs 48h vs 42h (14.3% over), P05 runs 62h vs 58h (6.9% over), P08 runs 44h vs 40h (10% over).
- **Station 016 (Gjutning)**: P03 runs 35h vs 28h (**+25% over**), P05 runs 40h vs 35h (**+14.3% over**), P07 runs 22h vs 20h (10% over).

Station 016 is the single biggest percentage overrun and is the clear bottleneck.

---

### Cypher query — find all >10% overrun cases by station

```cypher
MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.10
WITH s, proj, entry, r,
     round(100.0 * (r.actual_hours - r.planned_hours) / r.planned_hours, 1) AS variance_pct
RETURN
    s.station_code                    AS station,
    s.station_name                    AS station_name,
    collect({
        project:  proj.project_name,
        entry_id: entry.entry_id,
        planned:  r.planned_hours,
        actual:   r.actual_hours,
        variance: variance_pct
    })                                AS overruns,
    count(*)                          AS overrun_count
ORDER BY overrun_count DESC
```

---

### Modelling the alert as a graph pattern

Rather than computing overruns at query time every time, I'd materialise a `:Bottleneck` node when a threshold is breached — making the alert a first-class citizen in the graph:

```cypher
// Detect and write bottleneck nodes
MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
MATCH (entry)-[:SCHEDULED_IN]->(w:Week)
WHERE r.actual_hours > r.planned_hours * 1.10
MERGE (b:Bottleneck {id: entry.entry_id + "_" + s.station_code})
  ON CREATE SET
    b.variance_pct    = round(100.0 * (r.actual_hours - r.planned_hours) / r.planned_hours, 1),
    b.severity        = CASE
                          WHEN r.actual_hours > r.planned_hours * 1.25 THEN "critical"
                          WHEN r.actual_hours > r.planned_hours * 1.10 THEN "warning"
                          ELSE "ok"
                        END,
    b.detected_at     = datetime()
MERGE (entry)-[:TRIGGERS]->(b)
MERGE (b)-[:AT_STATION]->(s)
MERGE (b)-[:IN_WEEK]->(w)
```

This gives you a queryable alert layer: `MATCH (b:Bottleneck {severity:"critical"})-[:AT_STATION]->(s)` returns all hot stations instantly, without recomputing variance across all rows. Dashboards can subscribe to Bottleneck nodes rather than recalculating from raw production data on every render.

---

## Q4. Vector + Graph Hybrid

### What would I embed?

I'd embed **project description text** constructed from structured fields:

```
"{project_name} — {product_types} — {total_quantity}{unit} — {etapp} — stations: {station_list}"
```

For example:
> *"Sjukhus Linköping ET2 — IQB, IQP, SB, SD — 1200m IQB + 150 IQP — ET2 — stations: 011, 012, 013, 014, 015, 016, 017, 018, 021"*

I would also embed **worker skill profiles** (role + certifications joined as a sentence) to power the Boardy-style matching pattern later.

Storing raw product codes alone loses semantic meaning. The embedding needs enough natural language to capture scope, complexity, and domain (hospital vs warehouse vs bridge) so that vector similarity finds genuinely comparable past projects.

---

### Hybrid query: similar past projects with low variance

```cypher
// Phase 1 — vector ANN: find top-k semantically similar projects
// (assumes Neo4j Vector Index on Project.embedding)
CALL db.index.vector.queryNodes(
    'project_embeddings',
    5,
    $query_embedding   // embedding of the new request text
) YIELD node AS candidate, score

// Phase 2 — graph filter: same stations, variance < 5% across all runs
WITH candidate, score
MATCH (candidate)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
WHERE abs(r.actual_hours - r.planned_hours) / r.planned_hours < 0.05

// Phase 3 — verify station overlap with the incoming project's required stations
WITH candidate, score, collect(DISTINCT s.station_code) AS used_stations
WHERE all(req IN $required_stations WHERE req IN used_stations)

RETURN
    candidate.project_name   AS similar_project,
    candidate.project_id     AS pid,
    used_stations,
    score                    AS similarity
ORDER BY score DESC
LIMIT 3
```

---

### Why this beats filtering by product type alone

Filtering by `product_type = 'IQB'` would return every IQB project regardless of scale, station mix, or execution quality. Two projects can both produce IQB beams — one running 600m through 4 stations on time, another running 1200m through 9 stations 25% over budget. They're not comparable for planning purposes.

The vector finds *scope and domain* similarity (hospital extension ≈ hospital extension, regardless of exact product codes), while the graph filter enforces *structural compatibility* — same stations, same variance tolerance. Together they surface past projects that are both semantically relevant *and* operationally comparable, which is exactly the signal a production planner needs to estimate risk on new work.

This is the same pattern Boardy uses: the vector finds whose needs embed close to whose offers, and the graph filter ensures they're in the same community (geography, industry, mutual connections). Matching on embedding alone misses structural fit; graph alone misses latent similarity.

---

## Q5. L6 Blueprint

### Node Labels → CSV Column Mapping

| Node Label | CSV Source | Mapped Columns |
|---|---|---|
| `Project` | factory_production.csv | project_id, project_number, project_name, etapp |
| `Product` | factory_production.csv | product_type, unit, unit_factor |
| `Station` | factory_production.csv | station_code, station_name |
| `ProductionEntry` | factory_production.csv (1 node per row) | entry_id (generated), planned_hours, actual_hours, completed_units, quantity |
| `Worker` | factory_workers.csv | worker_id, name, role, hours_per_week, type |
| `Certification` | factory_workers.csv | certifications (split on comma) |
| `Week` | factory_capacity.csv | week (as week_id) |
| `CapacitySnapshot` | factory_capacity.csv | own_hours, hired_hours, overtime_hours, total_capacity, total_planned, deficit |
| `BOP` | factory_production.csv | bop (distinct values) |

---

### Relationship Types → What Creates Them

| Relationship | Created By |
|---|---|
| `(Project)-[:HAS_RUN]->(ProductionEntry)` | factory_production.csv — group by project_id |
| `(ProductionEntry)-[:USES_PRODUCT]->(Product)` | factory_production.csv — product_type column |
| `(ProductionEntry)-[:PROCESSED_AT {planned_hours, actual_hours, completed_units}]->(Station)` | factory_production.csv — station_code + hours columns |
| `(ProductionEntry)-[:SCHEDULED_IN {planned_hours, actual_hours}]->(Week)` | factory_production.csv — week column |
| `(Project)-[:REQUIRES_STATION]->(Station)` | factory_production.csv — derived: distinct (project_id, station_code) |
| `(Project)-[:STRUCTURED_BY]->(BOP)` | factory_production.csv — bop column |
| `(Worker)-[:PRIMARILY_AT]->(Station)` | factory_workers.csv — primary_station column |
| `(Worker)-[:CAN_COVER]->(Station)` | factory_workers.csv — can_cover_stations column (split on comma) |
| `(Worker)-[:WORKED_ON]->(ProductionEntry)` | factory_workers.csv + factory_production.csv — join on station_code |
| `(Worker)-[:HOLDS]->(Certification)` | factory_workers.csv — certifications column (split on comma) |
| `(Station)-[:REQUIRES_CERT]->(Certification)` | factory_workers.csv — derived: certifications required per station |
| `(Week)-[:HAS_SNAPSHOT]->(CapacitySnapshot)` | factory_capacity.csv — one snapshot per week row |

---

### Dashboard Panels

#### Panel 1 — Station Load Bar Chart

**Purpose:** Show planned vs actual hours per station per week, highlight overloaded stations in red.

```cypher
MATCH (entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
MATCH (entry)-[:SCHEDULED_IN]->(w:Week)
RETURN
    s.station_code                  AS station,
    s.station_name                  AS station_name,
    w.week_id                       AS week,
    sum(r.planned_hours)            AS total_planned,
    sum(r.actual_hours)             AS total_actual,
    sum(r.actual_hours) - sum(r.planned_hours) AS delta
ORDER BY w.week_id, s.station_code
```

Rendered as a grouped bar chart (Streamlit + Plotly). Bars coloured red when `delta > 0`, green when under.

---

#### Panel 2 — Project Timeline Heatmap

**Purpose:** Matrix of projects (rows) × weeks (columns), cell colour = variance percentage. Lets planners spot which projects are slipping and when.

```cypher
MATCH (proj:Project)-[:HAS_RUN]->(entry:ProductionEntry)-[r:PROCESSED_AT]->(s:Station)
MATCH (entry)-[:SCHEDULED_IN]->(w:Week)
WITH proj, w,
     sum(r.planned_hours) AS planned,
     sum(r.actual_hours)  AS actual
RETURN
    proj.project_name AS project,
    w.week_id         AS week,
    planned,
    actual,
    round(100.0 * (actual - planned) / planned, 1) AS variance_pct
ORDER BY proj.project_id, w.week_id
```

Rendered as a Seaborn/Plotly heatmap. Red = over plan, green = under, white = on target.

---

#### Panel 3 — Worker Coverage Matrix

**Purpose:** For each station, show which workers are available (primary) and who can cover in case of absence. Useful for vacation planning and risk visibility.

```cypher
MATCH (s:Station)
OPTIONAL MATCH (primary:Worker)-[:PRIMARILY_AT]->(s)
OPTIONAL MATCH (backup:Worker)-[:CAN_COVER]->(s)
WHERE backup.worker_id <> primary.worker_id
RETURN
    s.station_code                          AS station,
    s.station_name                          AS station_name,
    collect(DISTINCT primary.name)          AS primary_workers,
    collect(DISTINCT backup.name)           AS backup_workers,
    size(collect(DISTINCT backup.name))     AS coverage_depth
ORDER BY coverage_depth ASC   // stations with least coverage surface first
```

Rendered as an interactive table in Streamlit with `st.dataframe`. Rows with `coverage_depth = 0` highlighted in red.

---

#### Panel 4 — Capacity Overview (Gantt / Deficit Tracker)

**Purpose:** Weekly capacity vs demand with deficit bars, so management sees where overtime is required.

```cypher
MATCH (w:Week)-[:HAS_SNAPSHOT]->(cs:CapacitySnapshot)
RETURN
    w.week_id          AS week,
    cs.total_capacity  AS capacity,
    cs.own_hours       AS own_hours,
    cs.hired_hours     AS hired_hours,
    cs.overtime_hours  AS overtime_hours,
    cs.total_planned   AS planned,
    cs.deficit         AS deficit
ORDER BY w.week_id
```

Rendered as a combo chart: stacked bar for capacity broken down by own, hired, and overtime hours (all now available from `CapacitySnapshot`), and a line for planned demand. Deficit weeks shaded red.

---

### Tech Stack Notes

- **Neo4j AuraDB** (or local Docker) for graph storage
- **Python `neo4j` driver** for Cypher queries in Streamlit
- **Pandas** for intermediate aggregation before plotting
- **Plotly** for interactive charts (heatmap, bar, combo)
- **`st.cache_data`** with TTL on all Cypher calls to avoid hammering the DB on each widget interaction
- **Vector index** on `Project.embedding` (Neo4j 5.x) for Q4-style similarity queries in a later sprint
