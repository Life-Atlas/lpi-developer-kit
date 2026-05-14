# Level 5 — Graph Thinking
**Submission:** Adil Islam (@adil-islam) — Track A

---

## Q1. Model It

Schema diagram: see `schema.md` (Mermaid format)

**Summary:**

7 node labels: `Project`, `Product`, `Station`, `Worker`, `Week`, `Etapp`, `Certification`

8 relationship types:

| Relationship | Carries Data |
|-------------|-------------|
| `(Project)-[:PRODUCES {qty, unit_factor}]->(Product)` | ✅ qty (metres/units), unit_factor (conversion to hours) |
| `(Project)-[:SCHEDULED_AT {week, planned_hours, actual_hours}]->(Station)` | ✅ planned vs actual hours per week (one rel per CSV row) |
| `(Project)-[:BELONGS_TO]->(Etapp)` | — |
| `(Project)-[:ACTIVE_IN]->(Week)` | — |
| `(Worker)-[:WORKS_AT]->(Station)` | — |
| `(Worker)-[:CAN_COVER]->(Station)` | — |
| `(Worker)-[:HAS_CERTIFICATION]->(Certification)` | — |
| `(Station)-[:REQUIRES_CERT]->(Certification)` | — |

**Key design decision:** `SCHEDULED_AT` carries `week`, `planned_hours`, and `actual_hours` as relationship properties — one relationship per (project, station, week) triple, matching the 68 CSV rows exactly. This makes variance queries trivially simple: just filter on `WHERE r.actual_hours > r.planned_hours * 1.1`.

---

## Q2. Why Not Just SQL?

**The question:** Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is on vacation, and which projects would be affected?

> **Data note:** Per Hansen (W07, Operator) is the primary worker at Station 016 (Gjutning), certified in Casting and Formwork. His only backup is Victor Elm (W11, Foreman — covers all 10 stations), making 016 a single-point-of-failure station in the real data.

### SQL Version

```sql
SELECT
    w.name               AS backup_worker,
    w.role,
    w.certifications,
    STRING_AGG(DISTINCT p.project_name, ', ') AS affected_projects
FROM workers w
JOIN worker_coverage wc
    ON w.worker_id = wc.worker_id
    AND wc.station_code = '016'
WHERE w.name <> 'Per Hansen'
LEFT JOIN production p
    ON p.station_code = '016'
GROUP BY w.name, w.role, w.certifications
ORDER BY w.name;
```

This requires 3 tables (workers, worker_coverage, production), a multi-table join, and a GROUP BY —
and still doesn't naturally expose downstream risk (which etapp or product delivery is at risk).

### Cypher Version

```cypher
// Who can cover Station 016 when Per Hansen is out?
MATCH (backup:Worker)-[:CAN_COVER]->(s:Station {code: '016'})
WHERE backup.name <> 'Per Hansen'
OPTIONAL MATCH (p:Project)-[:SCHEDULED_AT]->(s)
RETURN backup.name               AS backup_worker,
       backup.role               AS role,
       collect(DISTINCT p.name)  AS affected_projects
ORDER BY backup.name
```

### What the graph version makes obvious

The Cypher query reads as the actual business question: follow `CAN_COVER` edges to Station 016, exclude the absent worker, then traverse `SCHEDULED_AT` edges in reverse to find every project that lands there.

SQL hides two things graphs reveal instantly:
1. **Reachability** — which stations a worker *can* reach is a traversal, not a join condition
2. **Impact propagation** — one Cypher path connects absence → station → projects → delivery risk. In SQL that takes 2–3 separate queries and application-level stitching

The graph schema makes the "coverage gap" pattern a first-class concept, not a query engineering problem.

---

## Q3. Spot the Bottleneck

### Which projects/stations are causing overload

From `factory_capacity.csv`, weeks with the worst deficits are:

| Week | Total Capacity | Total Planned | Deficit |
|------|--------------|--------------|---------|
| w1   | 480 hrs      | 612 hrs      | **-132** |
| w2   | 520 hrs      | 645 hrs      | **-125** |
| w4   | 500 hrs      | 550 hrs      | -50     |
| w6   | 440 hrs      | 520 hrs      | -80     |
| w7   | 520 hrs      | 600 hrs      | -80     |

The pattern: IQB-heavy stations (011–014) simultaneously overrun in the same weeks — structural overload, not isolated slips.

### Cypher Query — Projects with actual > planned by 10%+

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN
    s.name                                                    AS station,
    s.code                                                    AS station_code,
    p.name                                                    AS project,
    r.week                                                    AS week,
    r.planned_hours                                           AS planned_hrs,
    r.actual_hours                                            AS actual_hrs,
    round((r.actual_hours / r.planned_hours - 1.0) * 100, 1) AS variance_pct
ORDER BY variance_pct DESC
```

To rank worst stations aggregated across all projects and weeks:

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
WITH s, count(*) AS overrun_count,
     sum(r.actual_hours - r.planned_hours) AS total_excess_hrs
RETURN s.name AS station, overrun_count, total_excess_hrs
ORDER BY total_excess_hrs DESC
```

### How to model the alert as a graph pattern

