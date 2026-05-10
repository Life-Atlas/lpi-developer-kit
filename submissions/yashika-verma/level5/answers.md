# Level 5 Answers

## Q1. Model It

The schema models factory operations as interconnected production, staffing, and capacity relationships. Projects produce products that flow through stations across weekly schedules, while workers and certifications represent staffing flexibility and operational dependencies.

Graph relationships capture production flow, worker substitution capability, and overload propagation between shared stations. Relationship properties store operational metrics such as planned hours, actual hours, weekly variance, and capacity deficits.

Schema diagram included in schema.md.

---

## Q2. Why Not Just SQL?
### SQL Query

```sql
SELECT 
    w.worker_name,
    s.station_name,
    p.project_name
FROM workers w
JOIN worker_certifications wc 
    ON w.worker_id = wc.worker_id
JOIN certifications c
    ON wc.certification_id = c.certification_id
JOIN stations s
    ON c.station_id = s.station_id
JOIN production pr
    ON s.station_id = pr.station_id
JOIN projects p
    ON pr.project_id = p.project_id
WHERE s.station_code = '016'
AND s.station_name = 'Gjutning'
AND w.worker_name <> 'Per Gustafsson';
```

---

### Cypher Query

```cypher
MATCH (w:Worker)-[:HAS_CERTIFICATION]->(:Certification)-[:VALID_FOR]->(s:Station)
MATCH (p:Project)-[:USES_STATION]->(s)
WHERE s.station_code = "016"
AND s.name = "Gjutning"
AND w.name <> "Per Gustafsson"

RETURN w.name AS replacement_worker,
       s.name AS station,
       collect(p.name) AS affected_projects
```

---

### Explanation

The Cypher query follows the operational relationships directly, making worker substitution and project impact easier to understand visually. In SQL, the same logic requires multiple joins and intermediary tables, which hides the real dependency chain between workers, certifications, stations, and projects. The graph model makes operational reasoning and traversal much more intuitive for production planning scenarios.


## Q3. Spot the Bottleneck

### Bottleneck Analysis

The capacity dataset shows multiple weekly deficits where production demand exceeds available station capacity. By comparing planned_hours and actual_hours in the production dataset, the main bottlenecks appear in stations with repeated overtime and high variance across multiple projects.

Projects that consistently exceed planned hours create cascading overload effects because the same stations are shared across several active projects during the same production weeks.

---

### Cypher Query

```cypher
MATCH (p:Project)-[r:OVERLOADED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.10

RETURN 
    s.name AS station,
    p.name AS project,
    r.planned_hours AS planned_hours,
    r.actual_hours AS actual_hours,
    ROUND(
        ((r.actual_hours - r.planned_hours) / r.planned_hours) * 100,
        2
    ) AS variance_percent

ORDER BY variance_percent DESC
```

---

### Graph Alert Modeling

I would model bottlenecks using both relationship properties and dedicated Alert nodes.

The relationship property stores operational metrics directly on the production relationship:

```text
(:Project)-[:OVERLOADED_AT {
    planned_hours,
    actual_hours,
    variance_percent,
    week
}]->(:Station)
```

This keeps overload calculations close to the operational workflow.

For monitoring and dashboards, I would also create dedicated Alert nodes:

```text
(:Alert {
    type: "capacity_overload",
    severity: "high",
    variance_percent: 24.5
})
```

connected through:

```text
(:Alert)-[:TRIGGERED_FOR]->(:Project)
(:Alert)-[:AT_STATION]->(:Station)
(:Alert)-[:IN_WEEK]->(:Week)
```

This makes it easier to track historical bottlenecks, visualize recurring overload patterns, and build real-time operational dashboards.

## Q4. Vector + Graph Hybrid

### What I Would Embed

I would generate embeddings for:

- Project descriptions
- Product specifications
- Delivery timelines
- Construction/client requirements
- Worker skills and certifications
- Historical project summaries

Example project text:

```text
"450 meters of IQB beams for a hospital extension in Linköping with a tight delivery timeline"
```

Embedding this text allows the system to identify semantically similar projects even when the product names or wording are different.

---

### Hybrid Vector + Graph Query

