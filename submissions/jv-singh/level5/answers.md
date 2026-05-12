# Level 5 — Graph Thinking: Knowledge Graph Foundations

**Submission folder:** `submissions/jv-singh/level5/`
**Files:**

```text
submissions/jv-singh/level5/
├── answers.md
└── schema.md
```

## Dataset used

I used the three CSV files from `challenges/data/`:

1. `factory_production.csv` — project/product/station/week production facts.
2. `factory_workers.csv` — worker, station coverage, and certification data.
3. `factory_capacity.csv` — weekly total capacity and demand data.

Important data-quality note: the Level 5 prompt says `factory_workers.csv` has 13 workers, but the actual file contains 14 workers (`W01` to `W14`). I used the actual CSV as the source of truth. Another naming mismatch exists in Q2: the question mentions **Per Gustafsson**, but the actual Station `016` primary worker in the CSV is **Per Hansen**. I wrote the query using an absent-worker parameter so either name can be used, and I explain the assumption in Q2.

---

# Q1. Model It — Graph Schema Design

## A. Final Answer

The graph should model the factory as connected operational entities, not as isolated spreadsheet rows.

### Node labels

| Node label | Meaning | Key properties | Source columns |
|---|---|---|---|
| `Project` | A construction/customer project | `project_id`, `project_number`, `name` | `project_id`, `project_number`, `project_name` from `factory_production.csv` |
| `Product` | Product family being produced | `product_type`, `unit` | `product_type`, `unit` |
| `Station` | Factory production station | `station_code`, `name` | `station_code`, `station_name` |
| `Worker` | Factory employee or hired worker | `worker_id`, `name`, `role`, `type`, `hours_per_week` | `worker_id`, `name`, `role`, `type`, `hours_per_week` from `factory_workers.csv` |
| `Week` | Planning week | `week`, `sort_order` | `week` from production and capacity files |
| `Etapp` | Project phase/stage | `etapp_id` | `etapp` |
| `BOP` | Bill-of-process / process grouping | `bop_id` | `bop` |
| `Certification` | Skill or certificate held by a worker | `name` | parsed from `certifications` |
| `CapacityPlan` | Weekly capacity record | `capacity_id`, `own_hours`, `hired_hours`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit`, `is_deficit` | all columns in `factory_capacity.csv` |
| `BottleneckAlert` | Derived alert for overload or risk | `alert_id`, `severity`, `reason`, `planned_hours`, `actual_hours`, `variance_hours`, `variance_pct` | derived from production and capacity data |

This gives more than the required 6 node labels.

### Relationship types

| Relationship | Direction | Meaning | Key properties |
|---|---|---|---|
| `PRODUCES` | `(Project)-[:PRODUCES]->(Product)` | Project produces a product type | `quantity`, `unit`, `unit_factor` |
| `SCHEDULED_AT` | `(Project)-[:SCHEDULED_AT]->(Station)` | Project has work at a station in a week | `week`, `planned_hours`, `actual_hours`, `completed_units`, `variance_hours`, `variance_pct`, `is_over_10pct` |
| `HAS_WORK_IN` | `(Project)-[:HAS_WORK_IN]->(Week)` | Project has total work in a week | `planned_hours`, `actual_hours`, `station_count` |
| `HAS_ETAPP` | `(Project)-[:HAS_ETAPP]->(Etapp)` | Project belongs to or uses an etapp | `etapp` |
| `USES_BOP` | `(Project)-[:USES_BOP]->(BOP)` | Project uses a process grouping | `bop` |
| `REQUIRES_STATION` | `(Product)-[:REQUIRES_STATION]->(Station)` | Product type normally needs this station | `times_seen`, `total_planned_hours`, `total_actual_hours` |
| `PRIMARY_AT` | `(Worker)-[:PRIMARY_AT]->(Station)` | Worker’s main station | `role`, `hours_per_week` |
| `CAN_COVER` | `(Worker)-[:CAN_COVER]->(Station)` | Worker can cover this station | `is_primary`, `coverage_source`, `hours_per_week` |
| `HAS_CERTIFICATION` | `(Worker)-[:HAS_CERTIFICATION]->(Certification)` | Worker has this certification | `certification_name` |
| `HAS_CAPACITY` | `(Week)-[:HAS_CAPACITY]->(CapacityPlan)` | Week has capacity data | `total_capacity`, `total_planned`, `deficit` |
| `CAPACITY_PRESSURE_ON` | `(CapacityPlan)-[:CAPACITY_PRESSURE_ON]->(Station)` | A deficit week puts pressure on specific stations | `station_planned_hours`, `station_actual_hours`, `station_variance_hours`, `share_of_week_demand` |
| `FLAGS_PROJECT` | `(BottleneckAlert)-[:FLAGS_PROJECT]->(Project)` | Alert points to risky project | `reason` |
| `FLAGS_STATION` | `(BottleneckAlert)-[:FLAGS_STATION]->(Station)` | Alert points to risky station | `reason` |
| `FLAGS_WEEK` | `(BottleneckAlert)-[:FLAGS_WEEK]->(Week)` | Alert points to risky week | `reason` |

This gives more than the required 8 relationship types. Several relationships carry data, especially `SCHEDULED_AT`, `PRODUCES`, `HAS_CAPACITY`, and `CAPACITY_PRESSURE_ON`.

### Schema diagram

See `schema.md` in this folder. It contains the Mermaid schema diagram and relationship-property table.

## B. What I Did

1. I treated every row in `factory_production.csv` as a production fact: one project, one product, one station, one week, planned hours, actual hours, and completed units.
2. I separated repeated names into nodes: `Project`, `Product`, `Station`, `Week`, `Etapp`, and `BOP`.
3. I treated worker coverage as a graph problem: workers connect to stations through `PRIMARY_AT` and `CAN_COVER`.
4. I treated certifications as separate nodes because one worker can have many certifications and one certification can be shared by many workers.
5. I added `CapacityPlan` nodes so weekly capacity records are not hidden as flat rows.
6. I added derived `BottleneckAlert` nodes for operational monitoring.

## C. Why I Did It

A spreadsheet row is good for storage, but weak for asking connected questions. A graph is better because factory planning is mainly about relationships:

- Which project uses which station?
- Which worker can cover that station?
- Which week is overloaded?
- Which projects are driving the overload?
- Which stations have only one backup person?

I used relationships with properties because production facts are not just connections. They also have measurements like `planned_hours`, `actual_hours`, and `completed_units`.

## D. How It Works

Example production row:

```text
P01, Stålverket Borås, IQB, station 012, week w1, planned 32.0, actual 35.5
```

Becomes:

```cypher
(:Project {project_id: 'P01', name: 'Stålverket Borås'})
  -[:PRODUCES {quantity: 600, unit: 'meter', unit_factor: 1.77}]->
