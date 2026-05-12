# Level 5 — Graph Thinking

**Author:** Touqeer Hamdani  
**Date:** May 2026

---

## Q1. Model It (20 pts)

### Graph Schema

> Full diagram: [`schema.md`](./schema.md)

The graph schema is designed around the 3 factory CSVs and captures the full production planning domain — projects, what they produce, where they're built, who builds them, and when.

### Node Labels (8)

| Label | Source | Key Properties | Count |
|-------|--------|----------------|-------|
| **Project** | production.csv → `project_id`, `project_number`, `project_name` | project_id, project_number, project_name | 8 |
| **Product** | production.csv → `product_type`, `unit` | product_type, unit | 7 |
| **Station** | production.csv → `station_code`, `station_name` | station_code, station_name | 10 |
| **Worker** | workers.csv → `worker_id`, `name` | worker_id, name, role, hours_per_week, type | 14 |
| **Week** | capacity.csv → `week` | week_id | 8 |
| **Factory** | Implicit overall plant | factory_name | 1 |
| **Certification** | workers.csv → `certifications` (split by comma) | cert_name | 23 unique |
| **Etapp** | production.csv → `etapp` | etapp_name | 2 (ET1, ET2) |

### Relationship Types (9)

| Relationship | Direction | Properties |
|-------------|-----------|------------|
| **PRODUCES** | `(Project)→(Product)` | `quantity`, `unit_factor`, `unit` |
| **SCHEDULED_AT** | `(Project)→(Station)` | `planned_hours`, `actual_hours`, `completed_units`, `week`, `etapp`, `bop`, `variance_pct` |
| **ACTIVE_IN** | `(Project)→(Week)` | — |
| **IN_PHASE** | `(Project)→(Etapp)` | — |
| **WORKS_AT** | `(Worker)→(Station)` | — (primary station assignment) |
| **CAN_COVER** | `(Worker)→(Station)` | — (cross-trained coverage) |
| **HOLDS** | `(Worker)→(Certification)` | — |
| **LOADED_IN** | `(Station)→(Week)` | `total_planned`, `total_actual` |
| **HAS_CAPACITY** | `(Week)→(Factory)` | `own_hours`, `hired_hours`, `overtime_hours`, `total_planned`, `deficit` |

### Data-Carrying Relationships (4)

1. **PRODUCES** — Each project-to-product edge carries `{quantity: 600, unit_factor: 1.77, unit: "meter"}`, capturing the production spec. This lets you query things like "which projects produce more than 500 meters of IQB?" directly from the relationship.

2. **SCHEDULED_AT** — The core operational edge. Each project-station-week combination carries `{planned_hours: 48.0, actual_hours: 45.2, completed_units: 28, week: "w1", etapp: "ET1", bop: "BOP1"}`. This is the richest relationship in the graph — it's where all the variance analysis lives, and where we track the phase (`etapp`, `bop`) of the work.

3. **LOADED_IN** — Aggregated station load per week: `{total_planned: 393, total_actual: 410}`. Enables capacity-vs-demand queries at the station level without re-aggregating from SCHEDULED_AT every time. *(Note: these properties are calculated by aggregating `SCHEDULED_AT` edges during graph construction, as `factory_capacity.csv` only provides factory-wide totals).*

4. **HAS_CAPACITY** — Links each week to the global factory, carrying the `{own_hours, hired_hours, overtime_hours, total_planned, deficit}` workforce metrics straight out of `factory_capacity.csv`. This perfectly mirrors the exact relationship pattern requested in the L6 instructions.

### Design Decisions

