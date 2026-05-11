# Level 5 – Graph Thinking

# Q1 – Graph Schema Design

## Node Labels

| Node Label | Description | Example Properties |
|---|---|---|
| Worker | Factory workers/operators | worker_id, name, role |
| Certification | Worker certifications/skills | certification_name |
| Project | Factory construction projects | project_id, project_name |
| Product | Manufactured product types | product_type, quantity |
| Station | Production stations | station_code, station_name |
| Week | Weekly production schedule | week_id |
| Capacity | Weekly/station capacity data | total_capacity, total_planned, deficit |

---

## Relationship Types

| Relationship Type | From → To | Purpose |
|---|---|---|
| HAS_CERTIFICATION | Worker → Certification | Worker skill mapping |
| ASSIGNED_TO | Worker → Project | Worker assigned to project |
| WORKS_AT | Worker → Station | Worker primary station |
| DEPENDS_ON | Project → Station | Project depends on station |
| PRODUCES | Project → Product | Project uses/products |
| RUNS_ON | Product → Station | Product processed at station |
| SCHEDULED_IN | Project → Week | Weekly production schedule |
| HAS_CAPACITY | Week → Capacity | Weekly capacity tracking |
| HAS_CAPACITY | Station → Capacity | Station capacity information |

---

# Q2 – Why Not Just SQL?

## Problem Statement

> "Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is unavailable, and which projects would be affected?"

---

## SQL VERSION

```sql
SELECT 
    w.name AS replacement_worker,
    p.project_name AS affected_project,
    s.station_name
FROM workers w

JOIN stations s
    ON w.station_code = s.station_code

JOIN projects p
    ON p.station_code = s.station_code

WHERE s.station_code = '016'
AND w.name != 'Per Gustafsson';
```

### Explanation

Uses table joins to find workers connected to Station 016 and the projects dependent on that station.

---

## CYPHER VERSION

```cypher
MATCH (per:Worker {name:"Per Gustafsson"})

MATCH (replacement:Worker)-[:WORKS_AT]->(s:Station {
    station_code:"016"
})

MATCH (p:Project)-[:DEPENDS_ON]->(s)

WHERE replacement <> per

RETURN
replacement.name AS replacement_worker,
p.project_name AS affected_project,
s.station_name AS station
```

### Explanation

Traverses graph relationships between Worker, Station, and Project nodes to identify replacement workers and affected projects for Station 016.

---

## Why Graph Makes This Easier?

The graph query directly follows operational relationships between workers, certifications, stations, and projects without requiring multiple table joins. In SQL, dependency analysis becomes harder to manage as additional workforce, station, and scheduling conditions are added. The graph structure also makes operational impact easier to visualize.

---

# Q3 — Spot the Bottleneck

## 1. Main Bottleneck Areas

From the capacity data:

- Week 1 deficit: `-132 hours`
- Week 2 deficit: `-125 hours`

### Main overload contributors

| Station | Issue |
|---|---|
| 011 – FS IQB | Extremely high actual hours across multiple projects |
| 014 – Svets o montage | Frequent overruns above planned hours |
| 016 – Gjutning | Only one primary worker and repeated over-capacity usage |

### Projects contributing most

- P05 – Sjukhus Linköping
- P03 – Lagerhall Jönköping

Stations where `actual_hours > planned_hours` by more than 10% were identified as bottlenecks.

---

## 2. Cypher Query

```cypher
MATCH (p:Project)-[r:RUNS_ON]->(s:Station)

WHERE r.actual_hours > r.planned_hours * 1.10

RETURN s.station_name AS station,

collect({
    project: p.project_name,
    planned: r.planned_hours,
    actual: r.actual_hours
}) AS overruns,

count(*) AS total_overruns

ORDER BY total_overruns DESC
```

### Explanation

This query:

- checks where actual hours exceed planned hours by more than 10%,
- groups overloaded projects by station,
- and identifies stations causing repeated production bottlenecks.

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

