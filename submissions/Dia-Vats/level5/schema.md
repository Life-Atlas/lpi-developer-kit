# Level 5 — Graph Schema

## Schema Diagram

![Graph Schema](schema.png)

---

## Mermaid Source

```mermaid
flowchart LR

    Project -->|HAS_WORKORDER| WorkOrder
    WorkOrder -->|AT_STATION| Station
    WorkOrder -->|PRODUCES| Product
    WorkOrder -->|SCHEDULED_IN| Week

    Week -->|HAS_CAPACITY| CapacitySnapshot

    Worker -->|ASSIGNED_TO| Station
    Worker -->|CAN_COVER| Station
    Worker -->|CERTIFIED_IN| Certification

    Station -->|REQUIRES| Certification

    Station -->|FEEDS_INTO| Station

    WorkOrder -->|FOLLOWS| WorkOrder
```

---

## Relationship Properties

| Relationship | Properties |
|---|---|
| `SCHEDULED_IN` | planned_hours, actual_hours, completed_units |
| `PRODUCES` | quantity, unit_factor |

---

## Node Labels

- `Project`
- `WorkOrder`
- `Station`
- `Product`
- `Week`
- `Worker`
- `Certification`
- `CapacitySnapshot`

---

## Relationship Types

- `HAS_WORKORDER`
- `AT_STATION`
- `PRODUCES`
- `SCHEDULED_IN`
- `FEEDS_INTO`
- `FOLLOWS`
- `ASSIGNED_TO`
- `CAN_COVER`
- `CERTIFIED_IN`
- `REQUIRES`
- `HAS_CAPACITY`