- **Certification as a node** (not a Worker property): Workers share certifications (e.g., multiple workers hold MIG/MAG). Modeling it as a node enables queries like "find all workers certified for TIG welding" with a single hop instead of string parsing.
- **Etapp and BOP as properties on SCHEDULED_AT**: Since a single project can move through different BOPs (phases) across different stations and weeks, treating `bop` and `etapp` as edge properties accurately models *when and where* that phase occurs, rather than applying a blanket phase to the entire project.
- **SCHEDULED_AT carries `week` as a property** rather than routing through Week nodes: This keeps the most queried relationship (planned vs actual hours) as a direct Project→Station edge. The separate ACTIVE_IN relationship to Week handles the temporal dimension when needed.
- **Etapp as a node** (for L6 compliance): The L6 spec explicitly requires `Etapp` as a node label. From a pure design perspective, etapp works better as an edge property on SCHEDULED_AT (only 2 values, no properties of its own), and we keep it there for direct querying. The `Etapp` node + `IN_PHASE` relationship is included to meet the L6 minimum graph requirements.

### Implementation Notes for L6

- **SCHEDULED_AT creates parallel edges**: A single (Project, Station) pair can have multiple SCHEDULED_AT edges — one per week/etapp/bop/product combination. For example, P01→Station 011 appears in both w1 and w2. Additionally, P05→Station 018 has two rows in the same week (w1) with the same etapp/bop (ET2/BOP3) but different product types (SB and SD). In `seed_graph.py`, use `MERGE` with a composite key including `week`, `etapp`, `bop`, **and** `product_type` to ensure idempotency without data loss:
  ```cypher
  MERGE (p:Project {project_id: row.project_id})
  MERGE (s:Station {station_code: row.station_code})
  MERGE (p)-[r:SCHEDULED_AT {week: row.week, etapp: row.etapp, bop: row.bop, product_type: row.product_type}]->(s)
  SET r.planned_hours = toFloat(row.planned_hours),
      r.actual_hours = toFloat(row.actual_hours),
      r.completed_units = toInteger(row.completed_units)
  ```
- **PRODUCES needs deduplication**: The same (Project, Product) pair appears across many CSV rows (different weeks/stations), but the production spec (`quantity`, `unit_factor`, `unit`) is constant per pair. Create **one** PRODUCES edge per unique `(project_id, product_type)` — either deduplicate in Python before loading, or use `MERGE` on the pair:
  ```cypher
  MERGE (p:Project {project_id: row.project_id})
  MERGE (prod:Product {product_type: row.product_type})
  MERGE (p)-[r:PRODUCES]->(prod)
  SET r.quantity = toInteger(row.quantity),
      r.unit_factor = toFloat(row.unit_factor),
      r.unit = row.unit
  ```

---

## Q2. Why Not Just SQL? (20 pts)

*Prompt: "Which workers are certified to cover Station 016 (Gjutning) when Per Gustafsson is on vacation, and which projects would be affected?"*

> **Data Reality Check:** In `factory_workers.csv`, the worker at Station 016 is actually named **Per Hansen** (W07), not Per Gustafsson. The queries below reflect the actual data.

### 1. The SQL Query
Assuming a standard relational schema with normalized tables (`Workers`, `Worker_Coverage`, `Stations`, `Project_Schedules`, `Projects`), we must join 5 tables to traverse the relationships:

```sql
SELECT 
    w.name AS CoveringWorker, 
    GROUP_CONCAT(DISTINCT p.project_name) AS AffectedProjects
FROM Workers w
JOIN Worker_Coverage wc ON w.worker_id = wc.worker_id
JOIN Project_Schedules ps ON wc.station_code = ps.station_code
JOIN Projects p ON ps.project_id = p.project_id
WHERE wc.station_code = '016' 
  AND w.name != 'Per Hansen'
GROUP BY w.name;
```

