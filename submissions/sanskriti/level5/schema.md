# Factory Knowledge Graph Schema

## Graph Structure

```
                        ┌─────────────────────────────────────────┐
                        │                                           │
                     (Week)◄──────────[HAS_CAPACITY]───────────────┤
                    w1-w8  │                                         │
                        │  │ [USES_WEEK]                    [HAS]   │
                        │  │                                         │
                    ┌───┴──▼──────────────┐                   ┌──────┴─────┐
                    │                    │                   │            │
                 (Etapp)           (Project)◄──────[PART_OF]─(Capacity)  │
                 ET1,ET2             P01-P08                           │
                    │                    │                                │
            ┌───────┼───┐        ┌───────┼────────┐                      │
            │       │   │        │       │        │                      │
         [PART_OF]  │   │     [PRODUCES][FOLLOWS_BOP][SCHEDULED_AT]      │
            │       │   │        │       │        │                      │
         ┌──▼───┐   │   │   (Product)  (BOP)  (Station)─────────────────┘
         │(Worker)  │   │   IQB,IQP     BOP1    011-021
         │W01-W14   │   │   SB,SD,SR    BOP2
         └──┬─────┘ │   │   SP,HSQ      BOP3
            │       │   │        │               │
    ┌───────┼───────┼───┼────────┼───────────────┼────────┐
    │       │       │   │        │               │        │
[WORKS_AT][CAN_COVER]│   │   [PRODUCED_IN]  [IN_STATION] │
    │       │       │   │        │               │        │
    │       │       ▼   ▼        │               ▼        │
    │       │                    │                        │
    │       │             (Node Relationships)            │
    │       │                                              │
    └──────────────────────────────────────────────────────┘
```

## Node Labels

| Label | Purpose | Sample Data | Count |
|-------|---------|-------------|-------|
| **Project** | Construction projects | P01: "Stålverket Borås", P05: "Sjukhus Linköping" | 8 |
| **Product** | Product types | IQB (beams), IQP, SB, SD, SP, SR, HSQ | 7 |
| **Station** | Production stations | 011: "FS IQB", 016: "Gjutning", 017: "Målning" | 9 |
| **Worker** | Factory employees | W01: Erik Lindberg, W07: Per Hansen | 13 |
| **Week** | Planning weeks | w1, w2, ..., w8 | 8 |
| **Etapp** | Project phases | ET1 (phase 1), ET2 (phase 2) | 2 |
| **BOP** | Bill of processes | BOP1, BOP2, BOP3 | 3 |
| **Capacity** | Capacity aggregate | GLOBAL (single node for all weeks) | 1 |

## Relationship Types

### 1. PRODUCES
- **From:** Project → **To:** Product
- **Properties:** `quantity`, `unit_factor`
- **Example:** P01 -[:PRODUCES {quantity: 600, unit_factor: 1.77}]-> IQB
- **Meaning:** What products does this project produce?

### 2. SCHEDULED_AT
- **From:** Project → **To:** Station
- **Properties:** `week`, `planned_hours`, `actual_hours`, `completed_units`
- **Example:** P01 -[:SCHEDULED_AT {week: "w1", planned_hours: 48.0, actual_hours: 45.2, completed_units: 28}]-> Station 011
- **Meaning:** When/where/how much work is scheduled?

### 3. PART_OF
- **From:** Project → **To:** Etapp
- **Properties:** None
- **Example:** P01 -[:PART_OF]-> ET1
- **Meaning:** Which phase/etapp is project in?

### 4. FOLLOWS_BOP
- **From:** Project → **To:** BOP
- **Properties:** None
- **Example:** P01 -[:FOLLOWS_BOP]-> BOP1
- **Meaning:** Which bill-of-process does project follow?

### 5. WORKS_AT
- **From:** Worker → **To:** Station
- **Properties:** None
- **Example:** W01 (Erik) -[:WORKS_AT]-> Station 011
- **Meaning:** Primary work station for this worker

### 6. CAN_COVER
- **From:** Worker → **To:** Station
- **Properties:** `certifications`
- **Example:** W01 -[:CAN_COVER {certifications: "MIG/MAG,TIG"}]-> Station 012
- **Meaning:** Which stations can this worker cover? (with certifications)

