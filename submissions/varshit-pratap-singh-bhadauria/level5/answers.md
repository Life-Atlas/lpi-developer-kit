# Level 5: Graph Thinking Answers

## Q1. Model It (20 pts)
Here is the graph schema capturing the relationships between the factory entities based on the production, capacity, and worker data.

**6 Node Labels:**
1. Project
2. Product
3. Station
4. Worker
5. Week
6. Etapp

**8 Relationship Types:**
1. (Project)-[:PRODUCES {quantity, unit_factor}]->(Product)
2. (Project)-[:SCHEDULED_AT {planned_hours, actual_hours}]->(Station)
3. (Week)-[:HAS_CAPACITY {total_capacity, total_planned, deficit}]->(Station)
4. (Project)-[:BELONGS_TO]->(Etapp)
5. (Project)-[:ACTIVE_IN]->(Week)
6. (Worker)-[:PRIMARY_STATION]->(Station)
7. (Worker)-[:CAN_COVER]->(Station)
8. (Product)-[:REQUIRES]->(Station)

### Visual Diagram:
```mermaid
graph TD
    Project((Project))
    Product((Product))
    Station((Station))
    Worker((Worker))
    Week((Week))
    Etapp((Etapp))

    Project -- "PRODUCES {quantity, unit_factor}" --> Product
    Project -- "SCHEDULED_AT {planned_hours, actual_hours}" --> Station
    Project -- "BELONGS_TO" --> Etapp
    Project -- "ACTIVE_IN" --> Week
    Worker -- "PRIMARY_STATION" --> Station
    Worker -- "CAN_COVER" --> Station
    Week -- "HAS_CAPACITY {total_capacity, total_planned, deficit}" --> Station
    Product -- "REQUIRES" --> Station

Q2. Why Not Just SQL? (20 pts)
SQL Version:
SELECT w.name, p.project_name 
FROM workers w 
JOIN worker_coverage wc ON w.worker_id = wc.worker_id
JOIN stations s ON wc.station_code = s.station_code 
JOIN production pr ON s.station_code = pr.station_code 
JOIN projects p ON pr.project_id = p.project_id 
WHERE s.station_code = '016' AND w.name != 'Per Gustafsson';
Cypher Version:
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {station_code: '016'})<-[:SCHEDULED_AT]-(p:Project)
WHERE w.name <> 'Per Gustafsson'
RETURN w.name AS Backup_Worker, p.project_name AS Affected_Project
Why the graph version is better: The graph version makes it immediately obvious how workers, stations, and projects are connected without requiring expensive mapping tables or complex JOIN logic. In Cypher, you visually draw the path (Worker -> Station <- Project).

Q3. Spot the Bottleneck (20 pts)
Identifying the overload: According to the capacity data, Weeks 1 and 2 have the largest capacity deficits (-132 and -125 hours). The production data shows the 011 FS IQB and 012 Förmontering IQB stations have highly concurrent schedules across almost all projects during these weeks, causing the massive bottleneck.
Cypher Query:
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > (r.planned_hours * 1.10)
RETURN s.station_name, collect(p.project_name) AS Over_Budget_Projects
Modeling this alert: We can add a status: 'Bottleneck' property directly to the [:SCHEDULED_AT] relationship when actual hours exceed planned capacity, or create a dynamic (:Bottleneck) node linked to the specific (Station) and (Week).
For example, in Week 1, the factory had a capacity deficit of -132 hours. A major bottleneck was Station 014 (Svets o montage), where multiple projects went over their scheduled time. Project P03 planned for 42.0 hours but actually took 48.0 hours, and Project P08 planned for 40.0 hours but actually took 44.0 hours.

Q4. Vector + Graph Hybrid (20 pts)
What to embed: Embed the unstructured text of the "project descriptions" and "product requirements".
Hybrid Query:
CALL db.index.vector.queryNodes('project_embeddings', 5, $search_embedding) YIELD node AS p, score
MATCH (p)-[r:SCHEDULED_AT]->(s:Station)
WHERE ((r.actual_hours - r.planned_hours) / r.planned_hours) < 0.05
RETURN p.project_name, score, s.station_name
Why this is more useful: Keyword filtering is rigid. Vector search understands the semantic meaning to find similar past scopes (e.g., matching "hospital" to the existing "Sjukhus Linköping" project), while the graph enforces hard factual constraints (like ensuring historical variance is < 5%).

Q5. Your L6 Plan (20 pts)
Node Labels: Project, Product, Station, Worker, Week
Relationship Types: (Project)-[:PRODUCES]->(Product) (Project)-[:SCHEDULED_AT]->(Station) (Worker)-[:WORKS_AT]->(Station) (Worker)-[:CAN_COVER]->(Station) (Week)-[:HAS_CAPACITY]->(Station)
Dashboard Panels: Project Overview: A table showing all projects with planned vs actual hours. Station Load: An interactive Plotly bar chart visualizing hours per station. Worker Coverage: A matrix showing which workers can cover which stations.
Cypher Queries: Project Overview: MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station) RETURN p.project_name, sum(r.planned_hours), sum(r.actual_hours) Station Load: MATCH (s:Station)<-[r:SCHEDULED_AT]-(p:Project) RETURN s.station_name, r.week, r.planned_hours, r.actual_hours Worker Coverage: MATCH (w:Worker)-[:CAN_COVER]->(s:Station) RETURN w.name, collect(s.station_name)
