# Level 5 - Graph Thinking

## Q1. Model It

I designed a graph schema connecting projects, products, workers, stations, weeks, and capacity planning.

### Node Labels
- Project
- ProductionEntry
- Station
- Product
- Week
- Worker
- Certification
- CapacitySnapshot

### Relationship Types
- HAS_ENTRY
- AT_STATION
- FOR_PRODUCT
- IN_WEEK
- HAS_CAPACITY
- PRIMARY_AT
- CAN_COVER
- HAS_CERT
- REQUIRES_CERT
- USES_PRODUCT

The ProductionEntry node acts as the central operational event connecting projects, stations, products, and weekly production metrics.

---

## Q2. Why Not Just SQL?

### SQL Query

```sql
SELECT w.name, p.project_name
FROM workers w
JOIN production p ON w.station_id = p.station_id
WHERE p.station_id = '016';
```

### Cypher Query

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {station_code:'016'})
MATCH (p:Project)-[:HAS_ENTRY]->(:ProductionEntry)-[:AT_STATION]->(s)
RETURN w.name, p.project_name
```

The graph query makes relationships between workers, stations, and projects easier to understand because the traversal path is explicit.

---

## Q3. Spot the Bottleneck

Station 016 becomes a bottleneck because multiple projects depend on it while staffing coverage is limited.

### Cypher Query

```cypher
MATCH (p:Project)-[:HAS_ENTRY]->(pe:ProductionEntry)-[:AT_STATION]->(s:Station)
WHERE pe.actual_hours > pe.planned_hours * 1.1
RETURN s.station_name,
collect(p.project_name)
```

I would model bottlenecks using a dedicated Bottleneck node connected to overloaded stations and weeks.

---

## Q4. Vector + Graph Hybrid

I would embed project descriptions, product requirements, and workflow sequences.

### Hybrid Query

```cypher
MATCH (p1:Project)-[:HAS_ENTRY]->(:ProductionEntry)-[:AT_STATION]->(s:Station)
MATCH (p2:Project)-[:HAS_ENTRY]->(:ProductionEntry)-[:AT_STATION]->(s)
RETURN p1, p2
```

This combines semantic similarity with operational similarity.

---

## Q5. My L6 Blueprint

### Node Mapping
- Project → project_id
- Station → station_code
- Worker → worker_id
- Product → product_type
- Week → week

### Dashboard Panels
1. Project Overview Dashboard
2. Station Load Heatmap
3. Capacity Tracker
4. Worker Coverage Matrix

### Example Query

```cypher
MATCH (s:Station)<-[:AT_STATION]-(pe:ProductionEntry)
RETURN s.station_name,
sum(pe.actual_hours)
```