(:Product {product_type: 'IQB'})

(:Project {project_id: 'P01'})
  -[:SCHEDULED_AT {
      week: 'w1',
      planned_hours: 32.0,
      actual_hours: 35.5,
      variance_hours: 3.5,
      variance_pct: 0.109375,
      is_over_10pct: true
  }]->
(:Station {station_code: '012', name: 'Förmontering IQB'})
```

Example worker row:

```text
W07, Per Hansen, primary_station 016, can_cover_stations 016,017
```

Becomes:

```cypher
(:Worker {worker_id: 'W07', name: 'Per Hansen'})-[:PRIMARY_AT]->(:Station {station_code: '016'})
(:Worker {worker_id: 'W07'})-[:CAN_COVER]->(:Station {station_code: '016'})
(:Worker {worker_id: 'W07'})-[:CAN_COVER]->(:Station {station_code: '017'})
```

Now a query can jump from a project to a station to backup workers without manually joining many tables.

## E. What Still Remains / Assumptions

- I assume `station_code` uniquely identifies a station.
- I assume `product_type` uniquely identifies a product family.
- I assume `week` values like `w1`, `w2`, and `w3` can be sorted by the numeric part.
- I assume `BOP` means a process grouping or bill-of-process identifier.
- The schema can later be extended with real station-level capacity if the factory provides capacity per station, not just total weekly capacity.
- The schema can also support vector embeddings later by adding properties such as `embedding` or by using Neo4j vector indexes on project descriptions.

---

# Q2. Why Not Just SQL?

Question: **Which workers are certified to cover Station 016 (Gjutning) when Per Gustafsson is on vacation, and which projects would be affected?**

## A. Final Answer

### Assumption about the worker name

The question mentions **Per Gustafsson**, but the actual CSV has **Per Hansen** as the primary worker for Station `016` (`Gjutning`). To avoid hard-coding a possibly wrong name, both queries below use an absent-worker parameter:

```text
:absent_worker_name = 'Per Gustafsson'
```

For the actual CSV, I would run the same query with:

```text
:absent_worker_name = 'Per Hansen'
```

### Equivalent SQL query

Assumed SQL tables:

- `workers(worker_id, name, role, primary_station, hours_per_week, type)`
- `worker_station_coverage(worker_id, station_code)` — parsed from `can_cover_stations`
- `stations(station_code, station_name)`
- `worker_certifications(worker_id, certification)` — parsed from `certifications`
- `production(project_id, project_name, product_type, station_code, week, planned_hours, actual_hours)`

```sql
WITH affected_station AS (
    SELECT
        s.station_code,
        s.station_name
    FROM stations s
    WHERE s.station_code = '016'
),
backup_workers AS (
    SELECT
        w.worker_id,
        w.name,
        w.role,
        w.type,
        w.hours_per_week,
        STRING_AGG(wc.certification, ', ') AS certifications
    FROM workers w
    JOIN worker_station_coverage wsc
        ON w.worker_id = wsc.worker_id
    JOIN affected_station s
        ON s.station_code = wsc.station_code
    LEFT JOIN worker_certifications wc
        ON wc.worker_id = w.worker_id
    WHERE w.name <> :absent_worker_name
    GROUP BY
        w.worker_id,
        w.name,
        w.role,
        w.type,
        w.hours_per_week
),
affected_projects AS (
    SELECT DISTINCT
        p.project_id,
        p.project_name,
        p.product_type,
        p.week,
        p.planned_hours,
        p.actual_hours
    FROM production p
    JOIN affected_station s
        ON s.station_code = p.station_code
)
SELECT
    bw.worker_id,
    bw.name AS backup_worker,
    bw.role,
    bw.type,
    bw.hours_per_week,
    bw.certifications,
    ap.project_id,
    ap.project_name,
    ap.product_type,
    ap.week,
    ap.planned_hours,
    ap.actual_hours
