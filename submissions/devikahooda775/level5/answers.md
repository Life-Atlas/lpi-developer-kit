# Level 5 Answers — Graph Thinking

## Q1. Model It

I designed a graph schema connecting projects, products, stations, workers, certifications, weeks, and capacity data.

Main node labels:
- Project
- Product
- Station
- Worker
- Week
- Capacity
- Certification
- Bottleneck

Main relationship types:
- HAS_PRODUCT
- SCHEDULED_IN
- USES_STATION
- PROCESSED_AT
- PRIMARY_AT
- CAN_COVER
- HAS_CERTIFICATION
- HAS_CAPACITY
- HAS_BOTTLENECK
- AFFECTED_BY
- REQUIRES_CERTIFICATION

Relationships carrying data:
- `USES_STATION {planned_hours, actual_hours, completed_units}`
- `HAS_CAPACITY {total_capacity, total_planned, deficit}`

The graph structure allows production planning, worker coverage analysis, bottleneck detection, and future dashboard visualizations.

---

## Q2. Why Not Just SQL?

### SQL Query

```sql
SELECT w.name, w.worker_id, w.can_cover_stations, p.project_name
FROM workers w
JOIN production p
ON p.station_code = '016'
WHERE w.can_cover_stations LIKE '%016%'
AND w.name != 'Per Hansen';
```

### Cypher Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {station_code: "016"})
MATCH (p:Project)-[u:USES_STATION]->(s)
WHERE w.name <> "Per Hansen"
RETURN w.name, w.worker_id, p.project_name, u.actual_hours;
```

### Graph vs SQL

The graph version makes worker-to-station-to-project relationships immediately visible and easier to traverse. In SQL, multiple joins are required and relationships are less intuitive. The graph approach naturally models operational dependencies and worker substitution scenarios.

---

## Q3. Spot the Bottleneck

Weeks w1, w2, w4, w6, and w7 show capacity deficits in `factory_capacity.csv`.

Major overload examples:
- Project P03 at Station 016 (Gjutning): planned 28h, actual 35h
- Project P05 at Station 016 (Gjutning): planned 35h, actual 40h
- Project P08 at Station 016 (Gjutning): planned 22h, actual 25h
- Project P04 at Station 021: planned 60h, actual 65h

### Cypher Query

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
WHERE u.actual_hours > u.planned_hours * 1.10
RETURN s.station_name,
       p.project_name,
       u.planned_hours,
       u.actual_hours,
       ((u.actual_hours - u.planned_hours) / u.planned_hours) * 100 AS variance_pct
ORDER BY variance_pct DESC;
```

### Bottleneck Modeling

I would model bottlenecks using a `(:Bottleneck)` node connected to overloaded stations and affected projects.

Example:

```cypher
(:Station)-[:CAUSES]->(:Bottleneck)<-[:AFFECTED_BY]-(:Project)
```

This makes it easy to track recurring overloads, impacted stations, and affected projects over time.

---

## Q4. Vector + Graph Hybrid

### What I Would Embed

I would embed:
- project descriptions
- product specifications
- station usage patterns
- project timelines
- worker certifications and skills

### Hybrid Query

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
WHERE p.embedding SIMILAR TO $query_embedding
AND abs(u.actual_hours - u.planned_hours) / u.planned_hours < 0.05
RETURN p.project_name,
       s.station_name,
       u.actual_hours,
       u.planned_hours;
```

### Why This Is Better

Vector search finds semantically similar projects even when names or product types differ. Combining graph relationships with vector similarity enables smarter matching based on operational behavior, station usage, timelines, and production efficiency instead of relying only on simple product filtering.

---

## Q5. Your L6 Plan

### Node Labels

| Node Label | CSV Columns |
|------------|-------------|
| Project | project_id, project_name, project_number |
| Product | product_type, quantity, unit |
| Station | station_code, station_name |
| Worker | worker_id, name, role |
| Week | week |
| Capacity | total_capacity, total_planned, deficit |
| Certification | certifications |

### Relationship Types

| Relationship | Created From |
|--------------|-------------|
| HAS_PRODUCT | project_id → product_type |
| USES_STATION | project_id → station_code |
| CAN_COVER | worker → can_cover_stations |
| PRIMARY_AT | worker → primary_station |
| HAS_CERTIFICATION | worker → certifications |
| HAS_CAPACITY | week → capacity |
| HAS_BOTTLENECK | week → deficit |
| AFFECTED_BY | project → bottleneck |

### Streamlit Dashboard Panels

1. Station Load Heatmap
   - Displays station overload by week

2. Worker Coverage Matrix
   - Shows which workers can cover which stations

3. Project Timeline Dashboard
   - Tracks planned vs actual production hours

4. Bottleneck Alert Panel
   - Displays overloaded stations and affected projects

### Cypher Queries Powering Panels

#### Station Load Heatmap

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
RETURN s.station_name, u.week, sum(u.actual_hours);
```

#### Worker Coverage Matrix

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN w.name, s.station_name;
```

#### Bottleneck Alerts

```cypher
MATCH (s:Station)-[:CAUSES]->(b:Bottleneck)
RETURN s.station_name, b.level;
```

#### Project Timeline

```cypher
MATCH (p:Project)-[u:USES_STATION]->(s:Station)
RETURN p.project_name, u.week, u.planned_hours, u.actual_hours;
```