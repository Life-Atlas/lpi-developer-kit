# Level 5 Schema Diagram — Factory Knowledge Graph

This Mermaid diagram is the schema design for Level 5. It uses the three CSV files in `challenges/data/` as the source of truth.

```mermaid
erDiagram
    PROJECT {
        string project_id PK
        string project_number
        string name
    }

    PRODUCT {
        string product_type PK
        string unit
    }

    STATION {
        string station_code PK
        string name
    }

    WORKER {
        string worker_id PK
        string name
        string role
        string type
        float hours_per_week
    }

    WEEK {
        string week PK
        int sort_order
    }

    ETAPP {
        string etapp_id PK
    }

    BOP {
        string bop_id PK
    }

    CERTIFICATION {
        string name PK
    }

    CAPACITY_PLAN {
        string capacity_id PK
        float own_hours
        float hired_hours
        float overtime_hours
        float total_capacity
        float total_planned
        float deficit
        int own_staff_count
        int hired_staff_count
        boolean is_deficit
    }

    BOTTLENECK_ALERT {
        string alert_id PK
        string severity
        string reason
        float planned_hours
        float actual_hours
        float variance_hours
        float variance_pct
    }

    PROJECT ||--o{ PRODUCT : PRODUCES_qty_unit_factor
    PROJECT ||--o{ STATION : SCHEDULED_AT_week_planned_actual_completed
    PROJECT ||--o{ WEEK : HAS_WORK_IN_planned_actual
    PROJECT ||--o{ ETAPP : HAS_ETAPP
    PROJECT ||--o{ BOP : USES_BOP
    PRODUCT ||--o{ STATION : REQUIRES_STATION
    WORKER ||--|| STATION : PRIMARY_AT
    WORKER ||--o{ STATION : CAN_COVER
    WORKER ||--o{ CERTIFICATION : HAS_CERTIFICATION
    WEEK ||--|| CAPACITY_PLAN : HAS_CAPACITY
    CAPACITY_PLAN ||--o{ STATION : CAPACITY_PRESSURE_ON
    BOTTLENECK_ALERT ||--|| PROJECT : FLAGS_PROJECT
    BOTTLENECK_ALERT ||--|| STATION : FLAGS_STATION
    BOTTLENECK_ALERT ||--|| WEEK : FLAGS_WEEK
```

## Relationship Types and Main Properties

| Relationship | From → To | Main source | Important properties |
|---|---|---|---|
| `PRODUCES` | `Project → Product` | `factory_production.csv` | `quantity`, `unit`, `unit_factor` |
| `SCHEDULED_AT` | `Project → Station` | `factory_production.csv` | `week`, `planned_hours`, `actual_hours`, `completed_units`, `variance_hours`, `variance_pct`, `is_over_10pct` |
| `HAS_WORK_IN` | `Project → Week` | `factory_production.csv` | `planned_hours`, `actual_hours`, `station_count` |
| `HAS_ETAPP` | `Project → Etapp` | `factory_production.csv` | `etapp` |
| `USES_BOP` | `Project → BOP` | `factory_production.csv` | `bop` |
| `REQUIRES_STATION` | `Product → Station` | `factory_production.csv` | `times_seen`, `total_planned_hours`, `total_actual_hours` |
| `PRIMARY_AT` | `Worker → Station` | `factory_workers.csv` | `role`, `hours_per_week` |
| `CAN_COVER` | `Worker → Station` | `factory_workers.csv` | `is_primary`, `coverage_source`, `hours_per_week` |
| `HAS_CERTIFICATION` | `Worker → Certification` | `factory_workers.csv` | `certification_name` |
| `HAS_CAPACITY` | `Week → CapacityPlan` | `factory_capacity.csv` | `own_hours`, `hired_hours`, `overtime_hours`, `total_capacity`, `total_planned`, `deficit` |
| `CAPACITY_PRESSURE_ON` | `CapacityPlan → Station` | derived from production + capacity | `station_planned_hours`, `station_actual_hours`, `station_variance_hours`, `share_of_week_demand` |
| `FLAGS_PROJECT` | `BottleneckAlert → Project` | derived | `reason` |
| `FLAGS_STATION` | `BottleneckAlert → Station` | derived | `reason` |
| `FLAGS_WEEK` | `BottleneckAlert → Week` | derived | `reason` |

## Why this schema works

The graph separates stable business entities (`Project`, `Product`, `Station`, `Worker`, `Week`) from measured operational facts (`SCHEDULED_AT`, `HAS_CAPACITY`, `CAPACITY_PRESSURE_ON`, `BOTTLENECK_ALERT`). This makes it easy to answer both planning questions, such as “which stations are overloaded?”, and resilience questions, such as “who can cover a station if a worker is absent?”.
