# Level 5 — Graph Thinking
## Factory Production Knowledge Graph

## Q1. schema.md uploaded in the folder 
---
## Q2. Why Not Just SQL?

**Question:** Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is on vacation, and which projects would be affected?

### SQL Version
```sql
SELECT
    w.name                  AS backup_worker,
    w.role                  AS role,
    w.type                  AS employment_type,
    p.project_name          AS affected_project,
    p.project_number        AS project_number
FROM workers w
JOIN worker_can_cover wc
    ON w.worker_id = wc.worker_id
    AND wc.station_code = '016'
JOIN production p
    ON p.station_code = '016'
WHERE w.name <> 'Per Hansen'
  AND w.worker_id IN (
        SELECT DISTINCT worker_id
        FROM worker_certifications
        WHERE certification_code IN (
            SELECT certification_code
            FROM station_certifications
            WHERE station_code = '016'
        )
  )
GROUP BY w.name, w.role, w.type, p.project_name, p.project_number
ORDER BY w.name, p.project_name;
```
---
### Cypher Version

```cypher
MATCH (per:Worker {name: "Per Hansen"})-[:WORKS_AT]->(s:Station {station_code: "016"})
MATCH (backup:Worker)-[:CAN_COVER]->(s)
WHERE backup.name <> "Per Hansen"
MATCH (p:Project)-[:SCHEDULED_AT]->(s)
RETURN
    backup.name                         AS backup_worker,
    backup.role                         AS role,
    backup.type                         AS employment_type,
    collect(DISTINCT p.project_name)    AS affected_projects,
    count(DISTINCT p)                   AS project_count
ORDER BY backup.name
```
---
### What the Graph Makes Obvious That SQL Hides

When I checked the actual data, Station 016 (Gjutning) has only two workers who can cover it — Per Hansen (W07, primary) and Victor Elm (W11, Foreman). If Per Hansen is on vacation, Victor Elm is the only backup, even though he is already covering all 10 stations in the factory.

In SQL, finding this requires four tables and two nested subqueries. The relationship between "who covers a station" and "what projects run there" is hidden behind join keys. In Cypher, I just follow the path: find the station → find who covers it → find the projects scheduled there. It reads exactly like the question.

If the question changes to "what if Victor Elm is sick?" — which affects all 10 stations — I only need to change one node in Cypher. In SQL, the entire query needs to be rewritten.
---

## Q3. Spot the Bottleneck

### Weekly Capacity Deficits

After looking at `factory_capacity.csv`, I found that 5 out of 8 weeks have more work planned than hours available:

| Week | Capacity | Planned | Deficit  | Status  |
|------|--------- |---------|--------- |-------- |
| w1   | 480 hrs  | 612 hrs | −132 hrs | DEFICIT |
| w2   | 520 hrs  | 645 hrs | −125 hrs | DEFICIT |
| w3   | 480 hrs  | 398 hrs | +82 hrs  | OK      |
| w4   | 500 hrs  | 550 hrs | −50 hrs  | DEFICIT |
| w5   | 510 hrs  | 480 hrs | +30 hrs  | OK      |
| w6   | 440 hrs  | 520 hrs | −80 hrs  | DEFICIT |
| w7   | 520 hrs  | 600 hrs | −80 hrs  | DEFICIT |
| w8   | 500 hrs  | 470 hrs | +30 hrs  | OK      |

w1 and w2 are the worst. Even after adding 40 overtime hours in w2, demand still exceeds capacity by 125 hours. w6 is also risky because own staff drops to 9 people that week, bringing available hours down to 440.

---

### Which Stations and Projects Are Causing the Overload

By comparing `actual_hours` vs `planned_hours` in `factory_production.csv`, I found three stations consistently running over planned hours:

1. Station 018 — SB B/F-hall (4 overruns, worst overall)

2. Station 016 — Gjutning (3 overruns, highest single variance)

3. Station 015 — Montering IQP (3 overruns)


All three stations were overrunning at the same time in w1 and w2, which directly explains the −132 and −125 hour deficits those weeks. Station 016 also has a staffing risk on top of this — only Per Hansen and Victor Elm can cover it, making it a single point of failure as well.

---

### Cypher Query — Projects Over 10% Variance, Grouped by Station

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
  AND r.planned_hours > 0
WITH
    s.station_code                                          AS station_code,
    s.station_name                                          AS station_name,
    count(p)                                                AS overload_count,
    round(avg((r.actual_hours - r.planned_hours)
        / r.planned_hours * 100))                           AS avg_variance_pct,
    collect({
        project:      p.project_name,
        week:         r.week,
        planned:      r.planned_hours,
        actual:       r.actual_hours,
        variance_pct: round((r.actual_hours - r.planned_hours)
                      / r.planned_hours * 100)
    })                                                      AS overloaded_projects
RETURN station_code, station_name, overload_count,
       avg_variance_pct, overloaded_projects
