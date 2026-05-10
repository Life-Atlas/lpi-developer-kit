# Level 5 Answers

## Q2. Why Not Just SQL?

### SQL Query

```sql
SELECT 
    w.name AS replacement_worker,
    s.station_name,
    p.project_name
FROM workers w
JOIN production pr 
    ON pr.station_code = '016'
JOIN projects p 
    ON pr.project_id = p.project_id
JOIN stations s 
    ON s.station_code = pr.station_code
WHERE w.can_cover_stations LIKE '%016%'
AND w.name != 'Per Hansen';
```

### Cypher Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
MATCH (p:Project)-[:SCHEDULED_AT]->(s)
WHERE s.name = "Gjutning"
AND w.name <> "Per Hansen"
RETURN w.name AS replacement_worker,
       s.name AS station,
       p.name AS affected_project;
```

### What the Graph Version Makes Clear

The Cypher query is easier to follow because the relationships between workers, stations, and projects are directly visible in the query itself. In SQL, the same logic requires multiple joins and becomes harder to understand as the number of related tables grows. The graph structure also makes it much easier to expand the query later, for example by tracing downstream production impact or finding alternative coverage paths.

---

## Q3. Spot the Bottleneck

### 1. Bottleneck Analysis

The capacity dataset shows multiple deficit weeks, especially during weeks w1, w2, w4, w6, and w7 where planned production hours exceeded available factory capacity. Looking at the production data, the largest overloads were mainly caused by projects such as *Sjukhus Linköping ET2*, *Lagerhall Jönköping*, and *Bro E6 Halmstad*.

Stations like **FS IQB (011)**, **Gjutning (016)**, **Svets o montage IQB (014)**, and **SR B/F-hall (021)** frequently showed actual hours higher than planned hours. This indicates that these stations were operating under sustained pressure and contributed heavily to the factory deficits.

### 2. Cypher Query

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.name AS station,
       p.name AS project,
       r.planned_hours AS planned_hours,
       r.actual_hours AS actual_hours,
       ROUND(((r.actual_hours - r.planned_hours) / r.planned_hours) * 100, 2) AS variance_percent
ORDER BY variance_percent DESC;
```

### 3. Modeling the Bottleneck in the Graph

I would model bottlenecks as separate `(:Bottleneck)` nodes connected to both projects and stations. This makes the alert reusable and easier to analyze across different parts of the graph.

Example structure:

```text
(Project)-[:CAUSES]->(Bottleneck)
(Bottleneck)-[:AT]->(Station)
```

The bottleneck node could store properties such as:
- variance percentage
- affected week
- severity level
- overtime required

This structure would make it easier to visualize operational risks and run future analytics queries.

---

## Q4. Vector + Graph Hybrid

### 1. What Would I Embed?

I would embed project descriptions, product specifications, and project requirements such as delivery timelines or construction type. These fields carry the most semantic meaning and would help identify projects that are operationally similar even if they are not identical in product type.

### 2. Hybrid Query

Example hybrid workflow:

1. Use vector search to find projects with descriptions semantically similar to:
   > "450 meters of IQB beams for a hospital extension in Linköping"

2. From those results, run a graph query such as:

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE p.embedding_similarity > 0.85
AND r.actual_hours <= r.planned_hours * 1.05
RETURN p.name,
       collect(DISTINCT s.name) AS stations_used,
       AVG((r.actual_hours - r.planned_hours) / r.planned_hours) AS avg_variance;
```

This would return projects that are not only semantically similar, but also operationally efficient.

### 3. Why This Is Better Than Product Filtering

Filtering only by product type misses a lot of important context. Two projects may both use IQB beams but still differ heavily in workflow complexity, station usage, timeline pressure, or production efficiency.

Combining vector search with graph relationships gives a much more realistic understanding of similarity because it considers both semantic meaning and operational behavior. This leads to better planning, forecasting, and resource allocation decisions.

---

## Q5. My Level 6 Plan

### 1. Node Labels and CSV Mapping

| Node Label | CSV Source |
|------------|------------|
| Project | `project_id`, `project_name` from production data |
| Product | `product_type` |
| Station | `station_code`, `station_name` |
| Worker | `worker_id`, `name` |
| Week | `week` |
| Etapp | `etapp` |
| BOP | `bop` |
| Certification | `certifications` |
| Capacity | capacity dataset |

### 2. Relationship Types

| Relationship | Description |
|--------------|-------------|
| `PRODUCES` | Project produces a product |
| `SCHEDULED_AT` | Project scheduled at station with planned and actual hours |
| `OCCURS_IN` | Project occurs during a specific week |
| `PART_OF` | Project belongs to an etapp |
| `BELONGS_TO` | Project linked to BOP |
| `WORKS_AT` | Worker primary station |
| `CAN_COVER` | Worker can cover additional stations |
| `HAS_CERTIFICATION` | Worker certifications |
| `HAS_CAPACITY` | Week linked to capacity metrics |

### 3. Streamlit Dashboard Panels

#### Project Overview
Displays all projects with:
- total planned hours
- total actual hours
- variance percentage
- associated products

#### Station Load Dashboard
Interactive chart showing:
- station workload by week
- overload conditions
- planned vs actual comparison

#### Capacity Tracker
Shows:
- total capacity
- overtime usage
- planned demand
- weekly deficits

Deficit weeks will be highlighted in red.

#### Worker Coverage Matrix
Displays:
- workers mapped to stations
- backup coverage availability
- single-point-of-failure stations where only one worker is certified

### 4. Cypher Queries for the Dashboard

#### Project Overview Query

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN p.name,
       SUM(r.planned_hours) AS planned,
       SUM(r.actual_hours) AS actual;
```

#### Station Load Query

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN s.name,
       r.week,
       SUM(r.planned_hours) AS planned,
       SUM(r.actual_hours) AS actual;
```

#### Capacity Tracker Query

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
RETURN w.name,
       c.total_capacity,
       c.total_planned,
       c.deficit;
```

#### Worker Coverage Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN w.name,
       collect(s.name) AS covered_stations;
```