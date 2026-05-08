# Level 5 — Graph Thinking
**Deadline:** Tuesday May 13, 2026 23:59 UTC

---

## Q1. Model It

**Schema diagram:** see `schema.md` (Mermaid)

### Node Labels (7)

| Label | Key Properties | Source CSV |
|---|---|---|
| `Project` | project_id, project_number, project_name | factory_production.csv |
| `Product` | product_type, unit, quantity, unit_factor | factory_production.csv |
| `Station` | station_code, station_name | factory_production.csv + factory_workers.csv |
| `Worker` | worker_id, name, role, hours_per_week, type | factory_workers.csv |
| `Certification` | cert_name | factory_workers.csv (split from comma-separated column) |
| `Week` | week_id, total_capacity, total_planned, deficit | factory_capacity.csv |
| `Alert` | id, type, severity, variance_pct, resolved | Computed on load |

### Relationship Types (9)

| Relationship | From → To | Properties | Carries Data? |
|---|---|---|---|
| `INCLUDES` | Project → Product | etapp, bop | — |
| `PROCESSED_AT` | Product → Station | **planned_hours, actual_hours, completed_units, week** | ✅ |
| `ACTIVE_IN` | Project → Week | — | — |
| `SCHEDULED_IN` | Product → Week | — | — |
| `ASSIGNED_TO` | Worker → Station | — | — |
| `CAN_COVER` | Worker → Station | — | — |
| `HAS_CERTIFICATION` | Worker → Certification | — | — |
| `QUALIFIES_FOR` | Certification → Station | — | — |
| `TRIGGERED_AT` | Alert → Station | **variance_pct, week** | ✅ |

### Design Notes

The `PROCESSED_AT` relationship carries the production telemetry directly — each row in `factory_production.csv` becomes one edge with `planned_hours`, `actual_hours`, `completed_units`, and `week` as properties. This avoids a separate "WorkOrder" node and keeps traversal paths short.

`Certification` is modelled as its own node (not a property array on `Worker`) because the key query is always "which workers qualify for *this station*" — that's a two-hop traversal `Worker→Certification→Station`, not a string-scan. The CSVs store certifications as comma-separated strings; the loader splits them on ingest.

`Alert` is included as a computed node so overrun conditions become first-class graph entities you can query, assign, and resolve — rather than conditions you recalculate on every read.

---

## Q2. Why Not Just SQL?

**Question:** Which workers are certified to cover Station 016 (Gjutning) when Per Hansen is on vacation, and which projects would be affected?

> Note: The assignment refers to "Per Gustafsson" — the actual dataset has **Per Hansen (W07)** as the Station 016 primary worker (certifications: Casting, Formwork). Answer uses the real data.

---

### SQL Version

```sql
-- Assumes normalised tables: workers, worker_coverage(worker_id, station_code),
-- productions(project_id, station_code), projects(project_id, project_name)

SELECT
    w.name                   AS covering_worker,
    w.role,
    p.project_name           AS affected_project
FROM workers w
INNER JOIN worker_coverage wc
    ON w.worker_id  = wc.worker_id
   AND wc.station_code = '016'
INNER JOIN productions pr
    ON pr.station_code = '016'
INNER JOIN projects p
    ON p.project_id = pr.project_id
WHERE w.name <> 'Per Hansen'
GROUP BY w.name, w.role, p.project_name
ORDER BY w.name, p.project_name;
```

---

### Cypher Version

```cypher
MATCH (w:Worker)-[:CAN_COVER|ASSIGNED_TO]->(s:Station {station_code: "016"})
WHERE w.name <> "Per Hansen"
WITH w, s
MATCH (prod:Product)-[:PROCESSED_AT]->(s)
MATCH (proj:Project)-[:INCLUDES]->(prod)
RETURN
  w.name                              AS covering_worker,
  w.role                              AS role,
  collect(DISTINCT proj.project_name) AS affected_projects
ORDER BY w.name
```

