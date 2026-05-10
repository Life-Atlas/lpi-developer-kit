# Level 5 — Graph Thinking Answers

## Q1. Model It

The complete graph schema is provided in `schema.md`.

### Main Node Labels
- Project
- Product
- Station
- Worker
- Week
- Certification
- Role
- CapacityWeek

### Main Relationship Types
- PRODUCES
- USES_STATION
- RUNS_IN
- PROCESSED_AT
- PRIMARY_AT
- CAN_COVER
- HAS_ROLE
- CERTIFIED_IN
- HAS_CAPACITY

### Relationships with Properties

#### `(:Project)-[:PROCESSED_AT]->(:Station)`
Properties:
- planned_hours
- actual_hours
- completed_units
- week

#### `(:Worker)-[:CAN_COVER]->(:Station)`
Properties:
- coverage_priority
- skill_level

#### `(:Station)-[:HAS_CAPACITY]->(:CapacityWeek)`
Properties:
- total_capacity
- total_planned
- deficit

This schema captures:
- project production flow
- worker coverage capability
- station bottlenecks
- weekly production variance
- capacity overload conditions

---

# Q2. Why Not Just SQL?

## 1. SQL Query

```sql
SELECT
    w.worker_name,
    s.station_name,
    p.project_name
FROM workers w
JOIN worker_station_cover wsc
    ON w.worker_id = wsc.worker_id
JOIN stations s
    ON wsc.station_id = s.station_id
JOIN production pr
    ON s.station_id = pr.station_id
JOIN projects p
    ON pr.project_id = p.project_id
WHERE s.station_code = '016'
AND w.worker_name != 'Per Gustafsson';
```

---

## 2. Cypher Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {station_code:"016"})
MATCH (p:Project)-[:PROCESSED_AT]->(s)
WHERE w.worker_name <> "Per Gustafsson"
RETURN
    w.worker_name,
    s.station_name,
    p.project_name;
```

---

## 3. Graph Insight

The Cypher query directly follows operational relationships between workers, stations, and projects. The graph structure makes worker replacement impact and project dependencies visually obvious.

In SQL, the same logic is hidden behind multiple JOIN tables and intermediate mappings, making operational relationships harder to understand and maintain.

---

# Q3. Spot the Bottleneck

## 1. Bottleneck Analysis

Using `factory_capacity.csv`, several weeks show capacity deficits where planned production demand exceeds available station capacity.

From `factory_production.csv`, overloads are mainly caused by projects where:

```text
actual_hours > planned_hours
```

Example overload conditions:
- Station 016 (Gjutning) exceeded planned capacity during multiple production weeks
- Several projects showed production variance above 10%
- High-utilization stations such as FS IQB, Gjutning, and Svetsning contributed most to overload conditions

Projects with large production variance contribute directly to weekly capacity deficits.

---

## 2. Cypher Query

```cypher
MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.10

RETURN
    s.station_name AS station,
    p.project_name AS project,
    r.planned_hours AS planned,
    r.actual_hours AS actual,

    ROUND(
        ((r.actual_hours - r.planned_hours)
        / r.planned_hours) * 100,
        2
    ) AS variance_percent

ORDER BY variance_percent DESC;
```

---

## 3. Bottleneck Graph Modeling

I would model bottlenecks using a dedicated `(:Bottleneck)` node.

Example:

```text
(:Project)-[:CAUSES]->(:Bottleneck)-[:AT_STATION]->(:Station)
```

### Bottleneck Properties
- variance_percent
- week
- overload_hours
- severity

This approach allows:
- historical tracking
- severity analysis
- recurring overload detection
- alert aggregation across stations and weeks

It also keeps operational alerts separate from core production relationships.

---

# Q4. Vector + Graph Hybrid

## 1. What Would Be Embedded?

I would embed:
- project descriptions
- customer requirements
- product specifications
- delivery constraints
- timeline descriptions

Example:

> "450 meters of IQB beams for a hospital extension in Linköping"

These embeddings capture semantic similarity between projects beyond simple product categories.

---

## 2. Hybrid Vector + Graph Query

```cypher
CALL db.index.vector.queryNodes(
    'project_embeddings',
    5,
    $embedding
)

