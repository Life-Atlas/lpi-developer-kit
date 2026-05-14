Q1 — Graph Schema

You need:

6+ node labels
8+ relationship types
properties on relationships

Use this schema directly.

Node Labels
Node	Source
Project	production.csv
Product	production.csv
Station	production.csv
Worker	workers.csv
Week	capacity.csv
Etapp	production.csv
Capacity	capacity.csv
Relationship Types
Relationship	Example
PRODUCES	Project → Product
SCHEDULED_AT	Project → Station
RUNS_IN	Project → Week
PART_OF	Project → Etapp
WORKS_AT	Worker → Station
CAN_COVER	Worker → Station
HAS_CAPACITY	Week → Capacity
OVERLOADED_AT	Project → Station

That already gives 8 relationships.

Q2 — SQL vs Cypher

You need:

SQL query
Cypher query
explanation

Use this structure.

SQL
SELECT w.name, s.station_name, p.project_name
FROM workers w
JOIN worker_coverage wc ON w.worker_id = wc.worker_id
JOIN stations s ON wc.station_id = s.station_id
JOIN project_station ps ON s.station_id = ps.station_id
JOIN projects p ON ps.project_id = p.project_id
WHERE s.station_code = '016'
AND w.name != 'Per Gustafsson';
Cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {code:'016'})
MATCH (p:Project)-[:SCHEDULED_AT]->(s)
WHERE w.name <> 'Per Gustafsson'
RETURN w.name, s.name, p.name;
Explanation

Write:

The graph query directly shows how workers, stations, and projects connect. In SQL, multiple joins hide the relationships and make traversal harder to understand. Cypher naturally represents the real-world factory structure.

Q3 — Bottleneck Analysis

You need:

identify overload stations
Cypher query
graph alert model
Cypher Query
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.name AS station,
       p.name AS project,
       r.planned_hours,
       r.actual_hours,
       ((r.actual_hours-r.planned_hours)/r.planned_hours)*100 AS variance
ORDER BY variance DESC;
Bottleneck Modeling

Write:

I would model bottlenecks using a (:Bottleneck) node connected to overloaded stations and projects. This allows historical tracking of overload patterns and easier querying for recurring production issues.

Q4 — Vector + Graph Hybrid
What to Embed

Write:

project descriptions
product specifications
worker skills
timelines
Hybrid Query
MATCH (p:Project)-[:SCHEDULED_AT]->(s:Station)
WHERE p.variance < 5
AND s.name IN ['Cutting','Welding']
RETURN p.name, s.name;
Then explain vector search separately:

First, embeddings find semantically similar projects using free-text descriptions. Then graph filtering ensures the matched projects used similar stations and maintained low variance.

Q5 — L6 Blueprint

This is extremely important.

Use:

Node Labels
Project
Product
Station
Worker
Week
Etapp
Capacity
Dashboard Pages

Use exactly these:

1.Project Overview
2.Station Load
3.Capacity Tracker
4.Worker Coverage
5.Self-Test