**Result from the actual data:**
- **Victor Elm** (Foreman, W11) is the only backup — he covers all stations.
- Affected projects if Per Hansen is absent: **P03 Lagerhall Jönköping**, **P05 Sjukhus Linköping**, **P07 Idrottshall Västerås**, **P08 Bro E6 Halmstad**

---

### What the graph makes obvious that SQL hides

The Cypher traversal surfaces the answer as a readable path — Worker → Station → Product → Project — with no JOIN boilerplate. But the more important thing is what the graph reveals structurally: **Station 016 has exactly one backup in the entire factory, and that backup is the Foreman**. In SQL you get the same rows back, but the single-point-of-failure risk is invisible unless you manually count results. In a graph you can see it — one node, one outgoing edge, four affected projects hanging off it. The SQL gives you data; the graph gives you the risk pattern.

---

## Q3. Spot the Bottleneck

### Capacity Deficits from factory_capacity.csv

Five of eight weeks are in deficit:

| Week | Capacity | Planned | Deficit |
|------|----------|---------|---------|
| w1 | 480 hrs | 612 hrs | **-132** |
| w2 | 520 hrs | 645 hrs | **-125** |
| w3 | 480 hrs | 398 hrs | +82 |
| w4 | 500 hrs | 550 hrs | **-50** |
| w5 | 510 hrs | 480 hrs | +30 |
| w6 | 440 hrs | 520 hrs | **-80** |
| w7 | 520 hrs | 600 hrs | **-80** |
| w8 | 500 hrs | 470 hrs | +30 |

w1 and w2 are the crisis weeks — 132 and 125 hours over capacity respectively. The factory only added 40 hours overtime in w2 and none in w1. That gap doesn't disappear; it compresses into later weeks or gets absorbed as quality risk.

---

### Projects/Stations Causing the Overload (actual > planned by >10%)

Calculated directly from `factory_production.csv`:

| Station | Station Name | Project | Week | Planned | Actual | Variance |
|---|---|---|---|---|---|---|
| **016** | **Gjutning** | P03 Lagerhall Jönköping | w2 | 28h | 35h | **+25.0%** |
| 018 | SB B/F-hall | P04 Parkering Helsingborg | w1 | 19h | 22h | +15.8% |
| 014 | Svets o montage | P03 Lagerhall Jönköping | w1 | 42h | 48h | +14.3% |
| **016** | **Gjutning** | P05 Sjukhus Linköping | w2 | 35h | 40h | **+14.3%** |
| **016** | **Gjutning** | P08 Bro E6 Halmstad | w3 | 22h | 25h | **+13.6%** |
| 018 | SB B/F-hall | P06 Skola Uppsala | w2 | 16h | 18h | +12.5% |
| 018 | SB B/F-hall | P07 Idrottshall Västerås | w1 | 16h | 18h | +12.5% |
| 015 | Montering IQP | P04 Parkering Helsingborg | w1 | 16h | 18h | +12.5% |
| 015 | Montering IQP | P01 Stålverket Borås | w2 | 25h | 28h | +12.0% |
| 018 | SB B/F-hall | P05 Sjukhus Linköping | w1 | 25h | 28h | +12.0% |
| 012 | Förmontering IQB | P02 Kontorshus Mölndal | w1 | 22h | 24.5h | +11.4% |
| 012 | Förmontering IQB | P01 Stålverket Borås | w1 | 32h | 35.5h | +10.9% |

**Root cause:** Station 016 (Gjutning) appears 3 times and has the worst single overrun (+25%). Station 018 (SB B/F-hall) appears 4 times — more frequent but lower severity per instance. These two stations account for most of the w1/w2 capacity crisis. Critically, the overruns occur across *multiple projects simultaneously* — this is not one rogue job. It's a systematic underestimation of Gjutning and SB hours in the planning model.

---

### Cypher Query — Overruns >10% Grouped by Station