### 7. IN_STATION
- **From:** Station → **To:** BOP
- **Properties:** None
- **Example:** Station 011 -[:IN_STATION]-> BOP1
- **Meaning:** Which BOP process does this station belong to?

### 8. HAS_CAPACITY
- **From:** Week → **To:** Capacity
- **Properties:** `own_staff`, `hired_staff`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit`
- **Example:** w1 -[:HAS_CAPACITY {own_staff: 10, hired_staff: 2, overtime: 0, total: 480, planned: 612, deficit: -132}]-> Capacity
- **Meaning:** Weekly capacity snapshot

### 9. USES_WEEK
- **From:** Project → **To:** Week
- **Properties:** None
- **Example:** P01 -[:USES_WEEK]-> w1
- **Meaning:** Which weeks is this project active?

## Critical Queries

### Find Coverage for Missing Worker
```cypher
MATCH (worker:Worker)-[:CAN_COVER]->(station:Station {code: "016"})
WHERE worker.name <> "Per Hansen"
RETURN worker.name, worker.certifications
ORDER BY worker.name
```

### Bottleneck Detection (> 10% variance)
```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN s.code AS station, r.week AS week,
       ROUND((r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1) AS variance_pct
ORDER BY variance_pct DESC
```

### Capacity vs Demand
```cypher
MATCH (w:Week)-[c:HAS_CAPACITY]->(cap:Capacity)
WHERE c.deficit < 0
RETURN w.week, c.total_capacity, c.total_planned, c.deficit
ORDER BY c.deficit DESC
```

### Single Point of Failure
```cypher
MATCH (w:Worker)-[:CAN_COVER]->(s:Station)
WITH s, count(distinct w) AS worker_count
WHERE worker_count = 1
MATCH (w:Worker)-[:CAN_COVER]->(s)
RETURN s.code, s.name, collect(w.name) AS sole_worker, worker_count
ORDER BY s.code
```

### Project Overview
```cypher
MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
RETURN p.name,
       sum(r.planned_hours) AS total_planned,
       sum(r.actual_hours) AS total_actual,
       ROUND((sum(r.actual_hours) - sum(r.planned_hours)) / sum(r.planned_hours) * 100, 1) AS variance_pct,
       count(distinct s) AS station_count
GROUP BY p.name
ORDER BY variance_pct DESC
```

## Data Flow

```
CSV Files
    ↓
factory_production.csv (68 rows)
├── Projects, Products, Stations, Etapps, BOPs
├── PRODUCES relationships
└── SCHEDULED_AT relationships (main data)

factory_workers.csv (13 rows)
├── Workers
├── WORKS_AT relationships
└── CAN_COVER relationships

factory_capacity.csv (8 rows)
├── Weeks
└── HAS_CAPACITY relationships
    ↓
seed_graph.py (loads all)
    ↓
Neo4j Database
    ↓
app.py (Streamlit dashboard)
├── Page 1: Project Overview
├── Page 2: Station Load
├── Page 3: Capacity Tracker
├── Page 4: Worker Coverage
└── Page 5: Self-Test
    ↓
Deployed Dashboard URL
```

## Statistics

| Metric | Count |
|--------|-------|
| **Node Labels** | 8 |
| **Relationship Types** | 9 |
| **Projects** | 8 |
| **Products** | 7 |
| **Stations** | 9 |
| **Workers** | 13 |
| **Weeks** | 8 |
| **Etapps** | 2 |
| **BOPs** | 3 |
| **Total Nodes** | 60+ |
| **Total Relationships** | 150+ |

## Idempotent Seed Strategy

All node and relationship creation uses `MERGE` instead of `CREATE`:

```cypher
// ✅ Safe to run twice
MERGE (p:Project {id: "P01"})
SET p.name = "Stålverket Borås"

// ❌ Dangerous - creates duplicates
CREATE (p:Project {id: "P01"})
SET p.name = "Stålverket Borås"
```

This ensures `seed_graph.py` can be run multiple times without duplicating data.

## Constraints

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.type IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week) REQUIRE wk.week IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp) REQUIRE e.id IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (b:BOP) REQUIRE b.id IS UNIQUE
```

---

See [answers.md](answers.md) for Q1-Q5 full details.