The bottleneck is tied to a specific production event, not a completely separate entity. Using relationship properties keeps the overload information directly connected to the station-processing activity and makes bottleneck detection easier during graph traversal.

---

# Q4 — Vector + Graph Hybrid

## 1. What Should Be Embedded?

Embed project descriptions containing:

- project descriptions
- product specifications
- delivery timelines
- station capabilities
- worker skills/certifications
- historical project notes

### Example embedded project text

```text
"450 meters of IQB beams for hospital extension in Linköping, tight delivery timeline, high welding workload"
```

This allows semantic similarity matching between new and past projects.

---

## 2. Hybrid Query

```cypher
-- Vector similarity + graph filtering --

MATCH (p:Project)

WHERE vector.similarity(
p.embedding,
$new_project_embedding
) > 0.85

MATCH (p)-[r:RUNS_ON]->(s:Station)

WHERE r.actual_hours <= r.planned_hours * 1.05

RETURN
p.project_name AS similar_project,

collect(DISTINCT s.station_name) AS stations_used,

avg(
(r.actual_hours-r.planned_hours)
/r.planned_hours
) AS variance

ORDER BY variance ASC
```

### Explanation

The vector search finds semantically similar past projects.

The graph query verifies:

- same operational stations,
- and low production variance.

This combines semantic similarity with operational reliability.

---

## 3. Why Better Than Product Filtering?

Vector search understands semantic similarity, not just exact product matches. Two projects may use different products but still share similar production complexity, timelines, station usage, or workforce requirements.

Combining vector search with graph traversal makes it possible to find projects that are both operationally similar and historically efficient.

---

# Q5 — Level 6 Blueprint

## 1. Node Labels and CSV Mapping

| CSV File | Node Label | Columns Mapped |
|---|---|---|
| factory_production.csv | Project | project_id, project_name |
| factory_production.csv | Product | product_type, quantity |
| factory_production.csv | Station | station_code, station_name |
| factory_capacity.csv | Week | week |
| factory_capacity.csv | Capacity | total_capacity, total_planned, deficit |
| factory_workers.csv | Worker | worker_id, name, role, type |
| factory_workers.csv | Certification | certifications |

---

## 2. Relationship Types and What Creates Them

| Relationship | Created From |
|---|---|
| WORKS_AT | worker.primary_station = station.station_code |
| HAS_CERTIFICATION | worker certification data |
| ASSIGNED_TO | worker-project assignment |
| PRODUCES | project product mapping |
| RUNS_ON | product processed at station |
| SCHEDULED_IN | production week |
| DEPENDS_ON | project uses station |
| HAS_CAPACITY | week-capacity mapping |

---

## 3. Streamlit Dashboard Panels

| Dashboard Panel | Purpose |
|---|---|
| Project Timeline Heatmap | visualize weekly project workload |
| Station Load Bar Chart | compare planned vs actual hours |
| Worker Coverage Matrix | identify backup workers for stations |
| Bottleneck Alert Dashboard | show overloaded stations/projects |
| Capacity Deficit Trend | track weekly overload patterns |

---

## 4. Cypher Queries Powering Each Panel

### Project Timeline Heatmap

```cypher
MATCH (p:Project)-[:SCHEDULED_IN]->(w:Week)

RETURN
p.project_name,
w.week_id
```

---

### Station Load Bar Chart

```cypher
MATCH (p:Project)-[r:RUNS_ON]->(s:Station)

RETURN
s.station_name,
sum(r.planned_hours) AS planned,
sum(r.actual_hours) AS actual
```

---

### Worker Coverage Matrix

```cypher
MATCH (w:Worker)-[:WORKS_AT]->(s:Station)

RETURN
s.station_name,
collect(w.name) AS workers
```

---

### Bottleneck Alert Dashboard

```cypher
MATCH (p:Project)-[r:RUNS_ON]->(s:Station)

WHERE r.actual_hours > r.planned_hours * 1.10

RETURN
s.station_name,
p.project_name,
r.actual_hours,
r.planned_hours
```