### 2. The Cypher Query
Using our graph schema, the query becomes a visual representation of the path: `Worker → Station ← Project`:

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station {station_code: "016"})<-[:SCHEDULED_AT]-(p:Project)
WHERE w.name <> "Per Hansen"
RETURN w.name AS CoveringWorker, collect(DISTINCT p.project_name) AS AffectedProjects
```

### 3. What the graph makes obvious that SQL hides
SQL forces you to think about database mechanics—specifically, resolving foreign keys across multiple intermediate junction tables just to traverse a simple real-world relationship. The graph version (Cypher) hides those storage mechanics and makes the network topology instantly obvious, perfectly mirroring how a human visualizes the factory floor: "Find workers who point to this station, and find projects that point to this station."

---

## Q3. Spot the Bottleneck (20 pts)

### 1. Identifying the Overload

From `factory_capacity.csv`, five out of eight weeks show capacity deficits:

| Week | Total Capacity | Total Planned | Deficit |
|------|---------------|---------------|---------|
| w1 | 480 | 612 | **-132** |
| w2 | 520 | 645 | **-125** |
| w4 | 500 | 550 | **-50** |
| w6 | 440 | 520 | **-80** |
| w7 | 520 | 600 | **-80** |

Using `factory_production.csv` to drill into the two worst weeks (w1 and w2):

**Volume Bottleneck (Station 011):** Station 011 (FS IQB) is the primary structural bottleneck. In w1, it is scheduled to handle work from 7 projects simultaneously (P01, P02, P03, P04, P05, P07, P08). As the entry point of the manufacturing pipeline, it creates a massive initial capacity constraint.

**Volume Driver (Project P05):** Project P05 (Sjukhus Linköping ET2) is the largest individual contributor (1200 meters of IQB). It heavily loads the early-stage stations in w1.

**Efficiency Overruns (Station 016):** While 011 causes deficits via sheer scheduled volume, Station 016 (Gjutning / Casting) causes deficits through poor execution efficiency. Looking at the worst overruns by percentage (actual vs planned hours):

| Project | Station | Week | Planned | Actual | Variance |
|---------|---------|------|---------|--------|----------|
| P03 | 016 Gjutning | w2 | 28.0 | 35.0 | **+25%** |
| P04 | 018 SB B/F-hall | w1 | 19.0 | 22.0 | **+16%** |
| P05 | 016 Gjutning | w2 | 35.0 | 40.0 | **+14%** |
| P03 | 014 Svets o montage | w1 | 42.0 | 48.0 | **+14%** |
| P08 | 016 Gjutning | w3 | 22.0 | 25.0 | **+14%** |

Station 016 appears repeatedly in the worst overruns. Therefore, the factory capacity deficit is a dual problem: structural schedule overload at the start of the pipeline (011), and severe execution overruns at the finishing stages (016).

### 2. Cypher Query

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.station_name AS Station, 
       collect({
           project: p.project_name, 
           variance_pct: round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1)
       }) AS Overruns
```

### 3. Modeling the Alert as a Graph Pattern

**Approach: Store `variance_pct` as a numeric property on SCHEDULED_AT.**

During graph seeding, compute and store the variance percentage on each scheduling edge:

```cypher
SET r.variance_pct = round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1)
```

This means the threshold is applied at **query time**, not at seed time — making it fully flexible:

```cypher
// 10% threshold for alerts
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.variance_pct > 10
RETURN s.station_name, p.project_name, r.variance_pct ORDER BY r.variance_pct DESC

// 5% threshold for Q4's hybrid query (finding well-executed projects)
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.variance_pct < 5
RETURN p.project_name, avg(r.variance_pct)
```

**Why this over a `(:Bottleneck)` node or a boolean flag:**
- A dedicated `(:Alert)` node adds schema complexity (extra nodes + relationships) for what is essentially a simple numeric comparison on existing data.
- A boolean `overrun: true/false` flag loses the magnitude — a 11% overrun and a 50% overrun both say `true`, and changing the threshold requires re-seeding.
- A numeric `variance_pct` preserves full fidelity, keeps the data where it naturally belongs (on the scheduling edge), and lets dashboards apply any threshold on the fly.

---

## Q4. Vector + Graph Hybrid (20 pts)

