# Factory Knowledge Graph — Neo4j Schema

> Swedish steel fabrication factory · 8 projects · 9 production stations · 13 workers  
> Stack: Neo4j 5.x · Python driver · Streamlit · (optional) vector index for hybrid search

```mermaid
classDiagram
    direction TB

    class Project {
        <<Node>>
        +String  project_id      PK
        +String  project_number
        +String  project_name
        +String  etapp
    }

    class ProductionEntry {
        <<CentralNode>>
        +String  entry_id        PK
        +Float   planned_hours
        +Float   actual_hours
        +Integer completed_units
        +Integer quantity
    }

    class Station {
        <<Node>>
        +String  station_code    PK
        +String  station_name
    }

    class Product {
        <<Node>>
        +String  product_type    PK
        +String  unit
        +Float   unit_factor
    }

    class Worker {
        <<Node>>
        +String  worker_id       PK
        +String  name
        +String  role
        +Integer hours_per_week
        +String  type
    }

    class Week {
        <<Node>>
        +String  week_id         PK
    }

    class CapacitySnapshot {
        <<Node>>
        +Integer own_hours
        +Integer hired_hours
        +Integer overtime_hours
        +Integer total_capacity
        +Integer total_planned
        +Integer deficit
    }

    class Certification {
        <<Node>>
        +String  cert_id         PK
        +String  name
        +String  issuing_body
    }

    class BOP {
        <<Node>>
        +String  bop_id          PK
        +String  etapp
    }

    %% Core production flow
    Project         "1"    -->  "1..*"  ProductionEntry  : HAS_RUN
    ProductionEntry "0..*" -->  "1"     Product          : USES_PRODUCT
    ProductionEntry "0..*" -->  "1"     Station          : PROCESSED_AT [★]
    ProductionEntry "0..*" -->  "1"     Week             : SCHEDULED_IN [★]
    Project         "0..*" -->  "0..*"  Station          : REQUIRES_STATION
    Project         "0..*" -->  "1"     BOP              : STRUCTURED_BY

    %% Worker relationships
    Worker          "0..*" -->  "1"     Station          : PRIMARILY_AT
    Worker          "0..*" -->  "0..*"  Station          : CAN_COVER
    Worker          "0..*" -->  "0..*"  ProductionEntry  : WORKED_ON
    Worker          "0..*" -->  "0..*"  Certification    : HOLDS

    %% Station certification constraints
    Station         "0..*" -->  "0..*"  Certification    : REQUIRES_CERT

    %% Capacity tracking
    Week            "1"    -->  "1"     CapacitySnapshot : HAS_SNAPSHOT
```

> **[★] Relationship properties** stored as Neo4j edge attributes:
>
> | Relationship | Properties |
> |---|---|
> | `PROCESSED_AT` | `planned_hours: Float`, `actual_hours: Float`, `completed_units: Integer` |
> | `SCHEDULED_IN` | `planned_hours: Float`, `actual_hours: Float` |

---

## Node Reference

| Label | Stereotype | Key Properties | CSV Source |
|---|---|---|---|
| `Project` | `<<Node>>` | project_id (PK), project_number, project_name, etapp | factory_production.csv |
| `ProductionEntry` | `<<CentralNode>>` | entry_id (PK), planned_hours, actual_hours, completed_units, quantity | factory_production.csv |
| `Station` | `<<Node>>` | station_code (PK), station_name | factory_production.csv |
| `Product` | `<<Node>>` | product_type (PK), unit, unit_factor | factory_production.csv |
| `Worker` | `<<Node>>` | worker_id (PK), name, role, hours_per_week, type | factory_workers.csv |
| `Week` | `<<Node>>` | week_id (PK) | factory_capacity.csv |
| `CapacitySnapshot` | `<<Node>>` | own_hours, hired_hours, overtime_hours, total_capacity, total_planned, deficit | factory_capacity.csv |
| `Certification` | `<<Node>>` | cert_id (PK), name, issuing_body | factory_workers.csv |
| `BOP` | `<<Node>>` | bop_id (PK), etapp | factory_production.csv |

## Relationship Reference

| Relationship | From → To | Cardinality | Properties |
|---|---|---|---|
| `HAS_RUN` | Project → ProductionEntry | `1 → 1..*` | — |
| `USES_PRODUCT` | ProductionEntry → Product | `0..* → 1` | — |
| `PROCESSED_AT` ★ | ProductionEntry → Station | `0..* → 1` | planned_hours, actual_hours, completed_units |
| `SCHEDULED_IN` ★ | ProductionEntry → Week | `0..* → 1` | planned_hours, actual_hours |
| `REQUIRES_STATION` | Project → Station | `0..* → 0..*` | — |
| `STRUCTURED_BY` | Project → BOP | `0..* → 1` | — |
| `PRIMARILY_AT` | Worker → Station | `0..* → 1` | — |
| `CAN_COVER` | Worker → Station | `0..* → 0..*` | — |
| `WORKED_ON` | Worker → ProductionEntry | `0..* → 0..*` | — |
| `HOLDS` | Worker → Certification | `0..* → 0..*` | — |
| `REQUIRES_CERT` | Station → Certification | `0..* → 0..*` | — |
| `HAS_SNAPSHOT` | Week → CapacitySnapshot | `1 → 1` | — |
