```mermaid
graph TD

Project -->|PRODUCES| Product
Project -->|SCHEDULED_AT| Station
Project -->|RUNS_IN| Week
Project -->|PART_OF| Etapp

Worker -->|WORKS_AT| Station
Worker -->|CAN_COVER| Station

Week -->|HAS_CAPACITY| Capacity

Project -->|OVERLOADED_AT| Station
```
