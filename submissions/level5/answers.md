Q1. Graph Schema Design

To model the factory production system, I designed a graph schema that captures relationships between projects, products, stations, workers, and weekly capacity.

Node Labels
Project → represents construction projects
Product → items being manufactured
Station → production units (e.g., 011–019)
Worker → employees (operators, inspectors, etc.)
Week → time unit (w1–w8)
Capacity → weekly capacity and demand
Certification → worker skills and qualifications
Relationship Types
(Project)-[:HAS_PRODUCT]->(Product)
(Project)-[:USES_STATION]->(Station)
(Project)-[:SCHEDULED_IN]->(Week)
(Project)-[:PROCESSED_AT]->(Station)
(Worker)-[:WORKS_AT]->(Station)
(Worker)-[:CAN_COVER]->(Station)
(Worker)-[:HAS_CERTIFICATION]->(Certification)
(Worker)-[:WORKED_ON]->(Project)
(Week)-[:HAS_CAPACITY]->(Capacity)
Relationships with Properties

These relationships carry important production data:
(Project)-[:PROCESSED_AT {planned_hours, actual_hours, week}]->(Station)
(Worker)-[:WORKED_ON {hours, week}]->(Project)

These properties allow tracking of performance, workload, and deviations.

Q2. Why Not Just SQL?

SQL Query
SELECT w.name, p.project_name
FROM workers w
JOIN stations s ON w.can_cover_stations LIKE '%016%'
JOIN projects p ON p.station_id = s.id
WHERE s.id = '016'
AND w.name != 'Per Hansen';

Cypher Query
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {id:"016"})
WHERE w.name <> "Per Hansen"
MATCH (p:Project)-[:USES_STATION]->(s)
RETURN w.name, p.name

Explanation
The graph query directly follows relationships between workers, stations, and projects, making dependencies easy to understand.
In SQL, multiple joins and string matching hide these relationships, making queries harder to interpret.
Graph databases naturally represent connections, making impact analysis (like absence of a worker) much clearer.

Q3. Spot the Bottleneck
From the capacity data:
Overloaded weeks: w1, w2, w4, w6, w7
Most critical: w1 (-132), w2 (-125)

This indicates demand exceeding available capacity, especially when:

Overtime is insufficient
Staff count drops (e.g., week w6)
Certain stations are overused
Cypher Query
MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)
WHERE r.actual_hours > 1.1 * r.planned_hours
RETURN s.id AS station,
       p.name AS project,
       r.actual_hours,
       r.planned_hours,
       (r.actual_hours - r.planned_hours) AS overload
ORDER BY overload DESC
Graph Modeling of Bottleneck

I would model bottlenecks as a separate node:

(:Bottleneck {week: "w1", severity: "high"})

Relationships:

(Project)-[:HAS_BOTTLENECK]->(Bottleneck)
(Station)-[:CAUSES]->(Bottleneck)
(Bottleneck)-[:OCCURS_IN]->(Week)
Reasoning

This structure allows tracking recurring overload patterns, linking root causes (stations), and triggering alerts.

Q4. Vector + Graph Hybrid
What to Embed

I would embed:
Project descriptions (main priority)
Product specifications
Execution summaries (performance history)
Hybrid Query
CALL db.index.vector.query("projects", $embedding)
YIELD node AS similarProject

MATCH (similarProject)-[:USES_STATION]->(s:Station)
MATCH (similarProject)-[r:PROCESSED_AT]->(s)
WHERE r.actual_hours <= 1.05 * r.planned_hours

RETURN similarProject
Why This Approach is Better

This combines semantic similarity (vector embeddings) with operational performance (graph structure).
Instead of just matching product types, it finds projects that are both similar in context and proven efficient.
This leads to more reliable and intelligent recommendations.

Q5. Level 6 Implementation Plan

Node Mapping
Node	                                Source CSV
Worker                              	factory_workers.csv
Project                             	factory_production.csv
Product                             	factory_production.csv
Station	                              factory_production.csv
Week	                                factory_capacity.csv
Capacity	                            factory_capacity.csv
Certification                       	factory_workers.csv

Relationship Mapping
Relationship	                         Source
WORKS_AT	                             primary_station
CAN_COVER                            	 can_cover_stations
HAS_CERTIFICATION	                     certifications
USES_STATION                           production data
PROCESSED_AT	                         production data
WORKED_ON	                             production data
HAS_CAPACITY	                         capacity data


Streamlit Dashboard Panels
1. Station Load Dashboard
Shows workload per station
MATCH (s:Station)<-[r:PROCESSED_AT]-(p:Project)
RETURN s.id, SUM(r.actual_hours) AS load

2. Bottleneck Alert Panel
Highlights overloaded projects
MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station)
WHERE r.actual_hours > 1.1 * r.planned_hours
RETURN p.name, s.id

3. Worker Coverage Matrix
Shows which workers can cover which stations
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN w.name, COLLECT(s.id)

5. Weekly Capacity vs Demand
Tracks system load over time
MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
RETURN w.id, c.total_capacity, c.total_planned, c.deficit
Final Plan

In Level 6, I will:
Load CSV data into Neo4j
Create nodes and relationships using Cypher
Build Streamlit dashboards connected to Neo4j
Add visual insights for bottlenecks and workforce planning