```cypher
MATCH (proj:Project)-[:INCLUDES]->(prod:Product)-[r:PROCESSED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.10
WITH
  s.station_code  AS station_code,
  s.station_name  AS station_name,
  count(*)        AS overrun_count,
  sum(r.actual_hours - r.planned_hours) AS total_excess_hours,
  collect({
    project:      proj.project_name,
    week:         r.week,
    planned:      r.planned_hours,
    actual:       r.actual_hours,
    variance_pct: round((r.actual_hours - r.planned_hours) / r.planned_hours * 100)
  }) AS overrun_records
RETURN station_code, station_name, overrun_count, total_excess_hours, overrun_records
ORDER BY total_excess_hours DESC
```

---

### Modelling the Alert as a Graph Pattern

An `(:Alert)` node is the right choice — not a property on a relationship, not a flag on Station. If the alert is just `r.overrun: true` on a `PROCESSED_AT` edge, you can check it but you can't query across alerts, assign them, or resolve them. A node makes alerts first-class:

```cypher
MERGE (a:Alert {id: "ALERT-016-P03-w2"})
SET   a.type         = "capacity_overrun",
      a.severity     = "HIGH",
      a.variance_pct = 25.0,
      a.resolved     = false,
      a.created_at   = datetime()
MERGE (a)-[:TRIGGERED_AT]->(s:Station  {station_code: "016"})
MERGE (a)-[:TRIGGERED_IN]->(w:Week     {week_id: "w2"})
MERGE (a)-[:AFFECTS]      ->(p:Project {project_id: "P03"})
```

Now "show me all unresolved HIGH alerts affecting active projects" is a three-hop traversal, not a computed scan. The alert node also has a natural place to add `assigned_to`, `resolved_at`, and `notes` as the system matures into a real production tool.

---

## Q4. Vector + Graph Hybrid

### What to Embed

**Primary — project description strings:** composite text from `project_name + product_type + quantity + unit + etapp + sector`. Example for P05: *"Sjukhus Linköping ET2 — IQB beams 1200m, hospital, stage 2, BOP3, multi-station"*. This captures scope, sector, and scale in a form the embedding model understands.

**Secondary — station sequence fingerprint:** the ordered list of station codes a project uses, encoded as a string: `"011→012→013→014→015→016→017"`. Two projects can share a product type but have completely different production workflows; this fingerprint captures operational topology.

Worker skills embeddings are better suited to the Boardy people-matching use case than project similarity.

---

### Hybrid Query

```cypher
// Phase 1 — Vector search (Neo4j 5 vector index)
CALL db.index.vector.queryNodes(
  'project_embeddings',
  10,
  $query_embedding
) YIELD node AS candidate, score
WHERE score > 0.75

// Phase 2 — Graph filter: must use overlapping stations AND avg variance < 5%
WITH candidate
MATCH (candidate)-[:INCLUDES]->(prod:Product)-[:PROCESSED_AT]->(s:Station)
WHERE s.station_code IN $required_stations

WITH candidate, collect(DISTINCT s.station_code) AS matched_stations
MATCH (candidate)-[:INCLUDES]->(p2:Product)-[r:PROCESSED_AT]->(:Station)
WITH candidate, matched_stations,
     avg(abs(r.actual_hours - r.planned_hours) / r.planned_hours * 100) AS avg_variance
WHERE avg_variance < 5.0

RETURN
  candidate.project_name AS similar_project,
  matched_stations,
  round(avg_variance, 1)  AS avg_variance_pct
ORDER BY avg_variance ASC
LIMIT 5
```

---

### Why Better Than Filtering by Product Type

`product_type = 'IQB'` is a one-bit signal. It tells you the beam profile but nothing about scope, timeline, station count, or delivery risk. In this dataset, P02 (350m, 5 production rows, office building) and P05 (1200m, 11 rows, hospital with SR special structures) both use IQB — but they are completely unlike each other operationally.

