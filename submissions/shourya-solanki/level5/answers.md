# Level 5 — Graph Thinking
# Author: Shourya Solanki | Track: Agent Builders


## Q1. Model It

### Graph Schema

Node Labels:

- (:Project {project_id, project_number, project_name})
- (:Product {product_type, unit, unit_factor})
- (:Station {station_code, station_name})
- (:Worker {worker_id, name, role, hours_per_week, type})
- (:Week {week_id})
- (:Certification {name})
- (:WorkPackage {etapp, bop})

Relationship Types:

- (Project)-[:HAS_PRODUCT]->(Product)
- (Project)-[:SCHEDULED_IN]->(Week)
- (Project)-[:PRODUCED_AT {planned_hours, actual_hours, completed_units}]->(Station)
- (Worker)-[:PRIMARY_STATION]->(Station)
- (Worker)-[:CAN_COVER]->(Station)
- (Worker)-[:HAS_CERTIFICATION]->(Certification)
- (Worker)-[:WORKED_AT {hours: 38.5, week: "w1"}]->(Station)
- (Station)-[:PROCESSES]->(Product)
- (Week)-[:HAS_DEFICIT {total_capacity, total_planned, deficit}]->(Station)
- (WorkPackage)-[:PART_OF]->(Project)

See schema.md for Mermaid diagram.


## Q2. Why Not Just SQL?

### The Question
Which workers are certified to cover Station 016 (Gjutning) when Per Hansen
is on vacation, and which projects would be affected?

### SQL Version

SELECT w.name, w.certifications, p.project_name
FROM workers w
JOIN worker_stations ws ON w.worker_id = ws.worker_id
JOIN production p ON ws.station_code = p.station_code
WHERE ws.station_code = '016'
AND w.worker_id != 'W07'
AND w.can_cover_stations LIKE '%016%'
AND p.week IN (SELECT week FROM vacations WHERE worker_id = 'W07');

### Cypher Version

MATCH (absent:Worker {name: "Per Hansen"})-[:PRIMARY_STATION]->(s:Station {station_code: "016"})
MATCH (backup:Worker)-[:CAN_COVER]->(s)
WHERE backup <> absent
MATCH (p:Project)-[:PRODUCED_AT]->(s)
RETURN backup.name, backup.certifications, collect(p.project_name) AS affected_projects

### What the graph version makes obvious

In SQL, coverage relationships are buried in comma-separated strings or
junction tables — you need multiple joins and LIKE queries just to find
who can cover a station. In the graph, CAN_COVER is a first-class
relationship: the traversal is a single MATCH. More importantly, the
graph immediately shows the blast radius — which projects are affected
is just one more hop, not another join. The SQL version requires you to
know the schema intimately; the graph version makes the question feel
like reading a sentence.


## Q3. Spot the Bottleneck

### Weeks with Capacity Deficits (from factory_capacity.csv)

- w1: deficit -132 (worst)
- w2: deficit -125
- w4: deficit -50
- w6: deficit -80
- w7: deficit -80

### Projects/Stations Causing Overload

From factory_production.csv, the most overloaded station is 011 (FS IQB)
— it appears in nearly every project simultaneously in w1 and w2.
Projects P01 (Stålverket Borås) and P03 (Lagerhall Jönköping) are the
heaviest contributors, both with large IQB quantities running through
station 011 in the same weeks.

### Cypher Query

