# Level 5 - Graph Thinking
**Dia Vats**

---

## Q1. Model It

See `schema.md` for the full diagram source and `schema.png` for the rendered image.

### Schema Summary

**Node Labels (8):** `Project`, `WorkOrder`, `Station`, `Product`, `Week`, `Worker`, `Certification`, `CapacitySnapshot`

**Relationship Types (11):**

| Relationship | Direction | Properties |
|---|---|---|
| `HAS_WORKORDER` | Project → WorkOrder | — |
| `AT_STATION` | WorkOrder → Station | — |
| `PRODUCES` | WorkOrder → Product | — |
| `SCHEDULED_IN` | WorkOrder → Week | **`planned_hours`, `actual_hours`, `completed_units`** |
| `HAS_CAPACITY` | Week → CapacitySnapshot | — |
| `ASSIGNED_TO` | Worker → Station | — |
| `CAN_COVER` | Worker → Station | — |
| `CERTIFIED_IN` | Worker → Certification | — |
| `REQUIRES` | Station → Certification | — |
| `FEEDS_INTO` | Station → Station | — |
| `FOLLOWS` | WorkOrder → WorkOrder | — |

**Relationships carrying data:**

- `(WorkOrder)-[:SCHEDULED_IN {planned_hours, actual_hours, completed_units}]->(Week)`
- `(Project)-[:PRODUCES {quantity, unit_factor}]->(Product)` *(project-level aggregate)*

### Design Reasoning

The key design choice here is using `WorkOrder` as the operational unit instead of something like `ProductionEntry`. Each row in `factory_production.csv` is a discrete execution event — a specific project working a specific product through a specific station in a specific week. That's a work order, not just a data entry. Naming it that way makes the graph match how a factory actually operates.

The two relationships I added that others probably won't have: `FEEDS_INTO` between stations (011 → 012 → 013 is the IQB flow sequence), and `FOLLOWS` between WorkOrders (w1 execution feeds into w2 execution for the same project-station pair). Without these, every bottleneck looks isolated. With them, you can trace downstream impact — if station 016 overruns in w2, you can see which downstream work orders are at risk.

---

## Q2. Why Not Just SQL?

**Query:** *"Which workers are certified to cover Station 016 (Gjutning) when Per Gustafsson is on vacation, and which projects would be affected?"*

> Note: The dataset lists `Per Hansen` (W07) as the primary operator at Station 016. I'm treating "Per Gustafsson" as referring to this worker.

### SQL Version

```sql
-- Workers certified to cover 016
SELECT
    w.name,
    w.role,
    w.certifications
FROM workers w
WHERE w.worker_id != 'W07'
  AND '016' = ANY(string_to_array(w.can_cover_stations, ','));

-- Projects that run through station 016
SELECT DISTINCT
    p.project_id,
    p.project_name
FROM work_orders wo
JOIN projects p ON wo.project_id = p.project_id
WHERE wo.station_code = '016';
```

To get both in one result you need a CROSS JOIN - which already signals you're fighting the data model.

### Cypher Version

```cypher
MATCH (s:Station {station_code: '016'})
MATCH (w:Worker)-[:CAN_COVER]->(s)
WHERE w.worker_id <> 'W07'
MATCH (wo:WorkOrder)-[:AT_STATION]->(s)
MATCH (p:Project)-[:HAS_WORKORDER]->(wo)
OPTIONAL MATCH (w)-[:CERTIFIED_IN]->(c:Certification)
RETURN
    w.name                            AS backup_worker,
    collect(DISTINCT c.name)          AS certifications,
    collect(DISTINCT p.project_name)  AS affected_projects
```

### What the Graph Makes Clear

The SQL version gives the right answer but doesn't show the risk. You get a list of names and a separate list of projects - connecting them is left to whoever is reading the output.

In the graph, the path `(Worker)-[:CAN_COVER]->(Station)<-[:AT_STATION]-(WorkOrder)<-[:HAS_WORKORDER]-(Project)` makes the dependency structural. When I ran this against the actual data, Victor Elm (W11, Foreman) is the only worker who can cover station 016 besides Per Hansen. That means four active projects - P03, P05, P07, P08 — all route their coverage risk through one person. SQL can tell you that too, but it won't show you that it's a single path until you draw it out. The graph just... shows it.

---

## Q3. Spot the Bottleneck

### Capacity Deficits (from factory_capacity.csv)

| Week | Capacity | Planned | Deficit |
|------|----------|---------|---------|
| w1 | 480 hrs | 612 hrs | **-132** |
| w2 | 520 hrs | 645 hrs | **-125** |
| w4 | 500 hrs | 550 hrs | -50 |
| w6 | 440 hrs | 520 hrs | -80 |
| w7 | 520 hrs | 600 hrs | -80 |