Flag overruns as a relationship property — set during seeding, not as a separate node:

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
SET r.is_overrun   = true,
    r.variance_pct = round((r.actual_hours / r.planned_hours - 1.0) * 100, 1)
```

Dashboard query then becomes:

```cypher
MATCH (p:Project)-[r:SCHEDULED_AT {is_overrun: true}]->(s:Station)
RETURN p.name, s.name, r.variance_pct ORDER BY r.variance_pct DESC
```

**Why not a Bottleneck node?** A node makes sense if bottlenecks are named, persistent entities tracked over time. For historical analysis over 8 weeks, a relationship property is cleaner — no extra label, directly queryable.

---

## Q4. Vector + Graph Hybrid

### What to embed

**Project descriptions** — a composite string from: project name + product type(s) + scope (qty × unit_factor) + timeline. Example:

> "Stålverket Borås produces 600m IQB steel beams at Stations 011–014 over 8 weeks with ET1 deadline pressure"

This captures semantic fingerprint of scope + pressure. Worker skill embeddings are a secondary target (useful for Boardy-style people matching, not project similarity).

### Hybrid Query

```cypher
// Step 1 [Vector]: top-5 similar past projects by embedding cosine similarity
CALL db.index.vector.queryNodes('project_embeddings', 5, $query_embedding)
YIELD node AS similar_project, score

// Step 2 [Graph]: filter — same stations AND variance < 5%
MATCH (similar_project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours <= r.planned_hours * 1.05
WITH similar_project, collect(s.name) AS stations, avg(score) AS similarity

MATCH (new_proj:Project)-[:SCHEDULED_AT]->(s2:Station)
WHERE new_proj.name = $new_project_name
  AND s2.name IN stations

RETURN similar_project.name AS similar_project,
       stations              AS shared_stations,
       similarity            AS vector_score
ORDER BY similarity DESC
LIMIT 3
```

### Why this beats filtering by product type

`product_type = 'IQB'` tells you *what* was built — not how hard it was or whether the team delivered on time. The vector captures full context (scope pressure, station mix, timeline) while the graph filter (`variance < 5%`) removes projects that looked similar but went off the rails.

Together they answer: "find a past project genuinely comparable AND that actually ran well." Product type alone can't distinguish a smooth 6-week IQB run from a chaotic one.

This is the exact Boardy pattern — "find people with similar goals [vector] who are in complementary graph positions [graph]."

---

## Q5. L6 Blueprint

### Node → CSV Column Mapping

| Node | CSV | Key Columns |
|------|-----|-------------|
| `Project` | factory_production.csv | `project_id`, `project_name` |
| `Product` | factory_production.csv | `product_type` |
| `Station` | factory_production.csv | `station_code`, `station_name` |
| `Etapp` | factory_production.csv | `etapp` |
| `Week` | factory_capacity.csv | `week`, `own_hours`, `hired_hours`, `overtime_hours`, `total_planned`, `deficit` |
| `Worker` | factory_workers.csv | `worker_id`, `name`, `role`, `type` |
| `Certification` | factory_workers.csv | `certifications` (comma-separated, split per cert) |

### Relationship → CSV Logic

| Relationship | Created From |
|-------------|-------------|
| `PRODUCES {qty, unit_factor}` | production.csv → distinct (project, product_type) pairs |
| `SCHEDULED_AT {week, planned_hours, actual_hours, is_overrun, variance_pct}` | One rel per row of production.csv |
| `BELONGS_TO` | production.csv → `etapp` column |
| `ACTIVE_IN` | Distinct (project_id, week) pairs from production.csv |
| `WORKS_AT` | workers.csv → `primary_station` column |
| `CAN_COVER` | workers.csv → `can_cover_stations` (split on comma, create one rel per station) |
| `HAS_CERTIFICATION` | workers.csv → `certifications` (split on comma, one rel per cert) |
| `REQUIRES_CERT` | Derived from station → worker certification pairings |

> **Special case:** Worker W11 (Victor Elm) has `primary_station = "all"` — handled by skipping WORKS_AT creation and using the explicit `can_cover_stations` list.

### Streamlit Dashboard Panels (5)

**Panel 1 — Project Overview** (10 pts)
- Cypher: Aggregate `sum(planned_hours)`, `sum(actual_hours)` per project across all stations and weeks
- Viz: Table + grouped bar chart (planned vs actual per project)

**Panel 2 — Station Load** (10 pts)
- Cypher: Hours per station per week (planned + actual)
- Viz: Plotly heatmap (station × week), cells where actual > planned outlined red

**Panel 3 — Capacity Tracker** (10 pts)
- Cypher: All Week nodes with `own_hours`, `hired_hours`, `overtime_hours`, `total_planned`, `deficit`
- Viz: Stacked bar (own + hired + overtime) vs demand line; deficit weeks red

**Panel 4 — Worker Coverage** (10 pts)
- Cypher: Worker → CAN_COVER → Station traversal
- Viz: Boolean matrix; SPOF stations (only 1 covering worker) flagged red

**Panel 5 — Self-Test** (20 pts)
- Runs all 6 automated checks against live Neo4j
- Green/red checklist with point totals