FROM backup_workers bw
CROSS JOIN affected_projects ap
ORDER BY
    bw.name,
    ap.week,
    ap.project_id;
```

### Equivalent Cypher query

```cypher
:param absent_worker_name => 'Per Hansen';

MATCH (station:Station {station_code: '016'})
OPTIONAL MATCH (absent:Worker)-[:PRIMARY_AT|CAN_COVER]->(station)
WHERE absent.name = $absent_worker_name
MATCH (backup:Worker)-[:CAN_COVER]->(station)
WHERE backup.name <> $absent_worker_name
OPTIONAL MATCH (backup)-[:HAS_CERTIFICATION]->(cert:Certification)
MATCH (project:Project)-[work:SCHEDULED_AT]->(station)
RETURN
    station.station_code AS station_code,
    station.name AS station_name,
    $absent_worker_name AS absent_worker,
    backup.worker_id AS backup_worker_id,
    backup.name AS backup_worker_name,
    backup.role AS backup_worker_role,
    backup.type AS backup_worker_type,
    backup.hours_per_week AS backup_hours_per_week,
    collect(DISTINCT cert.name) AS backup_certifications,
    project.project_id AS affected_project_id,
    project.name AS affected_project_name,
    work.week AS affected_week,
    work.planned_hours AS planned_hours,
    work.actual_hours AS actual_hours
ORDER BY
    backup_worker_name,
    affected_week,
    affected_project_id;
