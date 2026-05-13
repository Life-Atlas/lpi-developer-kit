# Factory Knowledge Graph Schema

```mermaid
graph TD
    Project["**Project**\n─────────────\nid: P01–P08\nnumber: 4501–4508\nname\netapp\nbop"]
    Product["**Product**\n─────────────\ntype: IQB/IQP/SB/SD/SP/SR/HSQ\nunit\nunit_factor"]
    Station["**Station**\n─────────────\ncode: 011–021\nname"]
    Worker["**Worker**\n─────────────\nid: W01–W14\nname\nrole\nhours_per_week\ntype: permanent/hired"]
    Week["**Week**\n─────────────\nid: w1–w8"]
    Etapp["**Etapp**\n─────────────\nid: ET1/ET2"]
    Certification["**Certification**\n─────────────\nname"]
    Capacity["**Capacity**\n─────────────\nown_hours\nhired_hours\novertime_hours\ntotal_capacity\ntotal_planned\ndeficit"]
    Bottleneck["**Bottleneck**\n─────────────\nstation_code\nweek\nexcess_hours\nseverity: HIGH/MEDIUM/LOW"]

    Project -->|"PRODUCES\n{quantity, unit_factor}"| Product
    Project -->|"SCHEDULED_AT\n{week, planned_hours,\nactual_hours, variance_pct}"| Station
    Project -->|IN_ETAPP| Etapp
    Product -->|PROCESSED_AT| Station
    Worker -->|"WORKS_AT\n{primary: true}"| Station
    Worker -->|CAN_COVER| Station
    Worker -->|HAS_CERTIFICATION| Certification
    Week -->|"HAS_CAPACITY\n{deficit, total_capacity,\ntotal_planned}"| Capacity
    Bottleneck -->|TRIGGERED_AT| Station

    style Project fill:#1a3d6e,color:#fff,stroke:#4a7fd4
    style Product fill:#1a5c3a,color:#fff,stroke:#4ab07a
    style Station fill:#6e1a1a,color:#fff,stroke:#d44a4a
    style Worker fill:#5c3a1a,color:#fff,stroke:#b07a4a
    style Week fill:#3a1a6e,color:#fff,stroke:#7a4ad4
    style Etapp fill:#1a4a5c,color:#fff,stroke:#4aa0b0
    style Certification fill:#4a4a1a,color:#fff,stroke:#a0a04a
    style Capacity fill:#3d1a3d,color:#fff,stroke:#904a90
    style Bottleneck fill:#6e3a00,color:#fff,stroke:#d47a00
```

## Key Relationships with Properties

### SCHEDULED_AT (core operational relationship)
```
(P03:Project)-[:SCHEDULED_AT {
    week: "w2",
    planned_hours: 28.0,
    actual_hours: 35.0,
    completed_units: 8,
    variance_pct: 25.0
}]->(S016:Station {code: "016", name: "Gjutning"})
```
> 25% over plan — this is a HIGH bottleneck

### HAS_CAPACITY (weekly workforce data)
```
(w1:Week)-[:HAS_CAPACITY {
    own_hours: 400,
    hired_hours: 80,
    overtime_hours: 0,
    total_capacity: 480,
    total_planned: 612,
    deficit: -132
}]->(cap1:Capacity)
```
> Worst deficit week — 132 hours short

## Node Counts (from real data)

| Label | Count | Source |
|-------|-------|--------|
| Project | 8 | factory_production.csv |
| Product | 7 | factory_production.csv |
| Station | 9 | factory_production.csv |
| Worker | 14 | factory_workers.csv |
| Week | 8 | factory_capacity.csv |
| Etapp | 2 | factory_production.csv |
| Certification | ~12 | factory_workers.csv |
| Capacity | 8 | factory_capacity.csv |
| Bottleneck | ~4 | computed |
| **TOTAL** | **~72** | |

## Relationship Counts (estimated)

| Type | Count | Notes |
|------|-------|-------|
| SCHEDULED_AT | 68 | one per CSV row |
| PRODUCES | ~18 | project × product combos |
| PROCESSED_AT | ~12 | product × station combos |
| IN_ETAPP | 8 | one per project |
| WORKS_AT | ~20 | primary + foreman (all stations) |
| CAN_COVER | ~25 | coverage assignments |
| HAS_CERTIFICATION | ~30 | worker × cert combos |
| HAS_CAPACITY | 8 | one per week |
| TRIGGERED_AT | ~4 | bottleneck nodes |
| **TOTAL** | **~193** | |
```
