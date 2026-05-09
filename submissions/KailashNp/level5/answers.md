# Level 5 — Graph Thinking Answers

# Q1. Model It

I designed the graph schema around the core entities involved in factory production planning.

## Node Labels
- Project
- Product
- Station
- Worker
- Week
- Certification
- Bottleneck

## Relationship Types
- CONTAINS_PRODUCT
- PRODUCED_AT
- ASSIGNED_TO
- CERTIFIED_FOR
- SCHEDULED_IN
- OVERLOADED_IN
- CAUSES_ALERT
- WORKS_ON
- USES_STATION
- WORKED_AT

## Relationships With Properties

### Example 1
```cypher
(:Project)-[:USES_STATION {
    planned_hours: 40,
    actual_hours: 52
}]->(:Station)
```

### Example 2
```cypher
(:Worker)-[:WORKED_AT {
    hours: 38,
    week: "W1"
}]->(:Station)
```

The graph structure makes it easier to understand production flow, worker coverage, overload conditions, and dependencies between projects and stations.

---

# Q2. Why Not Just SQL?

## SQL Query

```sql
SELECT w.name, w.certification, p.project_name
FROM workers w
JOIN worker_certifications wc ON w.id = wc.worker_id
JOIN stations s ON wc.station_id = s.id
JOIN project_stations ps ON s.id = ps.station_id
JOIN projects p ON ps.project_id = p.id
WHERE s.station_name = '016 Gjutning'
AND w.name != 'Per Gustafsson';
```

## Cypher Query

```cypher
MATCH (w:Worker)-[:CERTIFIED_FOR]->(s:Station {name: "016 Gjutning"})
MATCH (p:Project)-[:USES_STATION]->(s)
WHERE w.name <> "Per Gustafsson"
RETURN w.name, p.name;
```

## Explanation

The SQL version requires multiple JOIN operations, making the relationships harder to follow. In the graph version, the connections between workers, stations, and projects are directly visible through relationships, making traversal and dependency analysis much more intuitive.

Graphs make it easier to reason about operational impact because the relationships themselves become first-class entities instead of hidden join logic.

---

# Q3. Spot the Bottleneck

## Projects/Stations Causing Overload

The overload occurs in stations where actual production hours consistently exceed planned hours, especially during weeks with capacity deficits shown in the capacity dataset.

Projects using overloaded stations contribute directly to bottlenecks because production demand exceeds available station capacity.

## Cypher Query

```cypher
MATCH (p:Project)-[r:USES_STATION]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.name AS station,
       p.name AS project,
       r.planned_hours,
       r.actual_hours,
       ((r.actual_hours - r.planned_hours) / r.planned_hours) * 100 AS variance_percent
ORDER BY variance_percent DESC;
```

## Alert Modeling

I would model bottlenecks using a dedicated `(:Bottleneck)` node connected to projects and stations.

Example:

```cypher
(:Project)-[:CAUSES_ALERT]->(:Bottleneck)
(:Station)-[:HAS_ALERT]->(:Bottleneck)
```

This allows bottlenecks to carry metadata such as severity, week, variance percentage, and status while remaining queryable as independent entities.

---

# Q4. Vector + Graph Hybrid

## What I Would Embed

I would embed:
- Project descriptions
- Product specifications
- Delivery timelines
- Worker skills
- Historical project summaries

These embeddings capture semantic similarity between projects and operational requirements.

## Hybrid Query

```cypher
MATCH (p:Project)-[:USES_STATION]->(s:Station)
WHERE p.variance < 5
AND s.name IN ["Cutting", "Welding", "Gjutning"]

WITH p
CALL db.index.vector.queryNodes(
    'project_embeddings',
    5,
    $embedding
)
YIELD node, score

RETURN node.name, score, p.name
ORDER BY score DESC;
```

## Why This Is Better

Filtering only by product type ignores operational complexity and project similarity.

The vector search finds semantically similar projects based on descriptions and requirements, while the graph filters ensure that operational constraints such as stations used and historical performance are also considered.

This creates much more accurate project matching and planning support.

---

# Q5. My Level 6 Plan

## Node Labels and CSV Mapping

### Project
Mapped from:
- project_id
- project_name

### Product
Mapped from:
- product_type
- product_id

### Station
Mapped from:
- station_id
- station_name

### Worker
Mapped from:
- worker_name
- role

### Week
Mapped from:
- week

### Certification
Mapped from:
- certifications

### Bottleneck
Generated dynamically from overload conditions.

---

## Relationship Types

### CONTAINS_PRODUCT
Created between projects and products.

### PRODUCED_AT
Created between products and stations.

### ASSIGNED_TO
Created between workers and stations.

### CERTIFIED_FOR
Created between workers and certifications/stations.

### USES_STATION
Created from production hours data.

### OVERLOADED_IN
Created when demand exceeds capacity.

### CAUSES_ALERT
Created when variance exceeds threshold.

---

## Streamlit Dashboard Panels

### 1. Station Load Heatmap
Shows overload and utilization across weeks.

### 2. Worker Coverage Matrix
Shows which workers can substitute for absent workers at specific stations.

### 3. Project Variance Dashboard
Displays planned vs actual hours grouped by station and project.

### 4. Bottleneck Alert Dashboard
Highlights stations and projects exceeding safe operational thresholds.

---

## Cypher Queries for Panels

### Station Load Heatmap

```cypher
MATCH (s:Station)-[:OVERLOADED_IN]->(w:Week)
RETURN s.name, w.name;
```

### Worker Coverage Matrix

```cypher
MATCH (w:Worker)-[:CERTIFIED_FOR]->(s:Station)
RETURN w.name, s.name;
```

### Project Variance Dashboard

```cypher
MATCH (p:Project)-[r:USES_STATION]->(s:Station)
RETURN p.name, s.name, r.planned_hours, r.actual_hours;
```

### Bottleneck Alerts

```cypher
MATCH (p:Project)-[:CAUSES_ALERT]->(b:Bottleneck)
RETURN p.name, b.severity, b.week;
```

---

# Conclusion

This graph-based approach provides a much clearer understanding of factory production dependencies, worker coverage, overload conditions, and operational bottlenecks compared to traditional spreadsheet-based workflows.

By combining graph relationships with vector similarity search, the system can support smarter planning, resource allocation, and future project matching in real-world industrial environments.