```

### Expected result using the actual CSV

For Station `016` (`Gjutning`), the workers who can cover the station are:

1. **Per Hansen** — primary worker for Station `016`; certifications include `Casting` and `Formwork`.
2. **Victor Elm** — foreman who can cover many stations, including `016`; certifications include `Leadership`, `CE`, and `ISO 9001`.

If **Per Hansen** is absent, the only remaining listed cover for Station `016` is **Victor Elm**. This is a resilience risk because Station `016` has only one backup in the current data.

Affected projects at Station `016` are:

| Project | Product | Week | Planned hours | Actual hours | Comment |
|---|---:|---:|---:|---:|---|
| `P03` Lagerhall Jönköping | IQB | `w2` | 28.0 | 35.0 | 25.0% over plan |
| `P05` Sjukhus Linköping ET2 | IQB | `w2` | 35.0 | 40.0 | 14.3% over plan |
| `P07` Idrottshall Västerås | IQB | `w2` | 20.0 | 22.0 | 10.0% over plan; not greater than 10%, exactly 10% |
| `P08` Bro E6 Halmstad | IQB | `w3` | 22.0 | 25.0 | 13.6% over plan |

## B. What I Did

1. I identified Station `016` as `Gjutning`.
2. I checked which workers have `016` in `can_cover_stations`.
3. I excluded the absent worker.
4. I connected the remaining backup workers to all projects scheduled at Station `016`.
5. I included certifications so the answer is not only “who can cover”, but also “why they are qualified”.

## C. Why I Did It

The question is not just asking for a list of workers. It is asking for operational impact:

- Who can replace the absent worker?
- Are they certified?
- Which projects depend on the affected station?
- Is this a single-point-of-failure risk?

The graph query expresses this naturally because all of these are relationships.

## D. How It Works

In SQL, the logic must be reconstructed using joins between workers, station coverage, certifications, stations, and production rows. That is correct, but it is verbose.

In Cypher, the logic follows the real-world chain:

```text
Backup Worker → can cover → Station 016 ← scheduled at ← Project
```

That path is exactly the business question.

The graph version makes the dependency visible:

```cypher
(backup:Worker)-[:CAN_COVER]->(station:Station)<-[work:SCHEDULED_AT]-(project:Project)
```

This tells us both the available replacement worker and the affected projects in one pattern.

## E. What Still Remains / Assumptions

- The CSV does not contain a worker named `Per Gustafsson`; I assume the intended absent worker is the Station `016` primary worker, `Per Hansen`.
- The CSV lists certifications as text; it does not say which exact certification is mandatory for each station. I assume a worker listed in `can_cover_stations` is operationally allowed to cover that station.
- If real factory rules are stricter, we should add `(:Station)-[:REQUIRES_CERTIFICATION]->(:Certification)` and filter backup workers by required certification.

### Why graph is better here

The graph version is better because the question is path-based. It moves from absent worker to station, from station to backup workers, and from station to affected projects. In SQL, the same question requires multiple joins and parsed many-to-many tables. In a graph, the same relationships are first-class data, so the impact chain is easier to read, validate, and extend.

---

# Q3. Spot the Bottleneck

## A. Final Answer

### Capacity-level finding

The capacity file shows weekly total factory capacity versus total planned demand.

| Week | Total capacity | Total planned | Deficit | Capacity status |
|---|---:|---:|---:|---|
| `w1` | 480 | 612 | -132 | Overloaded |
| `w2` | 520 | 645 | -125 | Overloaded |
| `w3` | 480 | 398 | 82 | Enough capacity |
| `w4` | 500 | 550 | -50 | Overloaded |
| `w5` | 510 | 480 | 30 | Enough capacity |
| `w6` | 440 | 520 | -80 | Overloaded |
| `w7` | 520 | 600 | -80 | Overloaded |
| `w8` | 500 | 470 | 30 | Enough capacity |

So the overloaded weeks are:

```text
w1, w2, w4, w6, w7
```

However, `factory_production.csv` only contains detailed station/project rows for `w1`, `w2`, and `w3`. Therefore, I can attribute station/project causes for `w1` and `w2`, but not for `w4`, `w6`, and `w7` without more production rows.

### Station-level bottlenecks from production data

Aggregating all available production rows by station:

| Rank | Station | Planned hours | Actual hours | Variance hours | Variance % | Rows >10% over plan | Bottleneck interpretation |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `012` Förmontering IQB | 324.0 | 345.0 | +21.0 | +6.5% | 2 | Largest total extra hours |
| 2 | `016` Gjutning | 105.0 | 122.0 | +17.0 | +16.2% | 3 | Worst percentage overrun and weak coverage |
| 3 | `014` Svets o montage IQB | 235.0 | 247.2 | +12.2 | +5.2% | 1 | Moderate overrun |
| 4 | `015` Montering IQP | 172.0 | 184.0 | +12.0 | +7.0% | 3 | Several jobs over 10% |
| 5 | `018` SB B/F-hall | 149.0 | 158.5 | +9.5 | +6.4% | 4 | Many small overruns |

### Most important bottleneck: Station 016 (`Gjutning`)

Station `016` is the most serious operational bottleneck even though it is not the largest by total hours.

Reasons:

1. It is **16.2% above planned hours overall**.
2. 3 of its 4 production rows are greater than 10% over plan.
3. It appears in overloaded week `w2`.
4. Worker coverage is thin: only **Per Hansen** and **Victor Elm** can cover it.
5. If Per Hansen is unavailable, only Victor Elm remains, and Victor is also listed as a cross-station foreman who covers many other stations.

### Project/station rows greater than 10% over plan

The exact rows where:

```text
actual_hours > 1.1 × planned_hours
```

are:

| Project | Station | Week | Planned | Actual | Variance | Variance % |
|---|---|---:|---:|---:|---:|---:|
| `P01` Stålverket Borås | `012` Förmontering IQB | `w1` | 32.0 | 35.5 | +3.5 | +10.9% |
| `P02` Kontorshus Mölndal | `012` Förmontering IQB | `w1` | 22.0 | 24.5 | +2.5 | +11.4% |
| `P03` Lagerhall Jönköping | `014` Svets o montage IQB | `w1` | 42.0 | 48.0 | +6.0 | +14.3% |
| `P02` Kontorshus Mölndal | `015` Montering IQP | `w1` | 19.0 | 21.0 | +2.0 | +10.5% |
| `P04` Parkering Helsingborg | `015` Montering IQP | `w1` | 16.0 | 18.0 | +2.0 | +12.5% |
| `P01` Stålverket Borås | `015` Montering IQP | `w2` | 25.0 | 28.0 | +3.0 | +12.0% |
| `P03` Lagerhall Jönköping | `016` Gjutning | `w2` | 28.0 | 35.0 | +7.0 | +25.0% |
| `P05` Sjukhus Linköping ET2 | `016` Gjutning | `w2` | 35.0 | 40.0 | +5.0 | +14.3% |
| `P08` Bro E6 Halmstad | `016` Gjutning | `w3` | 22.0 | 25.0 | +3.0 | +13.6% |
| `P04` Parkering Helsingborg | `018` SB B/F-hall | `w1` | 19.0 | 22.0 | +3.0 | +15.8% |
| `P05` Sjukhus Linköping ET2 | `018` SB B/F-hall | `w1` | 25.0 | 28.0 | +3.0 | +12.0% |
| `P07` Idrottshall Västerås | `018` SB B/F-hall | `w1` | 16.0 | 18.0 | +2.0 | +12.5% |
| `P06` Skola Uppsala | `018` SB B/F-hall | `w2` | 16.0 | 18.0 | +2.0 | +12.5% |
| `P02` Kontorshus Mölndal | `019` SP B/F-hall | `w2` | 14.0 | 15.5 | +1.5 | +10.7% |

### Project-level contributors

By total extra hours across available production rows:

| Rank | Project | Planned | Actual | Variance | Variance % | Rows >10% |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `P03` Lagerhall Jönköping | 392.0 | 406.5 | +14.5 | +3.7% | 2 |
| 2 | `P04` Parkering Helsingborg | 228.0 | 238.0 | +10.0 | +4.4% | 2 |
| 3 | `P08` Bro E6 Halmstad | 407.0 | 415.0 | +8.0 | +2.0% | 1 |
| 4 | `P05` Sjukhus Linköping ET2 | 613.0 | 619.5 | +6.5 | +1.1% | 2 |
| 5 | `P01` Stålverket Borås | 316.0 | 322.4 | +6.4 | +2.0% | 2 |

### Cypher query: actual_hours > 1.1 × planned_hours, grouped by station

```cypher
MATCH (p:Project)-[work:SCHEDULED_AT]->(s:Station)
WHERE work.actual_hours > work.planned_hours * 1.10
RETURN
    s.station_code AS station_code,
    s.name AS station_name,
    count(*) AS overrun_rows,
    collect(DISTINCT p.project_id + ' ' + p.name) AS affected_projects,
    round(sum(work.planned_hours), 2) AS planned_hours,
    round(sum(work.actual_hours), 2) AS actual_hours,
    round(sum(work.actual_hours - work.planned_hours), 2) AS variance_hours,
    round(
        100.0 * (sum(work.actual_hours) - sum(work.planned_hours)) / sum(work.planned_hours),
        2
    ) AS variance_pct
