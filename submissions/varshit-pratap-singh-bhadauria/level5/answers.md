\# Level 5: Graph Thinking Answers



\## Q1. Model It (20 pts)

Here is the graph schema capturing the relationships between the factory entities based on the production, capacity, and worker data.



\*\*6 Node Labels:\*\*

1\. `Project`

2\. `Product`

3\. `Station`

4\. `Worker`

5\. `Week`

6\. `Etapp`



\*\*8 Relationship Types:\*\*

1. (Project)-[:PRODUCES {quantity, unit_factor}]->(Product) 
2. (Project)-[:SCHEDULED_AT {planned_hours, actual_hours}]->(Station) 
3. (Week)-[:HAS_CAPACITY {total_capacity, total_planned, deficit}]->(Station)

4\. `(Project)-\[:BELONGS\_TO]->(Etapp)`

5\. `(Project)-\[:ACTIVE\_IN]->(Week)`

6\. `(Worker)-\[:PRIMARY\_STATION]->(Station)`

7\. `(Worker)-\[:CAN\_COVER]->(Station)`

8\. `(Product)-\[:REQUIRES]->(Station)`



\### Visual Diagram:

```mermaid

graph TD

&nbsp;   Project((Project))

&nbsp;   Product((Product))

&nbsp;   Station((Station))

&nbsp;   Worker((Worker))

&nbsp;   Week((Week))

&nbsp;   Etapp((Etapp))



&nbsp;   Project -- "PRODUCES {quantity, unit\_factor}" --> Product

&nbsp;   Project -- "SCHEDULED\_AT {planned\_hours, actual\_hours}" --> Station

&nbsp;   Project -- "BELONGS\_TO" --> Etapp

&nbsp;   Project -- "ACTIVE\_IN" --> Week

&nbsp;   Worker -- "PRIMARY\_STATION" --> Station

&nbsp;   Worker -- "CAN\_COVER" --> Station

&nbsp;   Week -- "HAS\_CAPACITY {total\_capacity, total\_planned, deficit}" --> Station

&nbsp;   Product -- "REQUIRES" --> Station

Q2. Why Not Just SQL? (20 pts)

1\. SQL Version:

SELECT w.name, p.project\_name 

FROM workers w 

JOIN worker\_coverage wc ON w.worker\_id = wc.worker\_id 

JOIN stations s ON wc.station\_code = s.station\_code 

JOIN production pr ON s.station\_code = pr.station\_code 

JOIN projects p ON pr.project\_id = p.project\_id 

WHERE s.station\_code = '016' AND w.name != 'Per Gustafsson';

2\. Cypher Version:

MATCH (w:Worker)-\[:CAN\_COVER]->(s:Station {station\_code: '016'})<-\[:SCHEDULED\_AT]-(p:Project)

WHERE w.name <> 'Per Gustafsson'

RETURN w.name AS Backup\_Worker, p.project\_name AS Affected\_Project

3\. Why the graph version is better: The graph version makes it immediately obvious how workers, stations, and projects are connected without requiring expensive mapping tables or complex JOIN logic. In Cypher, you visually draw the path (Worker -> Station <- Project).

### Q3. Spot the Bottleneck (20 pts)

1. Identifying the overload: According to the capacity data, Weeks 1 and 2 have the largest capacity deficits (-132 and -125 hours). The production data shows the 011 FS IQB and 012 Förmontering IQB stations have highly concurrent schedules across almost all projects during these weeks, causing the massive bottleneck.

2. Cypher Query:
```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > (r.planned_hours * 1.10)
RETURN s.station_name, collect(p.project_name) AS Over_Budget_Projects
Modeling this alert: We can add a status: 'Bottleneck' property directly to the [:SCHEDULED_AT] relationship when actual hours exceed planned capacity, or create a dynamic (:Bottleneck) node linked to the specific (Station) and (Week).
For example, in Week 1, the factory had a capacity deficit of -132 hours. A major bottleneck was Station 014 (Svets o montage), where multiple projects went over their scheduled time. Project P03 planned for 42.0 hours but actually took 48.0 hours, and Project P08 planned for 40.0 hours but actually took 44.0 hours.



Q4. Vector + Graph Hybrid (20 pts)

1\. What to embed: Embed the unstructured text of the "project descriptions" and "product requirements".

2\. Hybrid Query:

CALL db.index.vector.queryNodes('project\_embeddings', 5, $search\_embedding) YIELD node AS p, score

MATCH (p)-\[r:SCHEDULED\_AT]->(s:Station)

WHERE ((r.actual\_hours - r.planned\_hours) / r.planned\_hours) < 0.05

RETURN p.project\_name, score, s.station\_name

3\. Why this is more useful: Keyword filtering is rigid. Vector search understands the semantic meaning to find similar past scopes (e.g., matching "hospital" to the existing "Sjukhus Linköping" project), while the graph enforces hard factual constraints (like ensuring historical variance is < 5%).

Q5. Your L6 Plan (20 pts)

1\. Node Labels:

Project, Product, Station, Worker, Week

2\. Relationship Types:

(Project)-\[:PRODUCES]->(Product)

(Project)-\[:SCHEDULED\_AT]->(Station)

(Worker)-\[:WORKS\_AT]->(Station)

(Worker)-\[:CAN\_COVER]->(Station)

(Week)-\[:HAS\_CAPACITY]->(Station)

3\. Dashboard Panels:

Project Overview: A table showing all projects with planned vs actual hours.

Station Load: An interactive Plotly bar chart visualizing hours per station.

Worker Coverage: A matrix showing which workers can cover which stations.

4\. Cypher Queries:

Project Overview: MATCH (p:Project)-\[r:SCHEDULED\_AT]->(s:Station) RETURN p.project\_name, sum(r.planned\_hours), sum(r.actual\_hours)

Station Load: MATCH (s:Station)<-\[r:SCHEDULED\_AT]-(p:Project) RETURN s.station\_name, r.week, r.planned\_hours, r.actual\_hours

Worker Coverage: MATCH (w:Worker)-\[:CAN\_COVER]->(s:Station) RETURN w.name, collect(s.station\_name)



\*\*\*

