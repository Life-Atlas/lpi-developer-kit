# Level 5 — Graph Thinking

Submitted by: Srishti Gusain

---

# Q1. Model It

## Graph Schema Design

### Node Labels
- Project
- Product
- Station
- Worker
- Week
- Certification
- CapacityAlert
- Client

### Relationship Types
- (:Worker)-[:ASSIGNED_TO]->(:Project)
- (:Worker)-[:CERTIFIED_FOR]->(:Station)
- (:Project)-[:USES]->(:Station)
- (:Project)-[:PRODUCES]->(:Product)
- (:Project)-[:SCHEDULED_IN]->(:Week)
- (:Station)-[:OVERLOADED_IN]->(:Week)
- (:Worker)-[:WORKED_AT {hours: 38, week: "w2"}]->(:Station)
- (:Project)-[:HAS_ALERT]->(:CapacityAlert)

## Why I Designed It This Way

I modeled the factory as a graph because production systems are highly relationship-driven. Projects depend on stations, workers depend on certifications, and bottlenecks affect multiple connected entities simultaneously.

Using a graph makes operational dependencies easier to analyze compared to relational joins.

---

# Q2. Why Not Just SQL?

## SQL Query

```sql
SELECT w.name, p.project_name
FROM workers w
JOIN certifications c ON w.worker_id = c.worker_id
JOIN stations s ON c.station_id = s.station_id
JOIN projects p ON p.station_id = s.station_id
WHERE s.station_name = 'Gjutning'
AND w.name != 'Per Gustafsson';

Cypher Query
MATCH (w:Worker)-[:CERTIFIED_FOR]->(s:Station {name:"Gjutning"})
MATCH (p:Project)-[:USES]->(s)
WHERE w.name <> "Per Gustafsson"
RETURN w.name, p.name;
Explanation

The SQL version hides relationships behind multiple joins, making operational dependencies harder to understand.

The graph query directly represents real-world relationships. It becomes visually and logically easier to trace which workers can replace someone and which projects are affected.

Q3. Spot the Bottleneck
Bottleneck Analysis

Projects with actual production hours exceeding planned hours by more than 10% indicate operational overload.

Stations repeatedly showing overload patterns across multiple weeks represent bottleneck risks.

Cypher Query
MATCH (p:Project)-[r:USES]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.name, p.name,
r.actual_hours,
r.planned_hours,
((r.actual_hours-r.planned_hours)/r.planned_hours)*100 AS variance
ORDER BY variance DESC;
Graph Alert Design

I would model bottlenecks as relationship properties because overload conditions are contextual and time-dependent.

Example:

(:Station)-[:HAS_BOTTLENECK {
week:"w4",
variance:18
}]->(:Project)
Q4. Vector + Graph Hybrid
What I Would Embed

I would embed:

project descriptions
product specifications
worker skill descriptions
station capability summaries

These embeddings would capture semantic similarity between projects and operational requirements.

Hybrid Query Logic
Use vector similarity to find semantically similar projects.
Use graph traversal to verify:
same stations used
same workflows
acceptable production variance
Why Hybrid Is Better

Vector search alone only finds text similarity.

Graph constraints ensure operational similarity as well.

Two hospital projects may sound similar semantically, but the graph ensures they also used similar stations, workflows, and delivery patterns.

This produces more reliable planning recommendations.

Q5. My Level 6 Blueprint
Planned Node Labels
Node	CSV Source
Project	factory_production.csv
Product	factory_production.csv
Station	factory_production.csv
Worker	factory_workers.csv
Week	factory_capacity.csv
CapacityAlert	generated dynamically
Planned Relationships
Relationship	Logic
ASSIGNED_TO	Worker assigned to project
CERTIFIED_FOR	Worker certification
USES	Project uses station
PRODUCES	Project produces product
OVERLOADED_IN	Station overload in week
HAS_ALERT	Generated risk relationship
Planned Streamlit Dashboard Panels
1. Station Utilization Heatmap

Shows overloaded stations across weeks.

2. Worker Coverage Matrix

Shows certification coverage and backup worker availability.

3. Project Variance Tracker

Shows planned vs actual production variance.

4. Capacity Risk Dashboard

Highlights weeks where demand exceeds available capacity.

Planned Cypher Queries
Capacity Overload
MATCH (s:Station)-[:OVERLOADED_IN]->(w:Week)
RETURN s.name, w.name;
Worker Backup Query
MATCH (w:Worker)-[:CERTIFIED_FOR]->(s:Station)
RETURN s.name, collect(w.name);
High Variance Projects
MATCH (p:Project)-[r:USES]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN p.name, s.name;
Final Thoughts

This assignment helped me understand how graph databases represent operational systems more naturally than relational databases.

I also learned how vector search and graph traversal can work together to build intelligent industrial systems.