ORDER BY
    overrun_rows DESC,
    variance_hours DESC;
```

### Graph pattern for bottleneck alerts

I would model bottlenecks as explicit alert nodes:

```text
(:BottleneckAlert)
  -[:FLAGS_PROJECT]->(:Project)
  -[:FLAGS_STATION]->(:Station)
  -[:FLAGS_WEEK]->(:Week)
```

Example alert node:

```cypher
(:BottleneckAlert {
    alert_id: 'P03-016-w2-overrun',
    severity: 'high',
    reason: 'actual_hours > planned_hours by more than 10%',
    planned_hours: 28.0,
    actual_hours: 35.0,
    variance_hours: 7.0,
    variance_pct: 25.0
})
```

For capacity deficits, I would also create alerts like:

```text
(:BottleneckAlert {alert_id: 'capacity-w2', reason: 'weekly capacity deficit'})
  -[:FLAGS_WEEK]->(:Week {week: 'w2'})
```

Then connect that alert to the stations with the largest station-week variance or largest share of week demand.

## B. What I Did

1. I first looked at weekly total capacity versus total planned demand.
2. I identified deficit weeks: `w1`, `w2`, `w4`, `w6`, and `w7`.
3. I then checked production rows where actual hours exceeded planned hours by more than 10%.
4. I aggregated production by station to find which stations had the biggest total overruns.
5. I also checked worker coverage to see whether the station bottleneck is made worse by limited staffing.
6. I separated two concepts:
   - **capacity deficit** = the whole factory does not have enough hours in that week.
   - **execution overrun** = specific station/project rows used more hours than planned.

## C. Why I Did It

A real factory bottleneck is not just the biggest number. It is a combination of:

1. demand pressure,
2. actual time overruns,
3. weak worker coverage,
4. timing during already overloaded weeks.

That is why Station `016` is more alarming than Station `012` even though Station `012` has more total extra hours. Station `016` has a higher percentage overrun and only two listed workers who can cover it.

## D. How It Works

The basic overrun rule is:

```text
actual_hours > planned_hours × 1.10
```

Example:

```text
P03 at Station 016 in week w2:
planned = 28.0
actual = 35.0
threshold = 28.0 × 1.10 = 30.8
35.0 > 30.8, so this is a bottleneck row.
```

The capacity rule is:

```text
deficit < 0 means the week is overloaded.
```

Example:

```text
w2 total capacity = 520
w2 total planned = 645
deficit = -125
```

So week `w2` is overloaded. In the detailed production data, week `w2` also contains major Station `016` overruns, so Station `016` is a strong candidate bottleneck.

## E. What Still Remains / Assumptions

- The production CSV only has rows for `w1`, `w2`, and `w3`, while capacity exists for `w1` through `w8`. I cannot accurately assign station/project causes for deficits in `w4`, `w6`, and `w7` without detailed production rows for those weeks.
- The capacity file is total weekly factory capacity, not station-specific capacity. If station-level capacity is later provided, the bottleneck model should compare station demand against station capacity directly.
- The worker file says who can cover each station, but it does not say availability by week. If vacation/absence calendars are added, the graph can detect week-specific staffing bottlenecks.

---

# Q4. Vector + Graph Hybrid

## A. Final Answer

The factory receives new free-text requests such as:

```text
450 meters of IQB beams for a hospital extension in Linköping, similar scope to previous hospital projects, tight timeline
```

A good system should not only search by product type. It should find past projects that are semantically similar and operationally similar.

### What I would embed

I would create an embedding text for every historical project using fields like:

```text
Project name: Sjukhus Linköping ET2.
Products: IQB, SB, SR.
Quantity: 450 meters.
Stations used: FS IQB, Förmontering IQB, Montering IQB, Gjutning, SB B/F-hall, SR B/F-hall.
Weeks: w1, w2, w3.
Performance: planned hours, actual hours, variance percentage.
Context tags: hospital, Linköping, extension, tight timeline if available.
```

I would embed:

1. project descriptions,
2. product/product-spec summaries,
3. station route summaries,
4. lessons-learned or variance summaries,
5. worker skill/certification summaries if the future use case includes staffing.

### How similarity search works

1. Convert the new project request into an embedding vector.
2. Compare that vector against stored project vectors.
3. Return the top similar historical projects.
4. Then apply graph filters to keep only the projects that are operationally relevant.

### Hybrid vector + graph query

Example in Neo4j-style Cypher:

```cypher
// Step 1: vector search gives semantically similar projects
CALL db.index.vector.queryNodes('project_embedding_index', 10, $new_project_embedding)
YIELD node AS similarProject, score

// Step 2: graph filter keeps projects that use the same product/station pattern
MATCH (similarProject)-[:PRODUCES]->(product:Product {product_type: $product_type})
MATCH (similarProject)-[work:SCHEDULED_AT]->(station:Station)
WHERE station.station_code IN $required_station_codes

WITH
    similarProject,
    score,
    collect(DISTINCT station.name) AS matched_stations,
    sum(work.planned_hours) AS planned_hours,
    sum(work.actual_hours) AS actual_hours