*Prompt text:* "450 meters of IQB beams for a hospital extension in Linköping, similar scope to previous hospital projects, tight timeline"

### 1. What to Embed
There are two ways to handle this, ranging from a simple baseline to a robust production system:

**Approach A: Composite Description (Baseline & Simplicity)**
The simplest method is to create a single composite text block for each project combining its name, location, building type, and product scope (e.g., `"Sjukhus Linköping ET2, hospital, Linköping, 1200m IQB..."`). We embed this entire paragraph. This captures the overall semantic context ("vibe") perfectly for basic similarity searches.

**Approach B: Metadata Extraction & Filtering (Robust Precision)**
Relying entirely on a single embedding can sometimes be risky (e.g., the model might heavily weight "tight timeline" and return a project from the wrong city). A more precise, production-grade approach is to use an LLM to extract structured metadata from the free-text query (e.g., `location: "Linköping"`, `material: "IQB beams"`). We then use those extracted properties to perform exact comparisons and use them as **hard graph filters**, relying on the vector embedding purely for the fuzzy semantic matching of the remaining context.

*For the L5/L6 scope, Approach A is the standard expected baseline, but Approach B represents a more advanced architecture.*

### 2. The Hybrid Query
This query performs a two-stage pipeline: it uses Neo4j's vector index to find semantically similar projects, and then traverses the graph to filter out projects that were executed poorly.

```cypher
// Stage 1: Vector Search for top 5 semantic matches
CALL db.index.vector.queryNodes('project_embeddings', 5, $queryEmbedding)
YIELD node AS candidate, score

// Stage 2: Graph Traversal for operational quality
MATCH (candidate)-[r:SCHEDULED_AT]->(s:Station)
WHERE s.station_code IN ["011", "012", "013", "014", "016", "017"] // IQB pipeline stations
  AND r.variance_pct < 5 // Must be a well-executed project
  
RETURN candidate.project_name AS ReferenceProject, 
       score AS SimilarityScore,
       collect(DISTINCT s.station_name) AS StationsUsed
ORDER BY score DESC
```

### 3. Why this is better than just filtering by product type
If we only filtered the database by `product_type = 'IQB'`, we would return almost every project in the factory's history (P01–P06, P08). This is useless for accurate planning. 

The hybrid approach provides two crucial layers of intelligence:
1. **The Vector Layer** captures human context. A "hospital extension in Linköping" is semantically similar to past project P05 ("Sjukhus Linköping ET2") due to building type and location, whereas a standard filter would treat it exactly the same as a parking garage in Helsingborg (P04).
2. **The Graph Layer** ensures operational reliability. By traversing the `SCHEDULED_AT` edges and checking the `variance_pct` (our property from Q3), we ensure that the semantically matched project was actually executed well on the factory floor, making it a trustworthy baseline for scheduling the new request.

---

## Q5. Your L6 Plan (20 pts)

### 1. Node Labels → CSV Column Mappings

| Node Label | Source | CSV Columns | Key | Count |
|------------|--------|-------------|-----|-------|
| **Project** | production.csv | `project_id`, `project_number`, `project_name` | `project_id` | 8 |
| **Product** | production.csv | `product_type`, `unit` | `product_type` | 7 |
| **Station** | production.csv | `station_code`, `station_name` | `station_code` | 10 |
| **Worker** | workers.csv | `worker_id`, `name`, `role`, `hours_per_week`, `type` | `worker_id` | 14 |
| **Week** | capacity.csv | `week` | `week` | 8 |
| **Factory** | Implicit | — (single node) | — | 1 |
| **Certification** | workers.csv | `certifications` (comma-split) | `cert_name` | 23 |
| **Etapp** | production.csv | `etapp` | `etapp_name` | 2 |

### 2. Relationship Types → What Creates Them

