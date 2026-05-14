# Level 5 Answers

## Q1. Model It

Refer to `schema.png` for the visual schema diagram. A supporting `schema.md` Mermaid version is also included for readability.

This factory production system is highly interconnected: projects produce different product types, each project passes through multiple stations across different weeks, workers are assigned to stations but can also provide backup coverage, and overall weekly capacity determines operational feasibility. A graph model is ideal here because these relationships are first-class entities and can be traversed naturally.

### Node Labels

- Project
- Product
- Station
- Worker
- Week
- Etapp
- BOP
- Certification
- Capacity

### Relationship Types

- `PRODUCES {qty, unit_factor}`
- `SCHEDULED_AT {planned_hours, actual_hours, completed_units}`
- `OCCURS_IN`
- `PART_OF`
- `BELONGS_TO`
- `WORKS_AT`
- `CAN_COVER`
- `HAS_CERTIFICATION`
- `HAS_CAPACITY {deficit, overtime}`

This schema captures both operational production flow and workforce planning while keeping the graph practical for analytics, scheduling, and dashboard queries

---

# Q2. Why Not Just SQL?

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
AND w.name <> 'Per Hansen';
```

### Cypher Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {station_code: "016"})
MATCH (p:Project)-[:SCHEDULED_AT]->(s)
WHERE w.name <> "Per Hansen"
RETURN
    w.name AS replacement_worker,
    s.station_name AS station,
    collect(DISTINCT p.project_name) AS affected_projects;
```

### Why Graph Is Better

The graph query directly mirrors the business question: *which workers can cover a station, and which projects depend on that station?* This relationship path is explicit and intuitive. In SQL, the same logic becomes harder to maintain because multiple joins are required and the relationship structure remains implicit. Graph traversal makes dependency analysis much clearer and easier to extend.

---

# Q3. Spot the Bottleneck

### 1. Bottleneck Analysis

The capacity dataset shows clear overload periods:

| Week | Capacity | Planned | Deficit |
|------|----------|---------|---------|
| w1 | 480 | 612 | -132 |
| w2 | 520 | 645 | -125 |
| w4 | 500 | 550 | -50 |
| w6 | 440 | 520 | -80 |
| w7 | 520 | 600 | -80 |

The worst overload occurs in **w1 and w2**, where planned demand significantly exceeds available production capacity.

Cross-checking production data shows repeated overruns at critical stations:

**Station 016 (Gjutning)**
- P03: 28 planned → 35 actual (**25% overrun**)
- P05: 35 planned → 40 actual (**14.3% overrun**)

**Station 014 (Svets o montage IQB)**
- P03: 42 planned → 48 actual (**14.3% overrun**)

**Station 011 (FS IQB)**
- Multiple projects show sustained workload pressure due to high throughput demand.

This indicates that Station 016 and Station 014 are key operational bottlenecks contributing to weekly capacity deficits.

---

### 2. Cypher Query

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.10
RETURN
    s.station_name AS station,
    p.project_name AS project,
    r.planned_hours AS planned_hours,
    r.actual_hours AS actual_hours,
    ROUND(((r.actual_hours - r.planned_hours) / r.planned_hours) * 100, 2) AS variance_percent
ORDER BY variance_percent DESC;
```

---

### 3. Bottleneck Graph Modeling

I would model bottlenecks as dedicated nodes:

```text
(Project)-[:CAUSES]->(Bottleneck)
(Bottleneck)-[:AT]->(Station)
(Bottleneck)-[:IN_WEEK]->(Week)
```

Properties:
- variance percentage
- severity
- overtime impact
- detected week

This makes operational risk queryable and reusable for dashboards instead of recalculating thresholds repeatedly.

---

# Q4. Vector + Graph Hybrid

### 1. What Would I Embed?

I would embed:
- project descriptions
- product specifications
- construction context
- delivery urgency
- historical execution summaries

Example:

> "450 meters of IQB beams for a hospital extension in Linköping with tight timeline and multi-station processing"

These embeddings capture semantic similarity beyond structured codes alone.

---

### 2. Hybrid Query

Vector search first:
find semantically similar past projects.

Then graph filtering:

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE p.embedding_similarity > 0.85
AND r.actual_hours <= r.planned_hours * 1.05
RETURN
    p.project_name,
    collect(DISTINCT s.station_name) AS stations_used,
    AVG((r.actual_hours - r.planned_hours) / r.planned_hours) AS avg_variance;
```

---

### 3. Why Better Than Product Filtering?

Filtering only by product type ignores operational complexity. Two IQB projects may involve entirely different station sequences, workforce requirements, or execution risk.

Vector similarity captures semantic resemblance, while graph traversal validates operational compatibility. Together, they provide much more meaningful planning intelligence.

---

# Q5. My Level 6 Plan

## 1. Node Labels and CSV Mapping

| Node Label | CSV Mapping |
|----------|-------------|
| Project | project_id, project_name, project_number |
| Product | product_type |
| Station | station_code, station_name |
| Worker | worker_id, name, role |
| Week | week |
| Etapp | etapp |
| BOP | bop |
| Certification | certifications |
| Capacity | capacity metrics |

---

## 2. Relationship Design

| Relationship | Description |
|-------------|-------------|
| `PRODUCES` | Project produces product |
| `SCHEDULED_AT` | Project processed at station |
| `OCCURS_IN` | Project scheduled in week |
| `PART_OF` | Project linked to etapp |
| `BELONGS_TO` | Project linked to BOP |
| `WORKS_AT` | Worker assigned station |
| `CAN_COVER` | Backup station coverage |
| `HAS_CERTIFICATION` | Worker qualifications |
| `HAS_CAPACITY` | Weekly production capacity |

---

## 3. Streamlit Dashboard Panels

### Project Overview
Shows:
- planned hours
- actual hours
- variance
- products involved

### Station Load Dashboard
Interactive Plotly charts showing:
- workload by station
- overload detection
- planned vs actual comparison

### Capacity Tracker
Displays:
- available capacity
- planned workload
- deficit weeks
- overtime contribution

### Worker Coverage Matrix
Shows:
- primary station assignment
- backup worker availability
- single-point-of-failure risks

### Self-Test Page
Automated validation:
- Neo4j connection
- node count
- relationship count
- labels
- relationship types
- variance query

---

## 4. Cypher Queries

### Project Overview

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN
    p.project_name,
    SUM(r.planned_hours) AS planned,
    SUM(r.actual_hours) AS actual;
```

---

### Station Load

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
MATCH (p)-[:OCCURS_IN]->(w:Week)
RETURN
    s.station_name,
    w.week,
    SUM(r.planned_hours) AS planned,
    SUM(r.actual_hours) AS actual;
```

---

### Capacity Tracker

```cypher
MATCH (w:Week)-[r:HAS_CAPACITY]->(c:Capacity)
RETURN
    w.week,
    r.total_capacity,
    r.total_planned,
    r.deficit;
```

---

### Worker Coverage

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN
    w.name,
    collect(s.station_name) AS coverage;
```