WHERE planned_hours > 0
  AND abs(actual_hours - planned_hours) / planned_hours < 0.05

RETURN
    similarProject.project_id AS project_id,
    similarProject.name AS project_name,
    score AS semantic_similarity,
    matched_stations,
    planned_hours,
    actual_hours,
    round(100.0 * (actual_hours - planned_hours) / planned_hours, 2) AS variance_pct
ORDER BY
    semantic_similarity DESC,
    abs(actual_hours - planned_hours) ASC
LIMIT 5;
```

### Why this is better than filtering only by product type

Filtering only by product type may find projects that are all `IQB`, but not all `IQB` projects are operationally similar. A hospital extension with a tight timeline may behave differently from a bridge, a parking structure, or a warehouse.

The hybrid method is better because it checks:

1. semantic similarity — the request sounds like a past project,
2. product similarity — it uses similar products,
3. station-route similarity — it used the same factory stations,
4. performance similarity — it finished with low variance,
5. staffing/certification similarity — optional future filter.

## B. What I Did

1. I separated “meaning similarity” from “factory execution similarity”.
2. I used vectors for free text because text like “hospital extension in Linköping” is not easy to match with exact filters.
3. I used graph relationships for hard operational rules such as product type, station route, and variance.
4. I filtered for projects with variance under 5% because these are good planning references.

## C. Why I Did It

Vector search is good at fuzzy similarity. Graph search is good at exact connected constraints. Factory planning needs both.

A vector search alone might return a project that sounds similar but used very different stations. A graph query alone might return the same product type but miss that the customer context and timeline are similar. Together, they produce recommendations that are both meaningful and operationally useful.

## D. How It Works

The new project request becomes a numeric vector. Historical projects also have vectors. The system first finds projects with close vectors.

Then the graph asks:

```text
Did those similar projects use the required stations?
Did they use the same product type?
Was the variance less than 5%?
```

Only projects that pass both the vector similarity and graph constraints are recommended.

Example result:

```text
New request: hospital extension, IQB beams, tight timeline
Recommended reference: P05 Sjukhus Linköping ET2
Reason: semantically similar hospital project, used IQB-related stations, and gives real station-hour history.
```

## E. What Still Remains / Assumptions

- The current CSV does not include rich project descriptions, customer type, deadline pressure, or location fields except what can be inferred from project names.
- To make vector search truly strong, future data should include descriptions, project category, location, complexity, constraints, and post-project notes.
- Neo4j vector indexing requires embeddings to be generated and stored first.
- The query assumes the application can provide `$new_project_embedding`, `$product_type`, and `$required_station_codes`.

---

# Q5. Level 6 Plan — Build Blueprint

## A. Final Answer

Level 6 should build the Level 5 schema into a Neo4j graph and then use Streamlit to query Neo4j for dashboard pages.

## 1. Node labels and CSV column mapping

| Node label | Created from | CSV columns |
|---|---|---|
| `Project` | unique project rows from production | `project_id`, `project_number`, `project_name` |
| `Product` | unique product types from production | `product_type`, `unit` |
| `Station` | unique station rows from production | `station_code`, `station_name` |
| `Week` | unique weeks from production and capacity | `week` |
| `Etapp` | unique etapp values from production | `etapp` |
| `BOP` | unique bop values from production | `bop` |
| `Worker` | each worker row | `worker_id`, `name`, `role`, `primary_station`, `hours_per_week`, `type` |
| `Certification` | parsed certification names | `certifications` split by comma |
| `CapacityPlan` | each weekly capacity row | `week`, `own_staff_count`, `hired_staff_count`, `own_hours`, `hired_hours`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit` |
| `BottleneckAlert` | derived from overrun/capacity rules | derived IDs and metrics |

## 2. Relationships and how they are created

| Relationship | Creation rule |
|---|---|
| `(Project)-[:PRODUCES]->(Product)` | from each production row, merge by project and product |
| `(Project)-[:SCHEDULED_AT]->(Station)` | from each production row; relationship carries week and hour metrics |
| `(Project)-[:HAS_WORK_IN]->(Week)` | aggregate project-week planned and actual hours |
| `(Project)-[:HAS_ETAPP]->(Etapp)` | from production `etapp` |
| `(Project)-[:USES_BOP]->(BOP)` | from production `bop` |
| `(Product)-[:REQUIRES_STATION]->(Station)` | aggregate all product/station combinations from production |
| `(Worker)-[:PRIMARY_AT]->(Station)` | from worker `primary_station`, except `all` should be handled as foreman/global coverage |
| `(Worker)-[:CAN_COVER]->(Station)` | split `can_cover_stations` by comma and connect worker to each station |
| `(Worker)-[:HAS_CERTIFICATION]->(Certification)` | split `certifications` by comma |
| `(Week)-[:HAS_CAPACITY]->(CapacityPlan)` | from each capacity row |
| `(CapacityPlan)-[:CAPACITY_PRESSURE_ON]->(Station)` | derived by joining week-level capacity with station-week production demand |
| `(BottleneckAlert)-[:FLAGS_PROJECT]->(Project)` | created for rows over 10% plan or for risky project/station/week combinations |
| `(BottleneckAlert)-[:FLAGS_STATION]->(Station)` | created for overloaded station |
| `(BottleneckAlert)-[:FLAGS_WEEK]->(Week)` | created for overloaded week |