| Relationship | Created By | Properties |
|---|---|---|
| **PRODUCES** | `MERGE` on unique `(project_id, product_type)` pairs from production.csv | `quantity`, `unit_factor`, `unit` |
| **SCHEDULED_AT** | Each row of production.csv → `MERGE` with composite key `{week, etapp, bop, product_type}` | `planned_hours`, `actual_hours`, `completed_units`, `week`, `etapp`, `bop`, `product_type`, `variance_pct` |
| **ACTIVE_IN** | Distinct `(project_id, week)` pairs from production.csv | — |
| **IN_PHASE** | Distinct `(project_id, etapp)` pairs from production.csv | — |
| **WORKS_AT** | workers.csv → `primary_station` column | — |
| **CAN_COVER** | workers.csv → `can_cover_stations` (comma-split, one edge per station) | — |
| **HOLDS** | workers.csv → `certifications` (comma-split, one edge per cert) | — |
| **LOADED_IN** | Aggregated from SCHEDULED_AT per (station, week) during seeding | `total_planned`, `total_actual` |
| **HAS_CAPACITY** | Each row of capacity.csv | `own_hours`, `hired_hours`, `overtime_hours`, `total_planned`, `deficit` |

#### Seed Script Constraints & Idiosyncrasies
- **Uniqueness Constraints:** To ensure idempotency during the `MERGE` process, the script must create constraints beforehand:
  `CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE` (and similarly for Station, Worker, Week, Product).
- **Foreman Assignment:** Worker W11 (Victor Elm) is listed as a Foreman with `primary_station = "all"`. The seed script must handle `"all"` correctly (either by skipping the `WORKS_AT` edge and relying solely on his `can_cover_stations` list, or by explicitly creating edges to all 10 stations) to avoid creating a junk station node named "all".

### 3. Streamlit Dashboard Panels (4 + Self-Test)

#### Page 1: Project Overview (10 pts)
A summary table showing all 8 projects with total planned hours, total actual hours, variance %, and products involved.

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WITH p, sum(r.planned_hours) AS planned, sum(r.actual_hours) AS actual
MATCH (p)-[:PRODUCES]->(prod:Product)
RETURN p.project_name AS Project, planned AS PlannedHours, actual AS ActualHours,
       round((actual - planned) / planned * 100, 1) AS VariancePct,
       collect(DISTINCT prod.product_type) AS Products
ORDER BY p.project_id
```

#### Page 2: Station Load (10 pts)
Interactive Plotly bar chart showing hours per station across weeks. Stations where actual > planned are highlighted in red.

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN s.station_code AS StationCode, s.station_name AS Station, r.week AS Week,
       sum(r.planned_hours) AS Planned, sum(r.actual_hours) AS Actual
ORDER BY StationCode, Week
```

#### Page 3: Capacity Tracker (10 pts)
Weekly capacity (own + hired + overtime) vs total planned demand. Deficit weeks are color-coded red.

```cypher
MATCH (w:Week)-[r:HAS_CAPACITY]->(f:Factory)
RETURN w.week_id AS Week, 
       r.own_hours + r.hired_hours + r.overtime_hours AS TotalCapacity,
       r.total_planned AS PlannedDemand,
       r.deficit AS Deficit
ORDER BY w.week_id
```

#### Page 4: Worker Coverage (10 pts)
Matrix showing which workers can cover which stations. Single-point-of-failure stations (only 1 worker) are flagged.

```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
RETURN s.station_name AS Station, collect(w.name) AS Workers, count(w) AS WorkerCount
ORDER BY WorkerCount ASC
```

#### Navigation (5 pts)
A sidebar will be implemented to allow users to switch seamlessly between the 4 dashboard pages and the Self-Test page without reloading the app.

#### Page 5: Self-Test (20 pts)
Automated green/red checklist verifying: Neo4j connection, node count ≥ 50, relationship count ≥ 100, 6+ node labels, 8+ relationship types, and variance query returns results.

