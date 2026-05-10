# Level 5 — Graph Thinking

## Q1. Model It

I designed the graph around the operational production flow of the factory. The central entity is the `Project`, which connects to products, stations, workers, and weeks.

The graph contains the following node labels:

- Project
- ProductType
- Station
- Worker
- Week
- Certification
- Bottleneck

The graph contains the following relationship types:

- PRODUCES
- USES_STATION
- RUNS_IN
- PRIMARY_AT
- CAN_COVER
- HAS_CERTIFICATION
- WORKS_ON
- CAPACITY_STATUS
- HAS_BOTTLENECK
- AFFECTS

Operational production metrics such as `planned_hours`, `actual_hours`, `completed_units`, and `week` are stored on the `USES_STATION` relationship because they describe the interaction between a project and a station during a specific production period.

The graph structure makes it possible to traverse staffing dependencies, production bottlenecks, and station utilization directly without relying on complex relational joins.

The schema diagram is included in `schema.md`.

---

## Q2. Why Not Just SQL?

### SQL Query

```sql
SELECT DISTINCT
    w2.name AS replacement_worker,
    p.project_name
FROM workers w1
JOIN stations s
    ON w1.primary_station = s.station_code
JOIN workers w2
    ON w2.can_cover_stations LIKE CONCAT('%', s.station_code, '%')
JOIN production pr
    ON pr.station_code = s.station_code
JOIN projects p
    ON p.project_id = pr.project_id
WHERE w1.name = 'Per Gustafsson'
AND s.station_code = '016'
AND w2.name <> w1.name;
```

### Cypher Query

```cypher
MATCH (per:Worker {name:"Per Gustafsson"})-[:PRIMARY_AT]->(s:Station {code:"016"})

MATCH (backup:Worker)-[:CAN_COVER]->(s)

MATCH (p:Project)-[:USES_STATION]->(s)

WHERE backup.name <> per.name

RETURN
    s.name,
    collect(DISTINCT backup.name) AS replacement_workers,
    collect(DISTINCT p.project_name) AS affected_projects
```

### Comparison

The SQL version hides operational relationships inside multiple joins and filtering conditions. The Cypher query directly expresses the traversal path between workers, stations, and affected projects, making staffing dependencies easier to understand and analyze.

The graph structure also makes it easier to expand the query later, for example by including certifications, overtime risk, or multi-station worker coverage.

---

## Q3. Spot the Bottleneck

The capacity dataset shows recurring production deficits in multiple weeks, especially during w1, w2, w4, w6, and w7. This suggests structural overload rather than isolated production delays.

Projects where actual production hours consistently exceed planned hours are likely contributing to bottleneck conditions at specific stations.

### Cypher Query

```cypher
MATCH (p:Project)-[r:USES_STATION]->(s:Station)

WHERE r.actual_hours > r.planned_hours * 1.10

RETURN
    s.station_name AS station,
    p.project_name AS project,
    r.week AS week,
    r.planned_hours,
    r.actual_hours,
    ROUND(
        ((r.actual_hours - r.planned_hours) / r.planned_hours) * 100,
        2
    ) AS variance_pct

ORDER BY variance_pct DESC
```

### Bottleneck Modeling

I would model bottlenecks as separate nodes instead of boolean flags.

Example:

```text
(:Station)-[:HAS_BOTTLENECK]->(:Bottleneck)
```

The bottleneck node can store:

- severity
- overload percentage
- affected week
- capacity deficit
- impacted projects

This approach allows the graph to track recurring operational issues over time and analyze how bottlenecks propagate through projects and staffing dependencies.

---

## Q4. Vector + Graph Hybrid

I would embed:

- project descriptions
- product specifications
- customer requirements
- delivery constraints
- production notes
- timeline urgency

These fields contain semantic meaning that vector embeddings can compare effectively.

### Hybrid Query

```cypher
CALL db.index.vector.queryNodes(
  'project_embeddings',
  5,
  $embedding
)
YIELD node, score

MATCH (node)-[r:USES_STATION]->(s:Station)

WHERE r.actual_hours <= r.planned_hours * 1.05

RETURN
    node.project_name,
    score,
    collect(s.station_name) AS stations_used

ORDER BY score DESC
```

### Why Hybrid Retrieval Is Useful

Vector similarity identifies semantically similar projects based on textual meaning and operational context.

The graph layer validates operational similarity using shared stations, production flows, and performance metrics such as low variance between planned and actual production hours.

This is more useful than filtering only by product type because projects with similar operational complexity may use different products while still requiring similar workflows, staffing, and station utilization.

This same hybrid pattern can also be applied to people matching systems such as Boardy, where embeddings identify similar needs or offers while the graph validates social or professional relationships.

---

## Q5. Your L6 Plan

### Node Mapping

| CSV Column | Node |
|---|---|
| project_id | Project |
| project_name | Project |
| product_type | ProductType |
| station_code | Station |
| station_name | Station |
| week | Week |
| worker_id | Worker |
| certifications | Certification |

---

### Relationship Mapping

| Relationship | Source |
|---|---|
| PRODUCES | factory_production.csv |
| USES_STATION | factory_production.csv |
| RUNS_IN | factory_production.csv |
| PRIMARY_AT | factory_workers.csv |
| CAN_COVER | factory_workers.csv |
| HAS_CERTIFICATION | factory_workers.csv |
| CAPACITY_STATUS | factory_capacity.csv |

---

### Streamlit Dashboard Panels

#### 1. Station Overload Heatmap

Purpose:
Visualize overload conditions by station and week.

Cypher Query:

```cypher
MATCH (p:Project)-[r:USES_STATION]->(s:Station)

RETURN
    s.station_name,
    r.week,
    SUM(r.actual_hours - r.planned_hours) AS overload
```

---

#### 2. Worker Coverage Matrix

Purpose:
Show which workers can replace each other across stations.

Cypher Query:

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)

RETURN
    w.name,
    collect(s.station_name) AS coverage
```

---

#### 3. Project Variance Leaderboard

Purpose:
Identify projects with the largest production overruns.

Cypher Query:

```cypher
MATCH (p:Project)-[r:USES_STATION]->()

RETURN
    p.project_name,
    ROUND(
        SUM(r.actual_hours) / SUM(r.planned_hours),
        2
    ) AS variance_ratio

ORDER BY variance_ratio DESC
```

---

### Technologies

For Level 6 I plan to use:

- Neo4j for the graph database
- Cypher for graph queries
- pandas for CSV ingestion and transformation
- Streamlit for dashboard visualization
- Vector embeddings for semantic project similarity search

The graph database will allow the dashboard to analyze production dependencies, staffing flexibility, and bottleneck propagation more naturally than a relational model.