## 3. Data ingestion plan

### Step 1: Create constraints

```cypher
CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (p:Project) REQUIRE p.project_id IS UNIQUE;

CREATE CONSTRAINT product_type IF NOT EXISTS
FOR (p:Product) REQUIRE p.product_type IS UNIQUE;

CREATE CONSTRAINT station_code IF NOT EXISTS
FOR (s:Station) REQUIRE s.station_code IS UNIQUE;

CREATE CONSTRAINT worker_id IF NOT EXISTS
FOR (w:Worker) REQUIRE w.worker_id IS UNIQUE;

CREATE CONSTRAINT week_id IF NOT EXISTS
FOR (w:Week) REQUIRE w.week IS UNIQUE;

CREATE CONSTRAINT certification_name IF NOT EXISTS
FOR (c:Certification) REQUIRE c.name IS UNIQUE;
```

### Step 2: Load production CSV

For each row:

1. `MERGE` project.
2. `MERGE` product.
3. `MERGE` station.
4. `MERGE` week.
5. `MERGE` etapp.
6. `MERGE` BOP.
7. Create/update relationships using `MERGE`.
8. Store `planned_hours`, `actual_hours`, `completed_units`, and variance metrics on `SCHEDULED_AT`.

### Step 3: Load workers CSV

For each worker:

1. `MERGE` worker.
2. `MERGE` primary station if not `all`.
3. Create `PRIMARY_AT`.
4. Split `can_cover_stations` and create `CAN_COVER` relationships.
5. Split `certifications` and create `HAS_CERTIFICATION` relationships.

### Step 4: Load capacity CSV

For each week:

1. `MERGE` week.
2. `MERGE` capacity plan using ID like `capacity-w1`.
3. Create `HAS_CAPACITY` relationship.
4. Set `is_deficit = true` when `deficit < 0`.

### Step 5: Create derived alerts

Create `BottleneckAlert` nodes for:

1. production rows where `actual_hours > planned_hours * 1.10`,
2. weeks where `deficit < 0`,
3. stations with only one or two covering workers and high demand.

Use `MERGE`, not `CREATE`, so the script can run more than once safely.

## 4. Dashboard panels for Level 6

### Panel 1: Project Overview

**What it shows:**

- all 8 projects,
- total planned hours,
- total actual hours,
- variance hours,
- variance percentage,
- products involved,
- stations involved.

**Cypher query:**

```cypher
MATCH (p:Project)-[work:SCHEDULED_AT]->(s:Station)
OPTIONAL MATCH (p)-[:PRODUCES]->(prod:Product)
WITH
    p,
    collect(DISTINCT prod.product_type) AS products,
    collect(DISTINCT s.name) AS stations,
    sum(work.planned_hours) AS planned_hours,
    sum(work.actual_hours) AS actual_hours
RETURN
    p.project_id AS project_id,
    p.project_number AS project_number,
    p.name AS project_name,
    products,
    stations,
    round(planned_hours, 2) AS planned_hours,
    round(actual_hours, 2) AS actual_hours,
    round(actual_hours - planned_hours, 2) AS variance_hours,
    round(100.0 * (actual_hours - planned_hours) / planned_hours, 2) AS variance_pct
ORDER BY project_id;
```

### Panel 2: Station Load and Overrun Chart

**What it shows:**

- planned vs actual hours by station,
- station variance,
- stations where actual hours are higher than planned,
- highlight `016`, `012`, `015`, and `018` if overruns remain visible.

**Cypher query:**

```cypher
MATCH (p:Project)-[work:SCHEDULED_AT]->(s:Station)
WITH
    s,
    sum(work.planned_hours) AS planned_hours,
    sum(work.actual_hours) AS actual_hours,
    count(CASE WHEN work.actual_hours > work.planned_hours * 1.10 THEN 1 END) AS over_10pct_rows
RETURN
    s.station_code AS station_code,
    s.name AS station_name,
    round(planned_hours, 2) AS planned_hours,
    round(actual_hours, 2) AS actual_hours,
    round(actual_hours - planned_hours, 2) AS variance_hours,
    round(100.0 * (actual_hours - planned_hours) / planned_hours, 2) AS variance_pct,
    over_10pct_rows
ORDER BY variance_hours DESC;
```

### Panel 3: Capacity Tracker

**What it shows:**

- weekly total capacity,
- weekly total planned demand,
- deficit/surplus,
- red flag for deficit weeks.

**Cypher query:**

```cypher
MATCH (w:Week)-[:HAS_CAPACITY]->(c:CapacityPlan)
RETURN
    w.week AS week,
    c.own_hours AS own_hours,
    c.hired_hours AS hired_hours,
    c.overtime_hours AS overtime_hours,
    c.total_capacity AS total_capacity,
    c.total_planned AS total_planned,
    c.deficit AS deficit,
    c.is_deficit AS is_deficit
ORDER BY toInteger(replace(w.week, 'w', ''));
```

### Panel 4: Worker Coverage Matrix

**What it shows:**

- station rows,
- workers who can cover each station,
- number of certified/covering workers,
- single-point-of-failure stations.

**Cypher query:**