YIELD node AS similarProject, score

MATCH (similarProject)-[r:PROCESSED_AT]->(s:Station)

WHERE
    ABS(r.actual_hours - r.planned_hours)
    / r.planned_hours < 0.05

RETURN
    similarProject.project_name,
    s.station_name,
    score,
    r.actual_hours,
    r.planned_hours

ORDER BY score DESC;
```

---

## 3. Why Hybrid Is Better

Two projects may use different product names but still follow very similar production workflows, station usage patterns, and scheduling constraints.

Vector search captures semantic similarity between projects, while the graph ensures operational compatibility through shared stations and low production variance.

This produces much more useful recommendations than filtering only by product type.

This same hybrid pattern can later be extended to worker recommendation systems and production planning optimization.

---

# Q5. My Level 6 Blueprint

## 1. Node Labels + CSV Mapping

### Project
From:
- project_id
- project_number
- project_name

---

### Product
From:
- product_type
- quantity
- unit

---

### Station
From:
- station_code
- station_name

---

### Worker
From:
- worker_id
- worker_name
- worker_type
- hours_per_week

---

### Week
From:
- week

---

### Certification
From:
- certifications

---

### Role
From:
- role

---

### CapacityWeek
From:
- week
- total_capacity
- total_planned
- deficit

---

# 2. Relationship Types

```text
(:Project)-[:PRODUCES]->(:Product)

(:Project)-[:USES_STATION]->(:Station)

(:Project)-[:PROCESSED_AT {
    planned_hours,
    actual_hours,
    completed_units,
    week
}]->(:Station)

(:Project)-[:RUNS_IN]->(:Week)

(:Worker)-[:PRIMARY_AT]->(:Station)

(:Worker)-[:CAN_COVER {
    coverage_priority,
    skill_level
}]->(:Station)

(:Worker)-[:HAS_ROLE]->(:Role)

(:Worker)-[:CERTIFIED_IN]->(:Certification)

(:Station)-[:HAS_CAPACITY {
    total_capacity,
    total_planned,
    deficit
}]->(:CapacityWeek)
```

---

# 3. Streamlit Dashboard Panels

## 1. Station Load Heatmap

Shows:
- station overload
- weekly utilization
- production variance %

### Cypher Query

```cypher
MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)

RETURN
    s.station_name,
    r.week,
    SUM(r.actual_hours) AS actual_hours,
    SUM(r.planned_hours) AS planned_hours;
```

---

## 2. Worker Coverage Matrix

Shows:
- which workers can cover which stations
- backup coverage gaps

### Cypher Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)

RETURN
    w.worker_name,
    s.station_name;
```

---

## 3. Project Variance Dashboard

Shows projects exceeding planned production hours.

### Cypher Query

```cypher
MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)

WHERE r.actual_hours > r.planned_hours

RETURN
    p.project_name,
    s.station_name,
    r.actual_hours,
    r.planned_hours;
```

---

## 4. Capacity Deficit Panel

Shows:
- weekly station deficits
- overloaded capacity periods

### Cypher Query

```cypher
MATCH (s:Station)-[:HAS_CAPACITY]->(c:CapacityWeek)

RETURN
    s.station_name,
    c.week,
    c.total_capacity,
    c.total_planned,
    c.deficit;
```

---

# Final Thoughts

This graph model captures the operational structure of the factory:

- projects are processed through stations
- workers operate and cover stations
- bottlenecks emerge through production variance
- capacity overload can be analyzed across time

The combination of:
- graph relationships
- production metrics
- vector similarity

creates a strong foundation for:
- Level 6 implementation
- operational dashboards
- bottleneck analytics
- industrial AI applications
- hybrid graph + vector workflows