ORDER BY avg_variance_pct DESC
```

---

### How I Would Model the Alert

I would use a dedicated `(:Bottleneck)` node rather than adding a property to the relationship. My reasons:

- A property on `SCHEDULED_AT` can only be found by scanning every relationship in the graph. A `(:Bottleneck)` node can be queried directly with `MATCH (b:Bottleneck {status: "ACTIVE"})`.
- One bottleneck node can link to multiple projects at once, so I can see all contributing projects in a single query.
- It has its own lifecycle — created when variance crosses 10%, updated as things change, marked RESOLVED when fixed.

```cypher
MERGE (b:Bottleneck {station_code: "016", week: "w2"})
SET   b.severity         = "HIGH",
      b.avg_variance_pct = 17.2,
      b.status           = "ACTIVE",
      b.detected_at      = datetime()

MERGE (b)-[:OVERLOADS]->(s:Station {station_code: "016"})
MERGE (p1:Project {project_id: "P03"})-[:CONTRIBUTES_TO]->(b)
MERGE (p2:Project {project_id: "P05"})-[:CONTRIBUTES_TO]->(b)
```
---

## Q4. Vector + Graph Hybrid

### What I Would Embed

I would create a combined text string from the most meaningful fields in each production row and embed that:

```python
embed_text = (
    f"{row['product_type']} | "
    f"qty:{row['quantity']} {row['unit']} | "
    f"station:{row['station_name']} | "
    f"etapp:{row['etapp']} | "
    f"bop:{row['bop']} | "
    f"planned:{row['planned_hours']}h"
)
```

I would not embed raw numbers alone — a float like `38.5` means nothing to an embedding model without context. Combined with fields like `"IQB | 1200 meters | Gjutning | ET2"`, it carries real meaning. I would also embed worker profiles (`role + certifications + primary_station`) for future skill-based matching.

---

### Hybrid Query — Similar Past Projects That Also Ran on Budget

```python
# Step 1 — Vector search (finds semantically similar projects)
query_text = (
    "450 meters IQB beams hospital extension Linköping "
    "tight timeline similar scope to previous hospital projects"
)
similar_project_ids = vector_index.query(embed(query_text), top_k=10)
# Returns e.g. ["P05", "P01", "P08"] ranked by cosine similarity

# Step 2 — Graph filter (keeps only projects with variance under 5%)
cypher = """
WITH $similar_ids AS candidates
UNWIND candidates AS pid
MATCH (p:Project {project_id: pid})-[r:SCHEDULED_AT]->(s:Station)
WITH
    p,
    collect(DISTINCT s.station_name)            AS stations_used,
    avg(abs(r.actual_hours - r.planned_hours)
        / r.planned_hours)                       AS avg_variance,
    sum(r.planned_hours)                         AS total_planned_hours
WHERE avg_variance < 0.05
MATCH (p)-[:PRODUCES]->(prod:Product)
RETURN
    p.project_name                               AS project,
    p.project_number                             AS number,
    stations_used,
    collect(DISTINCT prod.product_type)          AS products,
    round(avg_variance * 100, 2)                 AS variance_pct,
    total_planned_hours
ORDER BY avg_variance ASC
LIMIT 3
"""
results = session.run(cypher, similar_ids=similar_project_ids)
```
---

### Why This Is Better Than Filtering by Product Type

If I filter by `product_type = 'IQB'`, I get all IQB projects regardless of scale or risk. For example, Kontorshus Mölndal (P02) and Sjukhus Linköping ET2 (P05) are both IQB — but P05 has 1200 meters at 613 planned hours while P02 has just 167 planned hours. Same product type, completely different execution profile.

My hybrid approach first finds projects that are contextually similar to the new request, then keeps only the ones that ran on budget. The result is not just "similar projects" — it is "similar projects that were actually executed successfully", which is the only kind of reference useful for planning.

---

### Connection to Boardy

Boardy uses this exact same two-step pattern but for matching people instead of projects:

- **Vector layer:** embed person profiles (skills, goals, interests) → find people whose needs are close to your offer
- **Graph layer:** filter by community, team, and existing connections → make sure the match is also structurally real

Semantic similarity alone gives false positives. The graph layer is what makes the match meaningful.

---

## Q5. My L6 Blueprint

### Node Labels → CSV Mapping

| Node       | Properties | CSV Source | Count |

| `Project`  | `project_id`, `project_number`, `project_name` | factory_production.csv | 8 nodes
| `Product`  | `product_type`, `unit`, `quantity`, `unit_factor` | factory_production.csv | 7 nodes 
| `Station`  | `station_code`, `station_name` | factory_production.csv | 10 nodes 
| `Worker`   | `worker_id`, `name`, `role`, `hours_per_week`, `type` | factory_workers.csv | 14 nodes
| `Week`     | `week` | both CSVs | 8 nodes
| `Etapp`    | `etapp` | factory_production.csv | 2 (ET1, ET2) 
| `Capacity` | `own_staff_count`, `hired_staff_count`, `own_hours`, `hired_hours`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit` | factory_capacity.csv | 8 nodes 

Total nodes: 57 (minimum required: 50)

---

### Relationship Types → What Creates Them

| Relationship | Properties | Created From | Count |