w1 and w2 are the worst - five of eight weeks are in deficit, which means this factory is running over capacity more often than not.

### Stations Causing the Overload (>10% actual vs planned)

| Station | Project | Week | Planned | Actual | Variance |
|---------|---------|------|---------|--------|---------|
| 016 Gjutning | P03 Lagerhall Jönköping | w2 | 28h | 35h | **+25.0%** |
| 016 Gjutning | P05 Sjukhus Linköping | w2 | 35h | 40h | **+14.3%** |
| 016 Gjutning | P08 Bro E6 Halmstad | w3 | 22h | 25h | **+13.6%** |
| 018 SB B/F-hall | P04 Parkering Helsingborg | w1 | 19h | 22h | **+15.8%** |
| 018 SB B/F-hall | P06 Skola Uppsala | w2 | 16h | 18h | **+12.5%** |
| 014 Svets o montage | P03 Lagerhall Jönköping | w1 | 42h | 48h | **+14.3%** |

Station 016 keeps showing up. It's consistently over by 13–25% across different projects, and the worker coverage there is basically one person (Per Hansen) with Victor Elm as the only real fallback.

### Cypher Query — Overruns >10% Grouped by Station

```cypher
MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)
MATCH (wo)-[:AT_STATION]->(s:Station)
MATCH (wo)-[r:SCHEDULED_IN]->(w:Week)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN
    s.station_code,
    s.station_name,
    collect(DISTINCT p.project_name)                                      AS affected_projects,
    round(avg((r.actual_hours - r.planned_hours) / r.planned_hours * 100), 1) AS avg_variance_pct,
    sum(r.actual_hours - r.planned_hours)                                 AS excess_hours
ORDER BY avg_variance_pct DESC
```

### Modelling the Bottleneck as a Graph Pattern

I'd keep the bottleneck signal on the `SCHEDULED_IN` relationship as a property (`is_bottleneck: true`) rather than creating a separate node. The reason is practical: bottlenecks in this data are tied to a specific execution event — a project at a station in a week. That's already what `SCHEDULED_IN` represents. Adding a `(:Bottleneck)` node would mean joining three things that are already joined.

The `FEEDS_INTO` relationships I have between stations add something useful here though: once you flag a bottleneck on `SCHEDULED_IN`, you can traverse `FEEDS_INTO` to see which downstream stations and work orders are at risk. That's the part a flat flag can't do on its own.

```cypher
MATCH (wo:WorkOrder)-[r:SCHEDULED_IN]->(w:Week)
WHERE r.actual_hours > r.planned_hours * 1.1
SET r.is_bottleneck = true,
    r.variance_pct = round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1)
```

---

## Q4. Vector + Graph Hybrid

### What I Would Embed

I'd embed a constructed string per project that includes: project type, product mix with quantities, station sequence, and etapp/phase. Something like:

```
"Warehouse project Lagerhall Jönköping — IQB 900m across stations 011 012 013 014 016 017 — ET1 BOP1/BOP2"
```

This captures what the project is, how complex the product mix is, and which part of the factory it touches. Embedding just product type misses scope; embedding station sequence captures operational complexity.

Worker skills are worth a separate embedding index too, especially for the coverage query problem — but for matching incoming project requests, the project description is the right unit.

### Hybrid Query

```cypher
CALL db.index.vector.queryNodes('project_embeddings', 10, $query_embedding)
YIELD node AS similar_project, score

MATCH (similar_project)-[:HAS_WORKORDER]->(wo:WorkOrder)
MATCH (wo)-[:AT_STATION]->(s:Station)
MATCH (wo)-[r:SCHEDULED_IN]->(:Week)

WITH similar_project,
     score,
     collect(DISTINCT s.station_code) AS stations_used,
     avg(abs((r.actual_hours - r.planned_hours) / r.planned_hours) * 100) AS avg_variance_pct

WHERE avg_variance_pct < 5.0

RETURN
    similar_project.project_name,
    similar_project.project_id,
    stations_used,
    round(avg_variance_pct, 2) AS variance_pct,
    round(score, 3)            AS similarity_score
ORDER BY similarity_score DESC
LIMIT 5
```

### Why This Matters More Than Filtering

If you filter by `product_type = 'IQB'`, you get every IQB project regardless of whether it was 200 meters or 1200 meters, whether it ran through 3 stations or 7, whether it overran by 25% or came in clean. The results aren't comparable.

The hybrid query finds projects that are actually similar in scope and execution footprint (vector), and then filters to only the ones that ran well (graph). For the hospital request in the question — "450 meters of IQB beams, tight timeline" — you'd get P04 or P06 back as references, not P05 (the 1200m hospital project that overran at 016). That's the useful answer.

