# Level 5 — Graph Thinking  
### DIA Vats

---

# Q1. Model It

See `schema.md` for the graph schema and `schema.png` for the rendered diagram.

## Schema Summary

### Node Labels
- `Project`
- `WorkOrder`
- `Station`
- `Product`
- `Week`
- `Worker`
- `Certification`
- `CapacitySnapshot`

### Relationship Types
- `HAS_WORKORDER`
- `AT_STATION`
- `PRODUCES`
- `SCHEDULED_IN`
- `FEEDS_INTO`
- `FOLLOWS`
- `ASSIGNED_TO`
- `CAN_COVER`
- `CERTIFIED_IN`
- `REQUIRES`
- `HAS_CAPACITY`

### Relationships Carrying Data
- `(WorkOrder)-[:SCHEDULED_IN]->(Week)`  
  Properties: `planned_hours`, `actual_hours`, `completed_units`

- `(Project)-[:PRODUCES]->(Product)`  
  Properties: `quantity`, `unit_factor`

## Design Choice

I used `WorkOrder` as the operational layer of the graph instead of treating every CSV row as just a relationship. A project can pass through multiple stations and weeks, so separating work execution from the project itself made the graph easier to reason about operationally.

I also added `FEEDS_INTO` relationships between stations to represent production flow. Without that, bottlenecks look isolated. With it, downstream impact becomes visible.

---

# Q2. Why Not Just SQL?

## SQL Version

```sql
-- Workers who can cover Station 016
SELECT
    w.name,
    w.role,
    w.certifications
FROM workers w
WHERE w.worker_id != 'W07'
  AND '016' = ANY(string_to_array(w.can_cover_stations, ','));

-- Projects affected by Station 016
SELECT DISTINCT
    p.project_id,
    p.project_name
FROM production_entries pe
JOIN projects p
ON pe.project_id = p.project_id
WHERE pe.station_code = '016';
```

## Cypher Version

```cypher
MATCH (s:Station {station_code:'016'})

MATCH (w:Worker)-[:CAN_COVER]->(s)
WHERE w.worker_id <> 'W07'

MATCH (wo:WorkOrder)-[:AT_STATION]->(s)
MATCH (p:Project)-[:HAS_WORKORDER]->(wo)

OPTIONAL MATCH (w)-[:CERTIFIED_IN]->(c:Certification)

RETURN
    w.name AS backup_worker,
    collect(DISTINCT c.name) AS certifications,
    collect(DISTINCT p.project_name) AS affected_projects
```

## What the Graph Makes Clear

The SQL version answers the question, but the graph version makes the operational dependency visible immediately.

Station 016 connects directly to both worker coverage and active project flow. In this dataset, Victor Elm is effectively the only backup for that station, so multiple projects depend on one fallback path. That kind of risk becomes obvious when traversing the graph.

---

# Q3. Spot the Bottleneck

## Capacity Deficit Weeks

From `factory_capacity.csv`:

| Week | Capacity | Planned | Deficit |
|---|---|---|---|
| w1 | 480 | 612 | -132 |
| w2 | 520 | 645 | -125 |
| w4 | 500 | 550 | -50 |
| w6 | 440 | 520 | -80 |
| w7 | 520 | 600 | -80 |

## Main Bottleneck Areas

The largest overruns are concentrated around:

- Station `016` — Gjutning
- Station `018` — SB B/F-hall
- Station `014` — Svets o montage IQB

Example overruns from the dataset:

| Project | Station | Planned | Actual | Variance |
|---|---|---|---|---|
| P03 | 016 | 28 | 35 | +25% |
| P05 | 016 | 35 | 40 | +14.3% |
| P08 | 016 | 22 | 25 | +13.6% |
| P04 | 018 | 19 | 22 | +15.8% |

Station 016 stands out because the overload is repeated across multiple projects while also depending heavily on a very small worker pool.

## Cypher Query

```cypher
MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)
MATCH (wo)-[:AT_STATION]->(s:Station)
MATCH (wo)-[r:SCHEDULED_IN]->(w:Week)

WHERE r.actual_hours > r.planned_hours * 1.1

RETURN
    s.station_code,
    s.station_name,
    collect(DISTINCT p.project_name) AS affected_projects,
    round(
        avg(
            (r.actual_hours - r.planned_hours)
            / r.planned_hours * 100
        ),1
    ) AS avg_variance_pct,
    sum(r.actual_hours - r.planned_hours) AS excess_hours

ORDER BY avg_variance_pct DESC
```

