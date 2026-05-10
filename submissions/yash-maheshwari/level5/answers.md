# Level 5 — Graph Thinking

# Q1 — Graph Schema Design

## Node Labels

| Node | Main Properties | Source CSV |
|---|---|---|
| `Project` | project_id, project_name | production |
| `Product` | product_type, unit | production |
| `Station` | station_code, station_name | production |
| `Worker` | worker_id, name, role | workers |
| `Week` | week_id, capacity, deficit | capacity |
| `Certification` | cert_name | workers |
| `WorkPackage` | etapp, bop | production |

---

## Relationship Types

| Relationship | Description |
|---|---|
| `BELONGS_TO` | WorkPackage → Project |
| `PROCESSED_AT` | WorkPackage → Station |
| `SCHEDULED_IN` | WorkPackage → Week |
| `USES_PRODUCT` | WorkPackage → Product |
| `PRIMARY_STATION` | Worker → Station |
| `CAN_COVER` | Worker → Station |
| `HAS_CERTIFICATION` | Worker → Certification |
| `ACTIVE_IN` | Project → Week |
| `REPORTS_TO` | Worker → Worker |

---


---

# Q2 — Why Not Just SQL?

## Problem Statement

> "Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is unavailable, and which projects would be affected?"

---

## SQL Version

### -- Find backup workers for Station 016 --

```sql
SELECT w.worker_id, w.name, w.role
FROM workers w
WHERE '016' = ANY(string_to_array(w.can_cover_stations, ','))
AND w.worker_id != (
    SELECT worker_id
    FROM workers
    WHERE primary_station = '016'
);
```

### Explanation

This query checks which workers can cover Station 016 while excluding the primary assigned worker.

---

## Cypher Version

### -- Find substitutes and impacted projects together --

```cypher
MATCH (absent:Worker)-[:PRIMARY_STATION]->(s:Station {station_code: "016"})

MATCH (sub:Worker)-[:CAN_COVER]->(s)
WHERE sub.worker_id <> absent.worker_id

MATCH (wp:WorkPackage)-[:PROCESSED_AT]->(s)
MATCH (wp)-[:BELONGS_TO]->(proj:Project)

RETURN sub.name AS substitute,
       sub.role AS role,
       collect(DISTINCT proj.project_name) AS affected_projects
```

### Explanation

This query directly follows the graph path:

```text
Worker → Station → WorkPackage → Project
```

It identifies:
- who can substitute,
- which station is affected,
- and which projects depend on it.

---

## Why Graph Makes This Easier

In SQL, the logic is spread across multiple tables and joins.  
In Cypher, the query follows the real-world relationship flow directly.

The graph version makes dependencies visually obvious:
- which worker covers which station,
- which projects depend on that station,
- and how failures propagate.

Cypher focuses on connected paths, while SQL focuses on join logic.

---

# Q3 — Spot the Bottleneck

## 1. Main Bottleneck Areas

From the capacity data:

- **Week 1 deficit:** `-132 hours`
- **Week 2 deficit:** `-125 hours`

Main overload contributors:

| Station | Issue |
|---|---|
| `011 - FS IQB` | Extremely high actual hours across multiple projects |
| `014 - Svets o montage` | Frequent overruns above planned hours |
| `016 - Gjutning` | Only one primary worker and repeated over-capacity usage |

Projects contributing most:
- `P05 — Sjukhus Linköping`
- `P03 — Lagerhall Jönköping`

---

## 2. Cypher Query

### -- Find projects exceeding planned hours by 10% --

```cypher
MATCH (wp:WorkPackage)-[:PROCESSED_AT]->(s:Station)
MATCH (wp)-[:BELONGS_TO]->(proj:Project)

WHERE wp.actual_hours > wp.planned_hours * 1.10

RETURN s.station_code AS station,
       collect({
           project: proj.project_name,
           planned: wp.planned_hours,
           actual: wp.actual_hours
       }) AS overruns,
       count(*) AS total_overruns

ORDER BY total_overruns DESC
```

### Explanation

This query:
- checks where actual hours exceed planned hours by more than 10%,
- groups results by station,
- and highlights which stations repeatedly overload.

---

## 3. Bottleneck Modeling

### Recommended Approach