The Boardy parallel makes sense here: instead of matching project descriptions to project history, you're matching what a person needs to what someone else offers. Vector finds the semantic overlap, graph confirms they're actually in compatible communities.

---

## Q5. My L6 Blueprint

### Node Labels → CSV Columns

| Node | CSV Source | Columns Mapped |
|---|---|---|
| `Project` | factory_production.csv | `project_id`, `project_number`, `project_name`, `etapp`, `bop` |
| `WorkOrder` | factory_production.csv | `planned_hours`, `actual_hours`, `completed_units` (one node per row) |
| `Station` | factory_production.csv | `station_code`, `station_name` |
| `Product` | factory_production.csv | `product_type`, `unit`, `unit_factor` |
| `Week` | both CSVs | `week` column (w1–w8) |
| `Worker` | factory_workers.csv | `worker_id`, `name`, `role`, `hours_per_week`, `type` |
| `Certification` | factory_workers.csv | `certifications` split by comma → one node per cert |
| `CapacitySnapshot` | factory_capacity.csv | `own_staff_count`, `hired_staff_count`, `own_hours`, `hired_hours`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit` |

### Relationship Types → What Creates Them

| Relationship | Created From |
|---|---|
| `(Project)-[:HAS_WORKORDER]->(WorkOrder)` | `project_id` column |
| `(WorkOrder)-[:AT_STATION]->(Station)` | `station_code` column |
| `(WorkOrder)-[:PRODUCES]->(Product)` | `product_type` column |
| `(WorkOrder)-[:SCHEDULED_IN {planned_hours, actual_hours, completed_units}]->(Week)` | `week` column + hour columns |
| `(Week)-[:HAS_CAPACITY]->(CapacitySnapshot)` | join on `week` across both CSVs |
| `(Worker)-[:ASSIGNED_TO]->(Station)` | `primary_station` column |
| `(Worker)-[:CAN_COVER]->(Station)` | `can_cover_stations` split by comma |
| `(Worker)-[:CERTIFIED_IN]->(Certification)` | `certifications` split by comma |
| `(Station)-[:REQUIRES]->(Certification)` | derived from worker certs per station |
| `(Station)-[:FEEDS_INTO]->(Station)` | derived from production flow order (011→012→013→014→015→016→017→018→019→021) |
| `(WorkOrder)-[:FOLLOWS]->(WorkOrder)` | same project-station pair, consecutive weeks |

### Dashboard Panels

#### Panel 1 — Project Overview
All 8 projects: planned vs actual hours, variance %, products involved, completed units.

```cypher
MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)
MATCH (wo)-[r:SCHEDULED_IN]->(:Week)
RETURN
    p.project_id,
    p.project_name,
    sum(r.planned_hours)  AS total_planned,
    sum(r.actual_hours)   AS total_actual,
    round(
        (sum(r.actual_hours) - sum(r.planned_hours)) / sum(r.planned_hours) * 100,
        1
    ) AS variance_pct
ORDER BY p.project_id
```

Display: horizontal bar chart planned vs actual, table below with variance % in red if > 10%.

#### Panel 2 — Station Load by Week
Heat map showing which stations are overloaded in which weeks. Overload cells highlighted.

```cypher
MATCH (wo:WorkOrder)-[:AT_STATION]->(s:Station)
MATCH (wo)-[r:SCHEDULED_IN]->(w:Week)
RETURN
    s.station_code,
    s.station_name,
    w.week_id,
    sum(r.planned_hours) AS planned,
    sum(r.actual_hours)  AS actual,
    round(
        (sum(r.actual_hours) - sum(r.planned_hours)) / sum(r.planned_hours) * 100,
        1
    ) AS variance_pct
ORDER BY s.station_code, w.week_id
```

Display: Plotly heatmap (stations × weeks), cells red where variance_pct > 10%.

#### Panel 3 — Capacity Tracker
Weekly capacity vs demand, deficit weeks flagged red.

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:CapacitySnapshot)
RETURN
    w.week_id,
    c.total_capacity,
    c.total_planned,
    c.deficit,
    c.overtime_hours
ORDER BY w.week_id
```

Display: grouped bar chart capacity vs planned, deficit bars below zero shown red.

#### Panel 4 — Worker Coverage Matrix
Which workers cover which stations, SPOF stations flagged. Shows downstream risk via `FEEDS_INTO`.

```cypher
MATCH (s:Station)
OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)
WITH s,
     collect(DISTINCT w.name) AS coverers,
     count(DISTINCT w)        AS coverage_count
RETURN
    s.station_code,
    s.station_name,
    coverers,
    coverage_count,
    CASE WHEN coverage_count <= 1 THEN true ELSE false END AS is_spof
ORDER BY coverage_count ASC
```

Display: table with red badge on SPOF stations. Secondary query on click shows which projects depend on that station.