## Bottleneck Modelling

I would model bottlenecks as a property on the scheduling relationship rather than creating a separate node.

Example:

```cypher
SET r.is_bottleneck = true
```

In this case the bottleneck is tied to a specific station-week execution event, so keeping it on the relationship feels more practical and easier to query during dashboard aggregation.

---

# Q4. Vector + Graph Hybrid

## What I Would Embed

I would embed project-level operational descriptions containing:
- project type
- product mix
- quantity scale
- station sequence
- variance history

Example:

```text
Hospital extension project using IQB + IQP products with high load on stations 011, 012, 014 and 016
```

This captures both semantic similarity and operational complexity.

## Hybrid Query

```cypher
CALL db.index.vector.queryNodes(
    'project_embeddings',
    10,
    $query_embedding
)
YIELD node AS similar_project, score

MATCH (similar_project)-[:HAS_WORKORDER]->(wo:WorkOrder)
MATCH (wo)-[:AT_STATION]->(s:Station)
MATCH (wo)-[r:SCHEDULED_IN]->(:Week)

WITH similar_project,
     score,
     collect(DISTINCT s.station_code) AS stations_used,
     avg(
        abs(
            (r.actual_hours - r.planned_hours)
            / r.planned_hours
        ) * 100
     ) AS variance_pct

WHERE variance_pct < 5

RETURN
    similar_project.project_name,
    stations_used,
    round(variance_pct,2) AS variance_pct,
    round(score,3) AS similarity_score

ORDER BY similarity_score DESC
LIMIT 5
```

## Why Hybrid Search Helps

Filtering only by product type would return projects that may look similar on paper but behave very differently operationally.

The vector layer finds projects with similar scope and execution context. The graph layer filters for projects that actually moved through similar stations and stayed operationally stable.

Vector finds similarity. Graph filters for execution quality.

---

# Q5. My L6 Blueprint

## Node Mapping

| Node | CSV Source | Columns |
|---|---|---|
| `Project` | production | project_id, project_number, project_name |
| `WorkOrder` | production | planned_hours, actual_hours, completed_units |
| `Station` | production | station_code, station_name |
| `Product` | production | product_type, unit, unit_factor |
| `Week` | both | week |
| `Worker` | workers | worker_id, name, role, type |
| `Certification` | workers | certifications |
| `CapacitySnapshot` | capacity | total_capacity, total_planned, deficit |

---

## Relationship Mapping

| Relationship | Created From |
|---|---|
| `HAS_WORKORDER` | project_id |
| `AT_STATION` | station_code |
| `PRODUCES` | product_type |
| `SCHEDULED_IN` | week |
| `ASSIGNED_TO` | primary_station |
| `CAN_COVER` | can_cover_stations |
| `CERTIFIED_IN` | certifications |
| `HAS_CAPACITY` | week join |
| `FEEDS_INTO` | derived production flow |
| `FOLLOWS` | sequential work order progression |

---

## Streamlit Dashboard Panels

### 1. Project Overview

Shows:
- total planned vs actual hours
- variance %
- products involved
- completed units

Cypher:

```cypher
MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)

RETURN
    p.project_name,
    sum(wo.planned_hours) AS planned,
    sum(wo.actual_hours) AS actual,
    round(
        (
            sum(wo.actual_hours) - sum(wo.planned_hours)
        ) / sum(wo.planned_hours) * 100,
        1
    ) AS variance_pct
```

---

### 2. Station Load Dashboard

Shows:
- station load across weeks
- overload hotspots
- planned vs actual variance

Cypher:

```cypher
MATCH (wo:WorkOrder)-[:AT_STATION]->(s:Station)
MATCH (wo)-[r:SCHEDULED_IN]->(w:Week)

RETURN
    s.station_code,
    w.week_id,
    sum(r.planned_hours) AS planned,
    sum(r.actual_hours) AS actual
```

---

### 3. Capacity Tracker

Shows:
- weekly capacity
- planned demand
- deficit weeks highlighted

Cypher:

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:CapacitySnapshot)

RETURN
    w.week_id,
    c.total_capacity,
    c.total_planned,
    c.deficit
```

---

### 4. Worker Coverage Matrix

Shows:
- worker-to-station coverage
- stations with weak backup coverage
- single-point-of-failure stations

Cypher:

```cypher
MATCH (s:Station)

OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s)

RETURN
    s.station_code,
    collect(w.name) AS covering_workers,
    count(w) AS coverage_count
ORDER BY coverage_count ASC
```