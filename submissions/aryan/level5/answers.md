# Level 5 — Graph Thinking

## Q1. Model It

Schema diagram provided in `schema.md`.

### Summary

The graph models:
- projects
- products
- stations
- workers
- certifications
- capacity planning
- weekly production execution
- bottleneck alerts

The schema emphasizes:
1. operational dependencies
2. station overload analysis
3. worker substitution coverage
4. temporal production flow
5. future vector + graph hybrid search

---

# Q2. Why Not Just SQL?

## SQL Version

```sql
SELECT
    w.name,
    w.worker_id,
    s.station_name,
    p.project_name
FROM workers w
JOIN worker_station_coverage c
    ON w.worker_id = c.worker_id
JOIN stations s
    ON c.station_code = s.station_code
JOIN production pr
    ON pr.station_code = s.station_code
JOIN projects p
    ON p.project_id = pr.project_id
WHERE s.station_code = '016'
AND w.name != 'Per Gustafsson';
```

---

## Cypher Version

```cypher
MATCH (vacationWorker:Worker {name: "Per Gustafsson"})
MATCH (replacement:Worker)-[:CAN_COVER]->(s:Station {station_code: "016"})
MATCH (p:Project)-[u:USES_STATION]->(s)
WHERE replacement <> vacationWorker
RETURN
    replacement.name AS replacement_worker,
    s.station_name AS station,
    collect(DISTINCT p.project_name) AS affected_projects;
```

---

## What the Graph Version Makes Obvious

The graph query directly expresses relationships:
- workers covering stations
- projects depending on stations
- operational dependency paths

Cypher models the business reality as traversals through connected entities. SQL hides this logic behind multiple joins and intermediate tables, making operational dependency analysis harder to reason about and extend.

---

# Q3. Spot the Bottleneck

## Projects/Stations Causing Overload

Using `factory_capacity.csv` and production variance:

### Major overload contributors

| Week | Station | Likely Cause |
|---|---|---|
| w1 | 012 Förmontering IQB | Actual hours exceed plan |
| w1 | 014 Svets o montage IQB | Welding overhead |
| w2 | Multiple stations | Capacity deficit -125 |
| w4 | IQB workflow stations | Sustained overload |
| w6 | Reduced own staff capacity | Only 9 permanent workers |
| w7 | High planned workload | Planned 600 vs capacity 520 |

### Observations

- IQB production flow dominates overload periods.
- Welding and pre-assembly stations appear repeatedly in overrun paths.
- Staffing reductions in w6 increase deficit risk.
- Overtime temporarily compensates but does not eliminate overload.

---

## Cypher Query

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
WHERE u.actual_hours > (u.planned_hours * 1.10)

RETURN
    s.station_name AS station,
    p.project_name AS project,
    u.week AS week,
    u.planned_hours AS planned,
    u.actual_hours AS actual,
    ROUND(
        ((u.actual_hours - u.planned_hours) / u.planned_hours) * 100,
        2
    ) AS variance_pct
ORDER BY variance_pct DESC;
```

---

## Bottleneck Modeling Strategy

Best approach:
- explicit `(:BottleneckAlert)` nodes

Example:

```cypher
(:BottleneckAlert {
    severity: "high",
    variance_pct: 22.5,
    week: "w2"
})
```

Relationships:

```cypher
(:BottleneckAlert)-[:AT_STATION]->(:Station)
(:BottleneckAlert)-[:AFFECTS_PROJECT]->(:Project)
(:BottleneckAlert)-[:DURING]->(:Week)
```

Why this works:
- alerts become queryable historical entities
- supports trend analysis
- enables graph analytics on recurring bottlenecks
- easier integration with dashboards and notifications

---

# Q4. Vector + Graph Hybrid

## What Would Be Embedded?

### Primary embeddings
- project descriptions
- customer requirements
- production notes
- product specifications

### Secondary embeddings
- worker skills/certifications
- station capabilities
- historical bottleneck summaries

---

## Hybrid Query

### Vector Search

Find semantically similar projects:

```python
embedding("450 meters of IQB beams for hospital extension")
```

Retrieve top-k similar projects.

---

### Graph Filter

```cypher
MATCH (candidate:Project)-[:PRODUCES]->(:Product)-[:PROCESSED_AT]->(s:Station)

