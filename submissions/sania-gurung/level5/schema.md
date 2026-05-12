# Factory Knowledge Graph Schema

## Graph Schema Diagram

```mermaid
classDiagram
    direction TB

    class Project {
        +String project_id
        +String project_number
        +String project_name
        +String etapp
        +String bop
    }

    class Product {
        +String product_type
        +String unit
        +Float unit_factor
        +Int quantity
    }

    class Station {
        +String station_code
        +String station_name
    }

    class Worker {
        +String worker_id
        +String name
        +String role
        +String type
        +Int hours_per_week
    }

    class Week {
        +String week_id
        +Int own_staff_count
        +Int hired_staff_count
        +Int total_capacity
        +Int total_planned
        +Int deficit
    }

    class Certification {
        +String name
    }

    class Bottleneck {
        +String station_code
        +String detected_week
        +Float avg_overrun_pct
        +String severity
    }

    Project "1" --> "1..*" Product         : HAS_PRODUCT
    Project "1..*" --> "1..*" Station      : USES_STATION
    Project "1..*" --> "1..*" Week         : PRODUCED_IN\nplanned_hours, actual_hours,\ncompleted_units, is_overrun
    Worker "1..*" --> "1" Station          : ASSIGNED_TO
    Worker "1..*" --> "0..*" Station       : CAN_COVER
    Worker "1..*" --> "1..*" Certification : HAS_CERTIFICATION
    Station "1" --> "0..*" Certification   : REQUIRES_CERT
    Product "1..*" --> "1..*" Station      : PROCESSED_AT
    Station "1" --> "0..1" Bottleneck      : HAS_BOTTLENECK
```

## Relationship Properties

| Relationship | Properties |
|---|---|
| `(:Project)-[:PRODUCED_IN]->(:Week)` | `planned_hours`, `actual_hours`, `completed_units`, `is_overrun` |
| `(:Worker)-[:CAN_COVER]->(:Station)` | `certified: true/false` |
| `(:Station)-[:HAS_BOTTLENECK]->(:Bottleneck)` | `detected_week`, `avg_overrun_pct`, `severity` |
