# Factory Knowledge Graph — Schema

```mermaid
graph LR
    %% ── Node definitions ──
    Project["🏗️ <b>Project</b><br/>project_id · project_number<br/>project_name"]
    Product["📦 <b>Product</b><br/>product_type · unit"]
    Station["🏭 <b>Station</b><br/>station_code · station_name"]
    Worker["👷 <b>Worker</b><br/>worker_id · name<br/>role · hours_per_week · type"]
    Week["📅 <b>Week</b><br/>week_id"]
    Factory["🏭 <b>Factory</b><br/>factory_name"]
    Certification["🎓 <b>Certification</b><br/>cert_name"]
    Etapp["🔄 <b>Etapp</b><br/>etapp_name"]

    %% ── Relationships ──
    Project -->|"PRODUCES<br/>{quantity, unit_factor, unit}"| Product
    Project -->|"SCHEDULED_AT<br/>{planned_hours, actual_hours, week,<br/>completed_units, etapp, bop, variance_pct}"| Station
    Project -->|"ACTIVE_IN"| Week
    Project -->|"IN_PHASE"| Etapp

    Worker -->|"WORKS_AT"| Station
    Worker -->|"CAN_COVER"| Station
    Worker -->|"HOLDS"| Certification

    Station -->|"LOADED_IN<br/>{total_planned,<br/>total_actual}"| Week
    Week -->|"HAS_CAPACITY<br/>{own_hours, hired_hours, overtime_hours, total_planned, deficit}"| Factory

    %% ── Styling ──
    classDef proj fill:#4F46E5,stroke:#3730A3,color:#fff,rx:12
    classDef prod fill:#059669,stroke:#047857,color:#fff,rx:12
    classDef stat fill:#D97706,stroke:#B45309,color:#fff,rx:12
    classDef work fill:#DC2626,stroke:#B91C1C,color:#fff,rx:12
    classDef week fill:#7C3AED,stroke:#6D28D9,color:#fff,rx:12
    classDef meta fill:#6B7280,stroke:#4B5563,color:#fff,rx:12
    classDef cert fill:#0891B2,stroke:#0E7490,color:#fff,rx:12
    classDef etap fill:#E11D48,stroke:#BE123C,color:#fff,rx:12

    class Project proj
    class Product prod
    class Station stat
    class Worker work
    class Week week
    class Factory meta
    class Certification cert
    class Etapp etap
```

## Node Labels (8)

| # | Label | Source CSV | Key Properties | Count |
|---|-------|-----------|----------------|-------|
| 1 | **Project** | production.csv | project_id, project_number, project_name | 8 |
| 2 | **Product** | production.csv | product_type, unit | 7 (IQB, IQP, SB, SD, SP, SR, HSQ) |
| 3 | **Station** | production.csv | station_code, station_name | 10 (011–019, 021) |
| 4 | **Worker** | workers.csv | worker_id, name, role, hours_per_week, type | 14 |
| 5 | **Week** | capacity.csv | week_id | 8 (w1–w8) |
| 6 | **Factory** | Implicit | factory_name | 1 |
| 7 | **Certification** | workers.csv | cert_name | 23 unique certs |
| 8 | **Etapp** | production.csv | etapp_name | 2 (ET1, ET2) |

## Relationship Types (9)

| # | Relationship | From → To | Properties (data-carrying?) |
|---|-------------|-----------|----------------------------|
| 1 | **PRODUCES** | Project → Product | ✅ `{quantity, unit_factor, unit}` |
| 2 | **SCHEDULED_AT** | Project → Station | ✅ `{planned_hours, actual_hours, completed_units, week, etapp, bop, variance_pct}` |
| 3 | **ACTIVE_IN** | Project → Week | — |
| 4 | **IN_PHASE** | Project → Etapp | — |
| 5 | **WORKS_AT** | Worker → Station | — (primary station) |
| 6 | **CAN_COVER** | Worker → Station | — (coverage capability) |
| 7 | **HOLDS** | Worker → Certification | — |
| 8 | **LOADED_IN** | Station → Week | ✅ `{total_planned, total_actual}`* |
| 9 | **HAS_CAPACITY**| Week → Factory | ✅ `{own_hours, hired_hours, overtime_hours, total_planned, deficit}` |

> 4 relationships carry data properties (**PRODUCES**, **SCHEDULED_AT**, **LOADED_IN**, **HAS_CAPACITY**), exceeding the minimum of 2.
>
> *\*Note: `LOADED_IN` properties are calculated by aggregating the `SCHEDULED_AT` edges for each station/week.*
>
> *\*Note: `etapp` is also kept as a property on `SCHEDULED_AT` for direct querying. The `Etapp` node is included for L6 compliance, but from a pure design perspective, etapp works better as an edge property since it only has 2 values and carries no properties of its own.*