MATCH (p:Project)-[r:PRODUCED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.station_name, p.project_name,
       r.planned_hours, r.actual_hours,
       round((r.actual_hours - r.planned_hours) / r.planned_hours * 100) AS variance_pct
ORDER BY variance_pct DESC

### Modeling the Alert as a Graph Pattern

I would create a (:Bottleneck) node linked to the station and week:

(:Week {week_id: "w1"})-[:HAS_BOTTLENECK]->(:Bottleneck {severity: "high", deficit: -132})-[:AT_STATION]->(:Station {station_code: "011"})

This makes bottlenecks queryable and visible in the graph without
scanning every production row. An agent or dashboard can MATCH
(:Bottleneck {severity: "high"}) and immediately traverse to affected
projects and available workers.


## Q4. Vector + Graph Hybrid

### What to Embed

I would embed project descriptions — specifically a concatenation of:
project_name + product_type + quantity + unit + station context.

Example embedding input:
"Lagerhall Jönköping — IQB 900 meters, stations 011/012/013/014, ET1"

Worker skills could also be embedded for the Boardy pattern, but for
project matching the project description embedding is most useful.

### Hybrid Query

First: vector search finds top-5 similar past projects by embedding distance.
Then: graph filter applies structural constraints.

// Assume vectorIndex on Project nodes
CALL db.index.vector.queryNodes('project_embeddings', 5, $query_embedding)
YIELD node AS similar_project, score
MATCH (similar_project)-[r:PRODUCED_AT]->(s:Station)
WHERE abs(r.actual_hours - r.planned_hours) / r.planned_hours <= 0.05
RETURN similar_project.project_name, collect(s.station_name) AS stations,
       score AS similarity
ORDER BY similarity DESC

### Why This Is More Useful Than Filtering by Product Type

Filtering by product type (IQB, SB, etc.) finds structurally similar
projects but misses scope and complexity. A hospital with 450m of IQB
beams on a tight timeline is very different from a warehouse with the
same product type but 3x the time. The vector embedding captures the
full context — location, scope, urgency signals in free text — while
the graph filter ensures the matched projects actually ran through the
same stations with low variance. You get semantic similarity AND
operational reliability in one query.

This is exactly the Boardy pattern: vector finds whose needs embed
close to whose offers, graph confirms they're in the same community
and have compatible constraints.


## Q5. My L6 Blueprint

### Nodes and where they come from

The core nodes I'll create are Project, Station, Worker, Week, Product,
Certification, WorkPackage, and Capacity.

Project maps directly from factory_production.csv using project_id,
project_number, and project_name as properties. Each unique project_id
becomes one node.

Station comes from the same file — station_code and station_name.
9 unique stations in the dataset.

Worker comes from factory_workers.csv — worker_id, name, role,
hours_per_week, and type (permanent vs hired).

Week is created from both CSVs — the week column in production gives
me w1 through w8, and I'll attach capacity data from factory_capacity.csv
as properties: total_capacity, total_planned, deficit.

Product is derived from unique product_type + unit + unit_factor
combinations in the production file.

Certification is split from the comma-separated certifications column
in factory_workers.csv — each cert becomes its own node so I can
query "who has TIG certification" without string matching.

WorkPackage captures etapp and bop from the production file —
these represent project phases and bill of production packages.

### Relationships and what creates them

PRODUCED_AT connects Project to Station, carrying planned_hours,
actual_hours, and completed_units as properties. One row in
factory_production.csv = one PRODUCED_AT relationship per project/station/week combo.

HAS_PRODUCT connects Project to Product — derived from unique
project + product_type combinations.

SCHEDULED_IN connects Project to Week.

PRIMARY_STATION connects Worker to their main station from
factory_workers.csv.

CAN_COVER connects Worker to each station in their
can_cover_stations column after splitting on commas.

HAS_CERTIFICATION connects Worker to each Certification node
after splitting the certifications column.

HAS_CAPACITY connects Week to its capacity data — carries
total_capacity, total_planned, and deficit as properties.

PART_OF connects WorkPackage back to its Project.

### Three Streamlit panels

Panel 1 — Station Load Heatmap
A week-by-station grid showing planned vs actual hours. Cells turn
red when actual > planned by more than 10%. This is the first thing
the factory manager needs to see — where are we burning overtime?

Cypher behind it:
MATCH (p:Project)-[r:PRODUCED_AT]->(s:Station)
RETURN s.station_name, r.week, sum(r.planned_hours) AS planned,
sum(r.actual_hours) AS actual
ORDER BY s.station_code, r.week

Panel 2 — Capacity vs Demand Timeline
A bar chart per week showing total_capacity vs total_planned, with
the deficit plotted as a line underneath. Weeks w1, w2, w4, w6, w7
are all in deficit — this makes it immediately visible.

Cypher behind it:
MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
RETURN w.week_id, c.total_capacity, c.total_planned, c.deficit
ORDER BY w.week_id

Panel 3 — Worker Coverage Matrix
A table of stations vs available workers, showing how many people
can cover each station. Stations with only one qualified worker are
highlighted in orange — single points of failure. Clicking a station
shows which projects would be affected if that worker is unavailable.

Cypher behind it:
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN s.station_name, collect(w.name) AS workers, count(w) AS coverage
ORDER BY coverage ASC