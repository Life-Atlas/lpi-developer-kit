# Level 5
**ANUPAUL Saikia | Submission**

---

## Q1. Model It (20 pts)

Schema image -> [`schema.png`](schema.png)

**Node Labels:**
`project`
`product`
`units`
`station`
`worker`
`week`
`certification`

**Relationship Types**
`project` → `has` → `product`

`project` → `assigned to` → `station`
`station` → `operated by` → `worker`

`worker` → `has` →  `certification`

`project` → `planned in` → `week`

`worker` → `assigned to` → `week`

`project` → `completed` → `units`

`project` → `logs` → `hours`

**Why this design?**

This schema provides flexibility through reusable nodes, enables performance tracking of hours and units for querying overloads and deficits, and ensures transparency by making bottlenecks and dependencies visible.


## Q2. Why Not Just SQL? (20 pts)

**SQL Query**

```sql 

SELECT w.name, w.certifications, p.project_name
FROM Workers w

JOIN WorkerStationCoverage wc ON w.worker_id = wc.worker_id

JOIN Stations s ON wc.station_id = s.station_id

JOIN ProjectStations ps ON s.station_id = ps.station_id

JOIN Projects p ON ps.project_id = p.project_id

WHERE s.station_code = '016'
  AND w.name <> 'Per Gustafsson';
```
---

**Cypher Query**

```cypher


MATCH (w:Worker)-[:WORKER_CAN_COVER_STATION]->(s:Station {station_code:'016'})

MATCH (s)-[:STATION_BELONGS_TO_PROJECT]->(p:Project)

WHERE w.name <> 'Per Gustafsson'

RETURN w.name AS worker, w.certifications AS certifications, p.project_name AS project;
```
**SQL vs Graph**

SQL hides this connectivity behind multiple joins, while Cypher shows the path of relationships directly, making it clearer which projects are impacted when a worker is unavailable. The graph version makes it immediately obvious that workers, stations, and projects are part of a network of relationships 


## Q3. Spot the Bottleneck (20 pts)


**Overloads and Deficits**

`Week w1` → `Deficit -132`
`Week w2` → `Deficit -125`
`Week w4` → `Deficit -50`
`Week w6` → `Deficit -80`
`Week w7` → `Deficit -80`

**Cypher Query**

```cypher

MATCH (p:Project)-[r:PROJECT_ASSIGNED_TO_STATION]->(s:Station)
MATCH (p)-[wRel:PROJECT_PLANNED_IN_WEEK]->(w:Week)
WHERE wRel.deficit < 0
  AND r.actual_hours > r.planned_hours * 1.1
RETURN w.week AS week,
       p.project_name AS project,
       s.station_name AS station,
       r.planned_hours AS planned,
       r.actual_hours AS actual,
       (r.actual_hours - r.planned_hours) AS overload
ORDER BY week, overload DESC;
```

**alert model** 

Create a Bottleneck node whenever a deficit or overload is detected.

Properties: week, planned_hours, actual_hours, overload_percent, deficit.

Relationships:

(:Project)-[:HAS_BOTTLENECK]->(:Bottleneck)

(:Station)-[:BOTTLENECK_AT]->(:Bottleneck)

This makes bottlenecks first-class citizens in the graph, easy to query and visualize.


## Q4. Vector + Graph Hybrid (20 pts)

**Embeddings**

Project descriptions → free-text scope, domain (hospital extension, bridge, factory).

Product specifications → type, units, quantities (IQB beams, 450 meters).

Station usage → which stations were involved in execution.

Worker skills → certifications and coverage ability.

**Cypher Query for Vector and Graph Hybrid**

``` cypher

CALL db.index.vector.queryNodes('project_embeddings', 5, $queryEmbedding)
YIELD node AS p, similarity
```

```cypher

MATCH (p)-[:PROJECT_ASSIGNED_TO_STATION]->(s:Station)
WHERE abs(s.actual_hours - s.planned_hours) / s.planned_hours < 0.05
RETURN p.project_name AS project,
       collect(s.station_name) AS stations,
       similarity
ORDER BY similarity DESC;
```

**Why is this more useful than just filtering by product type?**


Filtering by product type alone (e.g., “IQB beams”) ignores context: hospitals vs bridges, timelines, and station load patterns. 

The hybrid approach surfaces projects that are truly comparable in scope and execution, not just in product label.

 It highlights operational risks (stations overloaded) and opportunities (workers with matching certifications) that a flat filter would miss.


## Q5. Your L6 Plan (20 pts)

**Node Labels**

`Project` → `project_id`, `project_number`, `project_name`

`Product` → `product_type`, `unit`, `quantity`, `unit_factor`

`Station` → `station_code`, `station_name`

`Worker` → `worker_id`, `name`, `role`, `primary_station`

`Week` → `week`

`Certification` → `certifications`

**Relationship Types**

`project` → `has` → `product`

`project` → `assigned to` → `station`

`station` → `operated by` → `worker`

`worker` → `has` →  `certification`

`project` → `planned in` → `week`

`worker` → `assigned to` → `week`

`project` → `completed` → `units`

`project` → `logs` → `hours`


**Streamlit Dashboard Panels**

1. Project Timeline Heatmap
Shows planned vs actual hours across weeks.

Cypher Query:

```cypher
MATCH (p:Project)-[r:PROJECT_PLANNED_IN_WEEK]->(w:Week)
RETURN p.project_name, w.week, r.total_planned, r.total_capacity, r.deficit
```

2. Station Load Bar Chart
Compares planned vs actual hours per station.

Cypher Query:

```cypher
MATCH (p:Project)-[r:PROJECT_ASSIGNED_TO_STATION]->(s:Station)
RETURN s.station_name, sum(r.planned_hours) AS planned, sum(r.actual_hours) AS actual
```

3. Worker Coverage Matrix
Displays which workers can cover which stations, with certifications.

Cypher Query:

```cypher
MATCH (w:Worker)-[:WORKER_CAN_COVER_STATION]->(s:Station),
      (w)-[:WORKER_HAS_CERTIFICATION]->(c:Certification)
RETURN w.name, s.station_name, collect(c.name) AS certifications
```

4. Bottleneck Alerts Panel
Flags stations/projects where actual > planned by >10%.

Cypher Query:

```cypher
MATCH (p:Project)-[r:PROJECT_ASSIGNED_TO_STATION]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN p.project_name, s.station_name, r.planned_hours, r.actual_hours
```
