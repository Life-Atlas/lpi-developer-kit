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

The SQL query technically retrieves the required information, but the operational dependency chain is difficult to reason about because the relationships are fragmented across multiple tables and JOIN conditions.

In the graph model, the dependency becomes visually and logically direct:

```cypher
(:Worker)-[:CERTIFIED_FOR]->(:Station)<-[:USES_STATION]-(:Project)
```

This makes it immediately obvious which workers can substitute for Per Gustafsson and which active projects depend on that station.

In a real factory environment, this matters because Station 016 (Gjutning) may become a single point of failure if only one worker is certified for it. The graph structure exposes operational risk, staffing gaps, and downstream project impact much more naturally than relational tables.

## Q3. Spot the Bottleneck

Using `factory_capacity.csv`, several weeks showed clear production overloads where planned demand exceeded available factory capacity.

### Capacity Deficit Analysis

| Week | Capacity | Planned Demand | Deficit |
|------|----------|----------------|----------|
| w1 | 480 | 612 | -132 |
| w2 | 520 | 645 | -125 |
| w4 | 500 | 550 | -50 |
| w6 | 440 | 520 | -80 |
| w7 | 520 | 600 | -80 |

The largest overload occurred during **Week 1**, where demand exceeded available capacity by **132 hours**.

### Projects and Stations Contributing to Overload

Using `factory_production.csv`, the following projects and stations showed the highest variance between planned and actual production hours:

| Project | Station | Planned Hours | Actual Hours | Variance |
|---|---|---|---|---|
| Sjukhus Linköping ET2 | FS IQB | 120 | 145 | +20.8% |
| Bro E6 Halmstad | Svets o montage IQB | 88 | 101 | +14.7% |
| Lagerhall Jönköping | Förmontering IQB | 95 | 110 | +15.8% |
| Parking Helsingborg | Montering IQP | 76 | 88 | +15.7% |

The repeated overloads at:
- FS IQB
- Förmontering IQB
- Svets o montage IQB

indicate these stations are critical production bottlenecks within the factory workflow.

### Cypher Query

```cypher
MATCH (p:Project)-[r:USES_STATION]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.10
RETURN 
    p.name AS project,
    s.name AS station,
    r.planned_hours AS planned_hours,
    r.actual_hours AS actual_hours,
    ROUND(
        ((r.actual_hours - r.planned_hours) / r.planned_hours) * 100,
        2
    ) AS variance_percent
ORDER BY variance_percent DESC
```

### Bottleneck Graph Modeling

I modeled production overloads using a dedicated `(:Bottleneck)` node connected to:
- affected projects
- overloaded stations
- impacted production weeks

Example graph structure:

```cypher
(:Project)-[:HAS_BOTTLENECK]->(:Bottleneck)-[:AT_STATION]->(:Station)
```

The bottleneck node stores:
- overload percentage
- affected hours
- severity level
- week identifier

This makes recurring operational problems easy to trace and visualize across the factory graph.

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

Two projects may both involve steel beams, but still differ significantly in:
- station utilization
- production complexity
- timeline pressure
- welding intensity
- workforce requirements
- historical variance patterns

A pure product-type filter would miss these operational similarities.

Vector embeddings capture semantic context from project descriptions such as:
- “hospital extension”
- “tight deadline”
- “large structural beams”
- “high precision assembly”

The graph layer then adds operational constraints:
- which stations were used
- which projects experienced overload
- which production paths performed efficiently

This hybrid approach is much more useful because it combines semantic similarity with real operational history instead of relying only on category matching.

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

This dashboard helps production planners identify which stations are approaching overload conditions across multiple weeks.

Instead of manually checking spreadsheets, managers can immediately detect:
- overloaded stations
- underutilized stations
- recurring production pressure zones

This is especially useful for balancing production schedules before bottlenecks propagate downstream.

---

### 2. Worker Coverage Matrix

This panel visualizes worker certifications and replacement coverage for each station.

It helps identify:
- single points of failure
- understaffed stations
- workers with rare certifications
- possible backup assignments

For example, if a worker responsible for Gjutning becomes unavailable, managers can immediately see which certified workers can replace them.

---

### 3. Project Variance Dashboard

This dashboard compares planned production hours against actual execution hours grouped by project and station.

It helps management identify:
- projects consistently exceeding estimates
- inefficient production stages
- inaccurate planning assumptions
- stations causing delivery delays

The variance view also provides early warning signals before capacity deficits become critical.

---

### 4. Bottleneck Alert Dashboard

This panel highlights stations and projects exceeding predefined overload thresholds.

Instead of discovering delays after production issues occur, planners can proactively detect:
- overload accumulation
- recurring bottleneck patterns
- capacity risks
- operational instability

The graph structure also allows tracing how a bottleneck at one station impacts dependent projects downstream.

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