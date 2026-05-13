# Level 5 — Graph Thinking

## Q1. Factory Graph Design

The factory graph schema models production flow, worker coverage, station workload, and weekly capacity pressure.

The schema diagram is provided in:

- `schema.md`

Key design choices:
- workload metrics stored directly on relationships
- worker backup coverage modeled separately from primary assignment
- weekly overload conditions represented independently from production records

This structure supports:
- bottleneck analysis
- staffing replacement queries
- variance tracking
- hybrid vector + graph search

---

# Q2. SQL vs Cypher

## SQL Query

```sql
SELECT
    w.name,
    w.can_cover_stations,
    p.project_name
FROM workers w
JOIN production pr
    ON pr.station_code = '016'
JOIN projects p
    ON p.project_id = pr.project_id
WHERE w.can_cover_stations LIKE '%016%'
AND w.name != 'Per Gustafsson';
```

---

## Cypher Query

```cypher
MATCH (w:Worker)-[:BACKUP_FOR]->(s:Station {station_code: "016"})
MATCH (p:Project)-[:FLOWS_THROUGH]->(s)
WHERE w.worker_name <> "Per Gustafsson"

RETURN
    w.worker_name AS backup_worker,
    s.station_name AS station,
    collect(DISTINCT p.project_name) AS affected_projects
```

---

## Why the Graph Version Is Better

The Cypher query directly models operational relationships:
workers → stations → projects.

In SQL, the logic is spread across multiple joins and indirect foreign key connections.  
The graph query makes worker replacement impact much easier to understand visually and operationally.

The graph model also scales better when adding:
- skill matching
- multi-station routing
- dependency chains
- overtime propagation

---

# Q3. Bottleneck Analysis

From `factory_capacity.csv`:

- Week W04 shows planned demand exceeding available capacity
- Week W06 has one of the highest workload deficits in the dataset

Using production records from `factory_production.csv`, the largest overload contributors include:

| Project | Station | Planned Hours | Actual Hours |
|---|---|---|---|
| Project 104 | Station 016 | 72 | 88 |
| Project 107 | Station 020 | 64 | 79 |
| Project 102 | Station 012 | 55 | 67 |

These projects exceeded planned workload by more than 10%, increasing station pressure and creating downstream scheduling delays.

---

## Cypher Query

```cypher
MATCH (p:Project)-[w:WORKLOAD]->(s:Station)

WHERE w.actual_hours > (w.planned_hours * 1.10)

RETURN
    s.station_name AS station,
    collect(p.project_name) AS overloaded_projects,
    avg(w.actual_hours - w.planned_hours) AS avg_variance
ORDER BY avg_variance DESC
```

---

## Bottleneck Modeling Strategy

I would model bottlenecks using a dedicated relationship property instead of separate bottleneck nodes.

Example:

```cypher
(:Project)-[:WORKLOAD {
    planned_hours: 72,
    actual_hours: 88,
    overloaded: true
}]->(:Station)
```

This keeps operational queries simpler and avoids unnecessary node expansion for dashboard analytics.

---

# Q4. Hybrid Vector + Graph Search

## What I Would Embed

I would embed:
- project descriptions
- product specifications
- delivery requirements
- station usage patterns
- production timelines

This allows semantic similarity matching between incoming and historical projects.

---

## Hybrid Query

### Vector Search Stage
Find projects with semantically similar descriptions:

```text
"450 meters of IQB beams for a hospital extension"
```

---

### Graph Filtering Stage

```cypher
MATCH (p:Project)-[:FLOWS_THROUGH]->(s:Station)

WHERE p.similarity_score > 0.85
AND p.production_variance < 0.05

RETURN
    p.project_name,
    collect(DISTINCT s.station_name) AS stations_used
```

---

## Why Hybrid Search Is Better

Filtering only by product type ignores:
- timeline pressure
- production complexity
- routing similarity
- workload behavior

Vector search captures semantic similarity, while graph filtering validates operational compatibility.

This combination is useful for:
- production planning
- estimating delivery risk
- predicting overload conditions
- finding reusable factory workflows

---

# Q5. Level 6 Blueprint

## Planned Node Labels

| Node | CSV Source |
|---|---|
| Project | factory_production.csv |
| Product | factory_production.csv |
| Station | factory_production.csv |
| Worker | factory_workers.csv |
| Week | factory_production.csv |
| WeeklyLoad | factory_capacity.csv |
| Skill | factory_workers.csv |
| JobType | factory_workers.csv |

---

## Planned Relationships

| Relationship | Source |
|---|---|
| BUILDS | production records |
| FLOWS_THROUGH | station workflow |
| RUNS_DURING | weekly production |
| WORKLOAD | planned vs actual hours |
| ASSIGNED_TO | worker primary station |
| BACKUP_FOR | worker coverage stations |
| HAS_SKILL | certifications |
| HAS_JOB | worker role |
| WEEKLY_STATUS | capacity tracking |

---

## Planned Dashboard Pages

### 1. Project Overview
Shows:
- all active projects
- total planned vs actual hours
- production completion metrics

### Cypher Query

```cypher
MATCH (p:Project)-[w:WORKLOAD]->()

RETURN
    p.project_name,
    sum(w.planned_hours),
    sum(w.actual_hours)
```

---

### 2. Station Load Dashboard

Shows:
- overloaded stations
- workload variance
- station utilization

### Cypher Query

```cypher
MATCH (:Project)-[w:WORKLOAD]->(s:Station)

RETURN
    s.station_name,
    sum(w.actual_hours),
    sum(w.planned_hours)
```

---

### 3. Capacity Tracker

Shows:
- weekly deficits
- overtime pressure
- overload trends

### Cypher Query

```cypher
MATCH (s:Station)-[r:WEEKLY_STATUS]->(wl:WeeklyLoad)

RETURN
    wl.total_capacity,
    wl.total_planned,
    wl.deficit
```

---

### 4. Worker Coverage Matrix

Shows:
- station staffing
- backup coverage
- single points of failure

### Cypher Query

```cypher
MATCH (w:Worker)-[:BACKUP_FOR]->(s:Station)

RETURN
    s.station_name,
    collect(w.worker_name)
```

---

# Final Notes

One important design decision in my implementation was keeping operational metrics directly on graph relationships instead of introducing unnecessary intermediate nodes.

This keeps:
- Cypher queries shorter
- dashboard aggregation faster
- bottleneck analysis easier to maintain

The graph structure is designed specifically for operational factory analytics rather than generic entity storage.