The vector captures *what the project actually is* in human terms. The graph layer validates *whether similar projects were executed reliably*. Together they answer the real question: **"Have we done something like this before, and did we deliver it?"** That's what a project manager actually needs before committing to a new bid.

The Boardy parallel is exact: embed person profile descriptions instead of project strings; filter by graph community membership instead of station codes; filter by `shared_connections > 2` instead of `avg_variance < 5%`. Same two-phase pattern, different domain.

---

## Q5. L6 Blueprint

### Node Labels → CSV Column Mapping

| Node | Properties | Maps from |
|---|---|---|
| `Project` | project_id, project_number, project_name | `factory_production.csv` — MERGE on project_id |
| `Product` | product_type, unit, quantity, unit_factor | `factory_production.csv` — MERGE on (project_id, product_type, etapp, bop) |
| `Station` | station_code (zero-padded), station_name | `factory_production.csv` station_code + station_name |
| `Worker` | worker_id, name, role, hours_per_week, type | `factory_workers.csv` — one node per row |
| `Certification` | cert_name | `factory_workers.csv` certifications column — split on `","`, MERGE to deduplicate |
| `Week` | week_id, total_capacity, total_planned, deficit, overtime_hours | `factory_capacity.csv` — one node per row |
| `Alert` | id, type, severity, variance_pct, resolved | Computed post-load: any PROCESSED_AT edge where actual > planned × 1.10 |

### Relationship Types → What Creates Them

| Relationship | Created from |
|---|---|
| `(Project)-[:INCLUDES {etapp, bop}]->(Product)` | Unique (project_id, product_type, etapp, bop) groups in factory_production.csv |
| `(Product)-[:PROCESSED_AT {planned_hours, actual_hours, completed_units, week}]->(Station)` | One per row in factory_production.csv |
| `(Project)-[:ACTIVE_IN]->(Week)` | Unique (project_id, week) pairs in factory_production.csv |
| `(Worker)-[:ASSIGNED_TO]->(Station)` | `primary_station` column in factory_workers.csv |
| `(Worker)-[:CAN_COVER]->(Station)` | `can_cover_stations` column, split on comma |
| `(Worker)-[:HAS_CERTIFICATION]->(Certification)` | `certifications` column, split on comma |
| `(Certification)-[:QUALIFIES_FOR]->(Station)` | One-time mapping: Casting/Formwork → 016, MIG/MAG → 011/014, etc. |
| `(Alert)-[:TRIGGERED_AT]->(Station)` | Post-load Cypher: detect overrun PROCESSED_AT edges |
| `(Alert)-[:AFFECTS]->(Project)` | Same post-load script |

---

### 3 Streamlit Dashboard Panels

#### Panel 1 — Station Load Heatmap

**What it shows:** Grid of stations (rows) × weeks (columns). Cell colour = utilisation % — green below 90%, amber 90–110%, red above 110%. Instantly shows w1/w2 are systemically red and Station 016 is the chronic hotspot.

**Cypher:**
```cypher
MATCH (s:Station)<-[r:PROCESSED_AT]-(prod:Product)
WITH s.station_code AS station, r.week AS week,
     sum(r.planned_hours) AS total_planned,
     sum(r.actual_hours)  AS total_actual
RETURN station, week, total_planned, total_actual,
       round(total_actual / total_planned * 100) AS utilisation_pct
ORDER BY station, week
```

**Streamlit:** pivot result into a DataFrame, render with `plotly.express.imshow` or pandas Styler with background gradient.

---

#### Panel 2 — Project Variance Tracker

**What it shows:** Horizontal bar chart — one bar per project/station/week combo, sorted by variance%. Red threshold line at 10%. Sidebar filters for week and station. Answers "which jobs are running hot this week?"