| `(Project)-[:PRODUCES]->(Product)` | — | unique project + product pairs | 32 |
| `(Project)-[:SCHEDULED_AT]->(Station)` | `week`, `planned_hours`, `actual_hours`, `completed_units`, `bop` | every row in production CSV | 68 |
| `(Project)-[:RUNS_IN]->(Week)` | — | unique project + week pairs | 20 |
| `(Project)-[:IN_ETAPP]->(Etapp)` | — | unique project + etapp pairs | 8 |
| `(Product)-[:PROCESSED_AT]->(Station)` | — | unique product + station pairs | 16 |
| `(Worker)-[:WORKS_AT]->(Station)` | — | `primary_station` field | 13 |
| `(Worker)-[:CAN_COVER]->(Station)` | — | each value in `can_cover_stations` split by comma | 31 |
| `(Worker)-[:AVAILABLE_IN]->(Week)` | `hours_per_week` | every worker × every week | 112 |
| `(Week)-[:HAS_CAPACITY]->(Capacity)` | — | one row per week in capacity CSV | 8 |

Total relationships: 308 (minimum required: 100)
Relationship types: 9 (minimum required: 8)

---

### seed_graph.py — Key Rules

1. Create uniqueness constraints before loading any data
2. Always use `MERGE`, never `CREATE` — makes the script safe to run twice
3. Load all nodes first, then relationships — never create a relationship before both end nodes exist
4. Split `can_cover_stations` by comma before creating `CAN_COVER` relationships
5. Store `week`, `planned_hours`, `actual_hours`, `completed_units`, `bop` as properties on `SCHEDULED_AT` — the self-test variance query reads from these

---

### Dashboard — 4 Pages with Cypher Queries

**Page 1 — Project Overview**

Shows all 8 projects with total planned hours, total actual hours, variance %, and products involved. Variance color-coded: green under 5%, amber 5–10%, red above 10%.

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
RETURN
    p.project_id                                        AS id,
    p.project_name                                      AS project,
    p.project_number                                    AS number,
    sum(r.planned_hours)                                AS total_planned,
    sum(r.actual_hours)                                 AS total_actual,
    round((sum(r.actual_hours) - sum(r.planned_hours))
        / sum(r.planned_hours) * 100)                   AS variance_pct,
    collect(DISTINCT prod.product_type)                 AS products
ORDER BY variance_pct DESC
```

**Page 2 — Station Load**

Grouped Plotly bar chart — stations on x-axis, planned vs actual hours on y-axis, with a week dropdown to filter. Bars where actual > planned are shown in red.

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN
    s.station_code          AS station_code,
    s.station_name          AS station,
    r.week                  AS week,
    sum(r.planned_hours)    AS planned_hours,
    sum(r.actual_hours)     AS actual_hours
ORDER BY station_code, week
```

**Page 3 — Capacity Tracker**

Dual-line Plotly chart — total capacity vs total planned per week. The 5 deficit weeks (w1, w2, w4, w6, w7) are highlighted with a red background band and deficit number on each point.

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:Capacity)
RETURN
    w.week                  AS week,
    c.own_hours             AS own_hours,
    c.hired_hours           AS hired_hours,
    c.overtime_hours        AS overtime_hours,
    c.total_capacity        AS total_capacity,
    c.total_planned         AS total_planned,
    c.deficit               AS deficit
ORDER BY week
```

**Page 4 — Worker Coverage Matrix**

A heatmap table — rows are workers, columns are stations, each cell shows WORKS_AT, CAN_COVER, or empty. Stations with only one covering worker are flagged red as single points of failure. In this dataset, Station 016 is the highest-risk SPOF — only Per Hansen and Victor Elm cover it.

```cypher
MATCH (w:Worker)-[r:WORKS_AT|CAN_COVER]->(s:Station)
RETURN
    w.name                  AS worker,
    w.role                  AS role,
    s.station_code          AS station_code,
    s.station_name          AS station,
    type(r)                 AS coverage_type
ORDER BY w.name, s.station_code
```

SPOF detection query:

```cypher
MATCH (w:Worker)-[:WORKS_AT|CAN_COVER]->(s:Station)
WITH s, collect(DISTINCT w.name) AS workers, count(DISTINCT w) AS coverage
RETURN
    s.station_code          AS station_code,
    s.station_name          AS station,
    workers                 AS covering_workers,
    coverage                AS worker_count,
    CASE WHEN coverage = 1
         THEN " SINGLE POINT OF FAILURE"
         ELSE " OK" END   AS risk_status
ORDER BY coverage ASC
```

---

### Self-Test — Adapted Variance Query

The default self-test code uses `p.name` and `s.name` which do not exist in my schema. I will use this instead so Check 6 returns results correctly:

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN
    p.project_name          AS project,
    s.station_name          AS station,
    r.planned_hours         AS planned,
    r.actual_hours          AS actual
LIMIT 10
```

This returns results from Stations 018, 016, and 015 where actual hours exceed planned by more than 10% across multiple projects. 

--------------LEVEL 5 COMPLETED--------------