```cypher
MATCH (s:Station)
OPTIONAL MATCH (worker:Worker)-[:CAN_COVER]->(s)
WITH
    s,
    collect(DISTINCT worker.name) AS covering_workers,
    count(DISTINCT worker) AS coverage_count
RETURN
    s.station_code AS station_code,
    s.name AS station_name,
    coverage_count,
    covering_workers,
    CASE
        WHEN coverage_count <= 1 THEN 'HIGH RISK'
        WHEN coverage_count = 2 THEN 'MEDIUM RISK'
        ELSE 'OK'
    END AS coverage_risk
ORDER BY coverage_count ASC, station_code;
```

### Panel 5: Bottleneck Alerts

**What it shows:**

- every project/station/week row where actual hours are more than 10% above planned,
- severity,
- linked project,
- linked station,
- linked week.

**Cypher query:**

```cypher
MATCH (p:Project)-[work:SCHEDULED_AT]->(s:Station)
WHERE work.actual_hours > work.planned_hours * 1.10
RETURN
    p.project_id AS project_id,
    p.name AS project_name,
    s.station_code AS station_code,
    s.name AS station_name,
    work.week AS week,
    work.planned_hours AS planned_hours,
    work.actual_hours AS actual_hours,
    round(work.actual_hours - work.planned_hours, 2) AS variance_hours,
    round(100.0 * (work.actual_hours - work.planned_hours) / work.planned_hours, 2) AS variance_pct,
    CASE
        WHEN work.actual_hours > work.planned_hours * 1.25 THEN 'HIGH'
        WHEN work.actual_hours > work.planned_hours * 1.10 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS severity
ORDER BY variance_pct DESC;
```

## B. What I Did

1. I reused the schema from Q1 instead of inventing a new model.
2. I mapped every CSV column to either a node property, a relationship property, or a derived metric.
3. I designed ingestion to be idempotent with `MERGE`.
4. I planned dashboard panels around the scoring requirements: project overview, station load, capacity tracker, and worker coverage.
5. I added a fifth panel for bottleneck alerts because it directly supports factory decision-making.

## C. Why I Did It

Level 6 should prove that the graph is useful, not just that data was loaded. The dashboard should answer practical questions:

- Which projects are over plan?
- Which stations are overloaded?
- Which weeks have capacity deficits?
- Which stations have weak worker coverage?
- Where should a production manager act first?

This is why each panel is powered by a Cypher query instead of reading directly from CSV.

## D. How It Works

The ingestion script builds the graph once. Then the dashboard connects to Neo4j and runs Cypher queries.

The flow is:

```text
CSV files → seed_graph.py → Neo4j graph → Streamlit app → dashboard panels
```

Example:

1. `seed_graph.py` creates `Project`, `Station`, and `SCHEDULED_AT` relationships.
2. The Station Load panel runs a Cypher query that sums `planned_hours` and `actual_hours` per station.
3. Streamlit displays the result as a bar chart.
4. A production manager can immediately see which station is using more time than expected.

## E. What Still Remains / Assumptions

- Level 6 still needs actual implementation in Python.
- Neo4j Aura or local Neo4j credentials must be created and stored safely in `.env` or Streamlit secrets.
- Streamlit deployment must be completed separately.
- The production data currently has detailed rows only for `w1`, `w2`, and `w3`, so capacity dashboard will show all weeks, but station-level attribution is only possible where production rows exist.
- The dashboard should not read raw CSV files after seeding; it should query Neo4j.

---

# Final Section

## ✔ Summary of what is COMPLETED

- Completed the Level 5 graph schema design with more than 6 node labels and more than 8 relationship types.
- Created a separate `schema.md` containing a Mermaid schema diagram and relationship-property mapping.
- Mapped the CSV data into graph nodes, relationships, and properties.
- Wrote equivalent SQL and Cypher queries for the Station `016` worker-coverage question.
- Explained why the graph query is clearer and more natural than SQL for connected factory questions.
- Analyzed bottlenecks using capacity deficits, planned vs actual hours, station overruns, project overruns, and worker coverage risk.
- Identified Station `016` (`Gjutning`) as the highest-risk bottleneck because it combines high percentage overrun with weak worker coverage.
- Designed a practical vector + graph hybrid approach for matching new project requests to similar historical projects.
- Produced a detailed Level 6 blueprint including node labels, relationships, CSV mapping, ingestion plan, and dashboard Cypher queries.

## ❗ What is STILL REMAINING for Level 6 or improvements

- Implement `seed_graph.py`.
- Implement `app.py` in Streamlit.
- Create a Neo4j Aura or local Neo4j database.
- Load the graph using the three CSV files.
- Add the required Self-Test page.
- Deploy the Streamlit app.
- Add `DASHBOARD_URL.txt` with the deployed app URL.
- Add real station-level capacity if available.
- Add worker availability/vacation calendars if available.
- Add richer project descriptions for better vector search.

## 🧠 Key insights I should remember

1. A graph is useful because factory planning is relationship-heavy.
2. The most important bottleneck is not always the biggest total-hours station.
3. Station `012` has the largest total extra hours, but Station `016` is riskier because it has high percentage overruns and limited worker coverage.
4. Capacity deficit and production overrun are related but not identical.
5. The current data can explain `w1` and `w2` station/project causes, but not `w4`, `w6`, and `w7` because detailed production rows are missing for those weeks.
6. Level 5 Q5 should be treated as the implementation blueprint for Level 6.
7. In Level 6, the dashboard must query Neo4j, not read directly from CSV.