```cypher
CALL db.index.vector.queryNodes(
    'project_embeddings',
    5,
    $embedding
)
YIELD node, score

MATCH (node:Project)-[:USES_STATION]->(s:Station)
MATCH (node)-[r:OVERLOADED_AT]->(s)

WHERE r.variance_percent < 5

RETURN 
    node.name AS similar_project,
    score,
    collect(DISTINCT s.name) AS stations_used,
    avg(r.variance_percent) AS average_variance

ORDER BY score DESC
```

---

### Why Hybrid Search Is Better

Filtering only by product type would miss operational context and project complexity. Two projects may both involve IQB beams but differ significantly in staffing requirements, station usage, delivery pressure, or execution efficiency.

Vector similarity captures semantic and contextual similarity between projects, while the graph relationships ensure the retrieved projects are operationally relevant based on station usage, production flow, and historical performance.

This hybrid approach is more useful because it combines semantic understanding with real operational constraints.

The same pattern can also be applied to people-matching systems such as Boardy, where embeddings identify similar needs or offers, while graph relationships verify community, collaboration history, or organizational connections.

## Q5. Your L6 Plan

### Graph Nodes and CSV Mapping

| Node Label | CSV Columns |
|---|---|
| Project | project_id, project_name |
| Product | product_type |
| Station | station_code, station_name |
| Worker | worker_name, role |
| Certification | certifications |
| Week | week |
| Capacity | planned_capacity, actual_demand, deficit |
| Alert | derived from overload calculations |

---

### Relationship Types

| Relationship | Created From |
|---|---|
| PRODUCES | project_id → product_type |
| PROCESSED_AT | product_type → station |
| USES_STATION | project_id → station |
| SCHEDULED_IN | project_id → week |
| PRIMARY_OPERATOR_AT | worker → primary_station |
| CAN_COVER | worker → cover_stations |
| HAS_CERTIFICATION | worker → certifications |
| HAS_CAPACITY | station → weekly capacity |
| OVERLOADED_AT | actual_hours > planned_hours |
| TRIGGERED_FOR | alert → project |

---

### Streamlit Dashboard Panels

#### 1. Station Load Heatmap

Purpose:
- Compare planned vs actual hours by station and week
- Identify overloaded production stations visually

Cypher query:

```cypher
MATCH (p:Project)-[r:OVERLOADED_AT]->(s:Station)
RETURN 
    s.name,
    r.week,
    SUM(r.actual_hours) AS actual_hours,
    SUM(r.planned_hours) AS planned_hours
ORDER BY r.week
```

---

#### 2. Worker Coverage Matrix

Purpose:
- Show which workers can substitute for critical stations
- Identify staffing risks and certification gaps

Cypher query:

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN 
    w.name,
    collect(s.name) AS coverage_stations
```

---

#### 3. Bottleneck Alert Dashboard

Purpose:
- Track projects exceeding planned production hours
- Display highest variance stations and recurring overloads

Cypher query:

```cypher
MATCH (p:Project)-[r:OVERLOADED_AT]->(s:Station)
WHERE r.variance_percent > 10

RETURN 
    p.name,
    s.name,
    r.week,
    r.variance_percent

ORDER BY r.variance_percent DESC
```

---

#### 4. Similar Project Search

Purpose:
- Find historically similar projects using vector search
- Compare station usage and execution efficiency

Cypher query:

```cypher
CALL db.index.vector.queryNodes(
    'project_embeddings',
    5,
    $embedding
)
YIELD node, score

RETURN node.name, score
ORDER BY score DESC
```

---

### Implementation Plan

For Level 6, I would:

1. Load the CSV datasets into Neo4j
2. Create graph nodes and relationships using Cypher import scripts
3. Compute overload and variance metrics during ingestion
4. Generate embeddings for project descriptions
5. Build a Streamlit dashboard connected to Neo4j
6. Visualize bottlenecks, staffing coverage, and project similarity
7. Add alert monitoring for recurring station overloads

The graph structure enables operational analysis that would be difficult to model efficiently using relational joins alone, especially when tracking staffing substitutions, shared station dependencies, and cascading production bottlenecks.

---

## Conclusion

This graph-based approach models the factory as an interconnected operational system rather than isolated relational tables. Combining graph traversal with vector similarity enables more intelligent production planning, staffing analysis, bottleneck detection, and historical project comparison.