Use a relationship property:

```text
PROCESSED_AT {
    variance_pct,
    alert: true
}
```

### Why?

The bottleneck is tied to a specific production event, not a completely separate entity.

---

# Q4 — Vector + Graph Hybrid

## 1. What Should Be Embedded?

Embed project descriptions containing:
- project type,
- product mix,
- stations used,
- quantity,
- location,
- timeline context.

Example:

```text
Hospital project using IQB beams with high welding load and tight schedule
```

We can also embed:
- worker skill profiles,
- certifications,
- project risk patterns.

---

## 2. Hybrid Query

### -- Vector similarity + graph filtering --

```cypher
WITH ["P03", "P05"] AS similar_projects

UNWIND similar_projects AS pid

MATCH (past:Project {project_id: pid})
MATCH (past)<-[:BELONGS_TO]-(wp:WorkPackage)-[:PROCESSED_AT]->(s:Station)

WITH past, s, wp,
     abs(wp.actual_hours - wp.planned_hours) / wp.planned_hours * 100 AS variance

WHERE variance < 5

RETURN past.project_name,
       collect(DISTINCT s.station_name) AS stations_used,
       avg(variance) AS avg_variance
```

### Explanation

The vector search finds semantically similar projects.  
The graph query verifies:
- same operational stations,
- and low execution variance.

This combines similarity + operational reliability.

---

## 3. Why Better Than Product Filtering?

Filtering only by product type gives weak matches.

Two projects may both use IQB beams but:
- have different scale,
- worker requirements,
- timelines,
- or station loads.

Vector search captures project meaning and context.  
Graph filtering validates operational similarity.

Together they answer:

> "Which past projects were both semantically AND operationally similar?"

---

# Q5 — Level 6 Blueprint

## 1. Node Mapping

| Node | CSV Mapping |
|---|---|
| `Project` | project_id, project_name |
| `WorkPackage` | etapp, bop |
| `Station` | station_code, station_name |
| `Product` | product_type |
| `Worker` | worker_id, role |
| `Certification` | certifications |
| `Week` | capacity + deficit data |

---

## 2. Relationship Mapping

| Relationship | Created From |
|---|---|
| `BELONGS_TO` | project_id + work package |
| `PROCESSED_AT` | production rows |
| `SCHEDULED_IN` | week column |
| `USES_PRODUCT` | product_type |
| `PRIMARY_STATION` | worker primary station |
| `CAN_COVER` | cover station list |
| `HAS_CERTIFICATION` | certification list |

---

## 3. Streamlit Dashboard Panels

### Panel 1 — Station Load Heatmap

Shows:
- planned vs actual hours,
- overload zones,
- weekly station pressure.

#### Query

```cypher
MATCH (wp:WorkPackage)-[:PROCESSED_AT]->(s:Station)
MATCH (wp)-[:SCHEDULED_IN]->(w:Week)

RETURN w.week_id,
       s.station_code,
       sum(wp.planned_hours) AS planned,
       sum(wp.actual_hours) AS actual
```

---

### Panel 2 — Worker Coverage Matrix

Shows:
- primary workers,
- backup workers,
- station dependency risks.

#### Query

```cypher
MATCH (s:Station)

OPTIONAL MATCH (p:Worker)-[:PRIMARY_STATION]->(s)
OPTIONAL MATCH (b:Worker)-[:CAN_COVER]->(s)

RETURN s.station_code,
       p.name,
       collect(DISTINCT b.name)
```

---

### Panel 3 — Project Variance Tracker

Tracks:
- planned vs actual hours,
- variance percentage,
- risky projects.

#### Query

```cypher
MATCH (proj:Project)<-[:BELONGS_TO]-(wp:WorkPackage)
MATCH (wp)-[:SCHEDULED_IN]->(w:Week)

RETURN proj.project_name,
       w.week_id,
       sum(wp.planned_hours) AS planned,
       sum(wp.actual_hours) AS actual
```

---

# Final Notes

This schema is designed to support:
- production planning,
- bottleneck detection,
- workforce substitution analysis,
- and future vector + graph hybrid search systems.

It also directly connects with the Level 6 implementation workflow using:
- Neo4j,
- Cypher queries,
- and Streamlit dashboards.