MATCH (candidate)-[u:USES_STATION]->(s)

WHERE candidate.embedding_score > 0.85
AND abs(u.actual_hours - u.planned_hours) / u.planned_hours < 0.05

RETURN
    candidate.project_name,
    collect(DISTINCT s.station_name) AS stations,
    avg(
        abs(u.actual_hours - u.planned_hours) / u.planned_hours
    ) AS avg_variance
ORDER BY candidate.embedding_score DESC;
```

---

## Why This Is Better Than Product Filtering

Product filtering only matches structured attributes like:
- IQB
- beam
- dimensions

Vector + graph hybrid search additionally captures:
- semantic similarity
- operational similarity
- station workflow similarity
- execution reliability
- timeline complexity

Two projects may use the same product type but have completely different:
- staffing requirements
- bottlenecks
- risk profiles
- production flows

The hybrid approach captures operational reality instead of just metadata.

---

# Q5. Your L6 Plan

## 1. Node Labels + CSV Mapping

| Node Label | CSV Columns |
|---|---|
| `Project` | project_id, project_number, project_name |
| `Product` | product_type, unit, quantity, unit_factor |
| `Station` | station_code, station_name, etapp, bop |
| `Worker` | worker_id, name, hours_per_week |
| `Certification` | certifications |
| `Role` | role |
| `EmploymentType` | type |
| `Week` | week |
| `Capacity` | all capacity metrics |
| `BottleneckAlert` | generated dynamically |

---

## 2. Relationship Types

| Relationship | Created From |
|---|---|
| `PRODUCES` | project → product |
| `PROCESSED_AT` | product → station |
| `USES_STATION` | production rows |
| `ASSIGNED_TO` | worker primary_station |
| `CAN_COVER` | can_cover_stations |
| `HAS_CERTIFICATION` | certifications |
| `HAS_ROLE` | role |
| `EMPLOYED_AS` | type |
| `SCHEDULED_IN` | week |
| `HAS_CAPACITY` | capacity rows |

---

## 3. Streamlit Dashboard Panels

### A. Station Load Heatmap
Shows:
- planned vs actual hours
- overload intensity by week

Cypher:

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
RETURN
    s.station_name,
    u.week,
    sum(u.planned_hours),
    sum(u.actual_hours);
```

---

### B. Worker Coverage Matrix
Shows:
- which workers can replace others
- certification overlap
- station redundancy

Cypher:

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN w.name, collect(s.station_name);
```

---

### C. Bottleneck Timeline Dashboard
Shows:
- recurring overload stations
- weekly variance spikes
- severity trends

Cypher:

```cypher
MATCH (b:BottleneckAlert)-[:AT_STATION]->(s:Station)
RETURN
    s.station_name,
    b.week,
    b.variance_pct,
    b.severity;
```

---

### D. Project Execution Variance
Shows:
- projects exceeding plan
- variance percentage
- affected stations

Cypher:

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
RETURN
    p.project_name,
    s.station_name,
    u.planned_hours,
    u.actual_hours;
```

---

### E. Capacity vs Demand Dashboard
Shows:
- total weekly capacity
- total planned load
- overtime usage
- deficit trends

Cypher:

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
RETURN
    w.week,
    c.total_capacity,
    c.total_planned,
    c.deficit,
    c.overtime_hours;
```

---

# Final Architecture

## Neo4j
Stores:
- operational graph
- dependencies
- bottlenecks
- worker coverage
- station relationships

## Vector Database
Stores:
- project embeddings
- specification embeddings
- production notes

## Streamlit
Provides:
- operational dashboards
- bottleneck analytics
- staffing visualization
- production planning support

This architecture directly scales into:
- VSAB Dashboard
- Boardy matching engine
- Factory digital twin systems
- production optimization workflows
