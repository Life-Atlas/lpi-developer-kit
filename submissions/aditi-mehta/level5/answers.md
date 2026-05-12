# Level 5 — Graph Thinking
**Name:** Aditi Mehta

### Q1. Model It

*Note: The visual diagram for this graph schema has been submitted in this folder as `schema.md` using the Mermaid format.*

**Node Labels (8 total):**
1. `Project`
2. `Product`
3. `Station`
4. `Worker`
5. `Week`
6. `Etapp`
7. `Skill`
8. `Factory`

**Relationship Types (8 total):**
1. `PRODUCES` (Project → Product)
2. `SCHEDULED_AT` (Project → Station)
3. `BELONGS_TO` (Project → Etapp)
4. `PLANNED_IN` (Project → Week)
5. `WORKS_AT` (Worker → Station)
6. `CAN_COVER` (Worker → Station)
7. `CERTIFIED_FOR` (Worker → Skill)
8. `HAS_CAPACITY` (Week → Factory)

**Data-Carrying Relationships (3 total):**
1. `SCHEDULED_AT` carries: `{week, planned_hours, actual_hours}`
2. `HAS_CAPACITY` carries: `{own, hired, overtime, deficit}`
3. `PRODUCES` carries: `{quantity, unit_factor}`

### Q2. Why Not Just SQL?

**1. SQL Query**

*(Assuming standard relational tables: `Workers`, `Worker_Station_Coverage`, `Stations`, `Production_Schedule`, and `Projects`)*
```sql
SELECT DISTINCT 
    w.name AS Backup_Worker, 
    p.project_name AS Affected_Project
FROM Stations s
JOIN Worker_Station_Coverage wc ON s.station_code = wc.station_code
JOIN Workers w ON wc.worker_id = w.worker_id
JOIN Production_Schedule ps ON s.station_code = ps.station_code
JOIN Projects p ON ps.project_id = p.project_id
WHERE s.station_code = '016' 
  AND w.name != 'Per Gustafsson';
```

**2. Cypher Query**

*(Using the schema defined in Q1)*
```cypher
MATCH (w:Worker)-[:CAN_COVER|CERTIFIED_FOR]->(s:Station {code: '016'})<-[:SCHEDULED_AT]-(p:Project)
WHERE w.name <> 'Per Gustafsson'
RETURN w.name AS Backup_Worker, collect(DISTINCT p.name) AS Affected_Projects
```

**3. The Graph Advantage**

In SQL, linking a worker's capacity to a project's risk requires traversing multiple artificial junction tables (`Worker_Station_Coverage`, `Production_Schedule`). This generates a massive Cartesian product of duplicated rows that must be heavily filtered using computationally expensive table scans. In the graph version, the `Station` node naturally acts as a hub. Cypher simply walks the existing incoming `CAN_COVER` and `SCHEDULED_AT` relationship arrows, returning a clean, aggregated list of projects natively without any complex foreign-key mapping.

### Q3. Spot the Bottleneck

**1. Bottleneck Analysis**

Based on `factory_capacity.csv`, the factory experiences significant capacity deficits in week **w1 (-132 hours)** and week **w2 (-125 hours)**. Cross-referencing this with `factory_production.csv`, the primary cause of this overload is the simultaneous high demand from **Project P01 (Stålverket Borås)** and **Project P02 (Kontorshus Mölndal)**. Both projects require heavy concurrent hours at **Station 011 (FS IQB)** and **Station 012 (Förmontering IQB)** during these initial weeks, exceeding the available workforce capacity.

**2. Cypher Query**

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > (r.planned_hours * 1.10)
RETURN s.name AS Station, 
       collect(p.name) AS Overloaded_Projects, 
       sum(r.actual_hours - r.planned_hours) AS Total_Excess_Hours
```

**3. Modeling the Alert**

I would model this alert using a **dynamic secondary label `(:Bottleneck)`** on the affected `Station` nodes combined with a **specific relationship property**. When a query detects that `actual_hours` exceeds `planned_hours` by the 10% threshold, the system should:
*   Apply the `(:Bottleneck)` label to the `Station` node for real-time visual flagging in the dashboard.
*   Update a `variance_severity` property on the `SCHEDULED_AT` relationship (e.g., `severity: 'CRITICAL'`).
This approach allows for high-performance filtering—instantly finding all troubled areas by querying `MATCH (s:Bottleneck)`—without having to perform mathematical calculations across every relationship in the database during every page load.


### Q4. Vector + Graph Hybrid

**1. What to Embed**

To handle free-text requests effectively, I would embed the **Project Descriptions and Scope Notes** (e.g., historical RFPs, client emails, special requirements). While product specs (like "450 meters" or "IQB") are easily queried via standard Cypher/SQL `WHERE` clauses, the *context* (e.g., "hospital extension," "tight timeline," "strict QA") contains semantic meaning that traditional databases cannot parse. 

**2. The Hybrid Query**

*(Assuming a Neo4j Vector Index named `project_embeddings` and incoming parameters `$queryEmbedding` for the new request and `$targetStations` for the required routing).*

```cypher
// Step 1: Vector Search (Find semantically similar past projects)
CALL db.index.vector.queryNodes('project_embeddings', 10, $queryEmbedding) 
YIELD node AS pastProject, score

// Step 2: Graph Traversal & Filtering (Match stations and check variance)
MATCH (pastProject)-[r:SCHEDULED_AT]->(s:Station)
WHERE s.code IN $targetStations 
  // Calculate absolute variance < 5%
  AND abs(r.actual_hours - r.planned_hours) / r.planned_hours < 0.05 

