# Level 5: Graph Thinking 
**Name:** Ananyaa M

## Q1. Model It (20 pts)
*See `schema.png` in this directory for the visual diagram.*

Schema Breakdown:

* 7 Node Labels: Project, Station, Worker, Certification, Week, Product, BOP
* 9 Relationship Types:
    1. (Project)-[:PROCESSED_AT]->(Station)
    2. (Project)-[:LOGGED_IN_WEEK]->(Week)
    3. (Station)-[:UTILIZED_IN_WEEK]->(Week)
    4. (Worker)-[:PRIMARY_STATION]->(Station)
    5. (Worker)-[:CAN_COVER]->(Station)
    6. (Worker)-[:HAS_CERT]->(Certification)
    7. (Station)-[:REQUIRES_CERT]->(Certification)
    8. (Project)-[:USES_PRODUCT]->(Product)
    9. (Project)-[:BELONGS_TO_BOP]->(BOP)
* Relationships with Data:
    * PROCESSED_AT {planned_hours, actual_hours, completed_units}
    * LOGGED_IN_WEEK {planned_hours, actual_hours}
    * UTILIZED_IN_WEEK {planned_hours, actual_hours}
* Node Properties of Note:
    * Week {total_capacity, total_planned, deficit}

## Q2. Why Not Just SQL? (20 pts)

1.  SQL query: -
SELECT
    w.name AS CertifiedBackup,
    proj.project_name AS AffectedProject,
    proj.week
FROM workers w
JOIN factory_production proj ON proj.station_code = 16
WHERE w.name != 'Per Gustafsson'
AND (w.primary_station = '016' OR w.can_cover_stations LIKE '%016%');

2. Cypher query: -
MATCH (backup:Worker)-[:CAN_COVER]->(s:Station {code: "016"})
WHERE backup.name <> "Per Gustafsson"
MATCH (s)<-[:PROCESSED_AT]-(proj:Project)
RETURN DISTINCT backup.name AS CertifiedBackup, proj.name AS AffectedProject

3. In SQL, figuring out how things connect is a headache because the actual layout of the factory gets buried under a pile of junction tables and foreign keys. Cypher is way more intuitive because you literally just read the query left-to-right like a map: find the workers pointing to this station, then walk backwards to find the affected projects. It is more easier to understand because the graph actually looks like the real-life factory floor, meaning we don't have to rely on string matching just to answer a question.

## Q3. Spot the Bottleneck (20 pts)

1. By analyzing the factory_production.csv against the deficit weeks in factory_capacity.csv, the primary bottlenecks causing the factory overload are Station 16 (Gjutning) and Station 14 (Svets o montage IQB).
Specifically, these projects bled the most excess hours past their planned limits:
    Lagerhall Jönköping: Overran by 7.0 hours at Station 16 (Gjutning).
    Lagerhall Jönköping: Overran by 6.0 hours at Station 14 (Svets o montage IQB).
    Sjukhus Linköping ET2: Overran by 5.0 hours at Station 16 (Gjutning).
    Stålverket Borås: Overran by 3.5 hours at Station 12 (Förmontering IQB).

2. Cypher query: -
MATCH (proj:Project)-[r:PROCESSED_AT]->(s:Station)
WHERE r.actual_hours > (r.planned_hours * 1.10)
RETURN s.name AS Station, 
       collect(DISTINCT proj.name) AS OverrunProjects, 
       sum(r.actual_hours - r.planned_hours) AS ExcessHours
ORDER BY ExcessHours DESC

3. I would model the bottleneck as an Event Node triggered by a backend check. When actual hours exceed planned by 10%, the system should dynamically create a new node: (:BottleneckAlert {severity: "High", excess_hours: 7.0, week: "w3"}). Then I wire this node into the graph: (s:Station {code:"016"})-[:TRIGGERED]->(:BottleneckAlert)<-[:CAUSED_BY]-(proj:Project {name:"Lagerhall Jönköping"}). This allows the Streamlit dashboard to query pre-computed alerts instantly and visually map exactly where the factory floor is failing without recalculating the math on every page load.

## Q4. Vector + Graph Hybrid (20 pts)

1. I would embed the Project Descriptions (the free-text scope, requirements, and client requests) and attach the resulting vector as a property on the Project node (e.g., Project.embedding).

2. Hybrid Query:
// a. Vector Search: Find 5 projects semantically similar to the new prompt
CALL db.index.vector.queryNodes('project_embeddings', 5, $new_project_vector)
YIELD node AS pastProj, score

// b. Graph Traversal: Check how those specific projects actually performed on the floor
MATCH (pastProj)-[r:PROCESSED_AT]->(s:Station)
WITH pastProj, score, collect(DISTINCT s.name) AS stations, sum(r.actual_hours) AS actual, sum(r.planned_hours) AS planned
WHERE (actual - planned) / planned < 0.05 // Variance < 5%

RETURN pastProj.name AS SimilarSuccessfulProject, score AS Similarity, stations AS SharedStations

3. Filtering by product type (like just searching for "IQB beams") only looks at the material output and ignores the context of the work. For example, a "hospital extension" implies strict tolerances, specific certifications, and tight logistics that a standard "warehouse" IQB beam project doesn't have.
Vector search captures the semantic intent and scope of the project description, while the Graph traversal ensures we only recommend past projects that were actually successful on the factory floor (variance < 5%). It marries conceptual matching with ground-truth operational data—which is exactly how a smart agent should match humans to work.

## Q5. Your L6 Plan (20 pts)

1. Node Labels & CSV Mappings:
Project: factory_production.csv (project_id, project_number, project_name)
Station: factory_production.csv (station_code, station_name)
Worker: factory_workers.csv (worker_id, name, role, type)
Certification: factory_workers.csv (parsed from the comma-separated certifications column)
Week: factory_capacity.csv (week string, total_capacity, total_planned, deficit)

2. Relationship Types & Creation Triggers:
[:PRIMARY_STATION] & [:CAN_COVER]: Created from factory_workers.csv, mapping workers to their assigned and backup stations.
[:PROCESSED_AT {planned_hours, actual_hours}]: Created from factory_production.csv, tracking project execution per station.
[:UTILIZED_IN_WEEK {planned_hours, actual_hours}]: Created from factory_production.csv, linking Station loads to specific Weeks.

3. 3 Streamlit Dashboard Panels and their Cypher queries:
a. "Capacity Deficit Tracker" (Factory Load)- A time-series bar chart showing total factory capacity vs. planned demand per week, flagging weeks with a negative deficit in red.
Cypher: MATCH (w:Week) RETURN w.id AS Week, w.total_capacity AS Capacity, w.total_planned AS Demand, w.deficit AS Deficit ORDER BY w.id

b. "Project Variance Radar" (Planned vs Actual Hours)- A radar or grouped bar chart identifying which projects bleed the most hours at which specific stations.
Cypher: MATCH (p:Project)-[r:PROCESSED_AT]->(s:Station) RETURN p.name, s.name, sum(r.planned_hours), sum(r.actual_hours)

c. "Risk: Uncovered Stations" (Worker Coverage Matrix)- A horizontal bar chart or matrix flagging stations that have a low "bus factor" (e.g., only 1 worker knows how to operate it, creating a severe Single Point of Failure).
Cypher: MATCH (s:Station) OPTIONAL MATCH (w:Worker)-[:CAN_COVER]->(s) RETURN s.name, count(w) AS AvailableCoverage ORDER BY AvailableCoverage ASC