**Cypher:**
```cypher
MATCH (proj:Project)-[:INCLUDES]->(prod:Product)-[r:PROCESSED_AT]->(s:Station)
RETURN
  proj.project_name AS project,
  s.station_name    AS station,
  r.week            AS week,
  r.planned_hours,
  r.actual_hours,
  round((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1) AS variance_pct
ORDER BY variance_pct DESC
```

**Streamlit:** `st.selectbox` for week/station filters; `plotly.express.bar` coloured by variance_pct.

---

#### Panel 3 — Worker Coverage Matrix

**What it shows:** Table of stations (rows) × workers (columns). Cell = 🟢 Primary / 🟡 Can Cover / ⬜ None. A "Mark as absent" multiselect simulates vacation — stations lose coverage and turn red, the rightmost column shows affected projects and remaining backups. Directly exposes the Per Hansen / Station 016 single-point-of-failure.

**Cypher (base matrix):**
```cypher
MATCH (w:Worker)-[rel:ASSIGNED_TO|CAN_COVER]->(s:Station)
RETURN w.worker_id, w.name, s.station_code, type(rel) AS coverage_type
```

**Cypher (absence impact):**
```cypher
MATCH (absent:Worker {worker_id: $absent_id})-[:ASSIGNED_TO]->(s:Station)
MATCH (proj:Project)-[:INCLUDES]->(:Product)-[:PROCESSED_AT]->(s)
OPTIONAL MATCH (backup:Worker)-[:CAN_COVER]->(s)
WHERE backup.worker_id <> $absent_id
RETURN s.station_name,
       collect(DISTINCT proj.project_name) AS at_risk_projects,
       collect(DISTINCT backup.name)       AS available_backups
```

**Streamlit:** `st.multiselect` for absence selector; `st.dataframe` with pandas Styler cell colouring.

---

### Loading Strategy (Python for L6)

```python
from neo4j import GraphDatabase
import pandas as pd

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

prod    = pd.read_csv("factory_production.csv")
workers = pd.read_csv("factory_workers.csv")
cap     = pd.read_csv("factory_capacity.csv")

# Load order: Stations → Projects → Products → Weeks → Workers → Certs → Relationships → Alerts

with driver.session() as session:
    for _, row in prod.iterrows():
        session.run("""
            MERGE (proj:Project {project_id: $pid})
              SET proj.project_name = $pname
            MERGE (s:Station {station_code: $sc})
              SET s.station_name = $sname
            MERGE (w:Week {week_id: $wk})
            MERGE (prod:Product {product_type: $pt, project_id: $pid})
            MERGE (prod)-[r:PROCESSED_AT {week: $wk}]->(s)
              SET r.planned_hours   = $ph,
                  r.actual_hours    = $ah,
                  r.completed_units = $cu
        """, pid=row.project_id, pname=row.project_name,
             sc=str(row.station_code).zfill(3), sname=row.station_name,
             wk=row.week, pt=row.product_type,
             ph=row.planned_hours, ah=row.actual_hours, cu=row.completed_units)

    # Post-load: generate Alert nodes for any overrun > 10%
    session.run("""
        MATCH (proj:Project)-[:INCLUDES]->(prod:Product)-[r:PROCESSED_AT]->(s:Station)
        WHERE r.actual_hours > r.planned_hours * 1.10
        MERGE (a:Alert {id: proj.project_id + '-' + s.station_code + '-' + r.week})
        SET a.type         = 'overrun',
            a.severity     = CASE WHEN r.actual_hours > r.planned_hours * 1.20
                                  THEN 'HIGH' ELSE 'MEDIUM' END,
            a.variance_pct = round((r.actual_hours - r.planned_hours)
                                    / r.planned_hours * 100),
            a.resolved     = false
        MERGE (a)-[:TRIGGERED_AT]->(s)
        MERGE (a)-[:AFFECTS]->(proj)
    """)
```

---

*All answers based directly on the real dataset: 68 production rows across 8 projects, 9 stations, 14 workers, 8 capacity weeks.*