// Step 3: Return the vetted historical matches
RETURN pastProject.name AS Recommended_Reference_Project, 
       score AS Semantic_Similarity, 
       collect(s.name) AS Successful_Stations,
       sum(r.actual_hours) AS Total_Actual_Hours
ORDER BY score DESC
```

**3. Why this is more useful than just filtering by product type**

Filtering strictly by "Product = IQB" ignores the human and contextual realities of manufacturing. A 450m IQB beam order for a basic warehouse behaves entirely differently on the factory floor than a 450m IQB order for a hospital with tight deadlines and extreme QA tolerances. 
The **Vector Search** captures the *semantic intent and context* ("This feels like that rushed hospital job from last year"), while the **Graph Traversal** grounds that similarity in *operational reality* ("Did we actually execute that similar job well at these specific stations?"). 

### Q5. My L6 Plan 

**1. Node Labels & CSV Mapping (8 Labels)**

* `Project`: Created from `factory_production.csv` (`project_id`, `project_name`).
* `Product`: Created from `factory_production.csv` (`product_type`).
* `Station`: Created from `factory_production.csv` and `factory_workers.csv` (`station_code`, `station_name`).
* `Worker`: Created from `factory_workers.csv` (`worker_id`, `name`).
* `Week`: Created from `factory_capacity.csv` and `factory_production.csv` (`week`).
* `Etapp`: Created from `factory_production.csv` (`etapp`).
* `Skill`: Created dynamically by parsing the `certifications` column in `factory_workers.csv`.
* `Factory`: A singleton node ("Main Factory") created to anchor factory-wide capacity data.

**2. Relationships & Creation Logic (8 Types)**

* `PRODUCES`: Created by matching `Project` to `Product`, attaching `quantity` and `unit_factor` from `factory_production.csv`.
* `SCHEDULED_AT`: Created by matching `Project` to `Station`, attaching `week`, `planned_hours`, and `actual_hours` from `factory_production.csv`.
* `BELONGS_TO`: Created by linking `Project` to its respective `Etapp`.
* `PLANNED_IN`: Created by linking `Project` to `Week`.
* `WORKS_AT`: Created by matching `Worker` to their primary `Station` in `factory_workers.csv`.
* `CAN_COVER`: Created by parsing the comma-separated strings in `factory_workers.csv` and linking `Worker` to secondary `Station` nodes.
* `CERTIFIED_FOR`: Created by parsing the certifications in `factory_workers.csv` and linking `Worker` to `Skill` nodes.
* `HAS_CAPACITY`: Created from `factory_capacity.csv`, attaching `own`, `hired`, `overtime`, and `deficit` hours to the arrow between `Week` and the `Factory` node.

**3. Streamlit Dashboard Panels & Cypher Queries**

* **Panel 1: Project Overview**
    * *Concept:* High-level KPI metrics and a table showing planned vs. actual hours and variance percentages for all 8 projects.
    * *Cypher Query:* `MATCH (p:Project) OPTIONAL MATCH (p)-[r:SCHEDULED_AT]->(:Station) OPTIONAL MATCH (p)-[:PRODUCES]->(pr:Product) RETURN p.name AS Project, sum(r.planned_hours) AS Planned_Hours, sum(r.actual_hours) AS Actual_Hours, collect(DISTINCT pr.type) AS Products`

* **Panel 2: Station Load (Weekly Timeline)**
    * *Concept:* An interactive Plotly bar chart comparing planned vs. actual hours per station across weeks, with dynamic filtering and warnings for over-budget stations.
    * *Cypher Query:*
        `MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station) RETURN s.name AS Station, r.week AS Week, sum(r.planned_hours) AS Planned, sum(r.actual_hours) AS Actual ORDER BY Week`

* **Panel 3: Capacity Tracker**
    * *Concept:* A factory-wide table tracking weekly capacity against total planned demand. Includes mathematical transformations to isolate deficits and highlight shortfalls in red.
    * *Cypher Query:*
        `MATCH (wk:Week)-[c:HAS_CAPACITY]->(f:Factory) RETURN wk.name AS Week, c.own AS Own_Hours, c.hired AS Hired, c.overtime AS Overtime, c.deficit AS Deficit ORDER BY Week`

* **Panel 4: Worker Coverage Matrix**
    * *Concept:* A dynamic cross-training matrix (Worker vs. Station) built using Pandas crosstab. It programmatically identifies and highlights Single Points of Failure (SPOF) with custom business impact warnings.
    * *Cypher Query:*
        `MATCH (w:Worker), (s:Station) WHERE s.name IS NOT NULL OPTIONAL MATCH (w)-[r:CAN_COVER|WORKS_AT]->(s) RETURN w.name AS Worker, s.name AS Station, count(r) > 0 AS Can_Cover`

* **Panel 5: The Self-Test Validator**
    * *Concept:* Automated grading checks to verify the Neo4j database is populated, structured correctly, and meets all auto-grader rubric minimums (labels, relationships, and variance logic).

**Stream Bonus C: Predictive Forecast**
To provide executive-level insights, the dashboard will include a "Predictive Forecast" module. 
- **Logic:** Utilize the `scipy.stats` library to perform linear regression on historical station load data.
- **Visualization:** A Plotly `graph_objects` chart showing historical actuals vs. a dashed trajectory line for Week 9, including a 95% confidence interval (calculated via standard error).
- **Business Goal:** Identify which stations will exceed a 15% growth threshold above the planned baseline before the week begins.
