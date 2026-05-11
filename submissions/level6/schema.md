```mermaid
graph TD

Worker -->|WORKS_AT| Station
Worker -->|CAN_COVER| Station
Worker -->|HAS_CERTIFICATION| Certification
Worker -->|WORKED_ON| Project

Project -->|HAS_PRODUCT| Product
Project -->|USES_STATION| Station
Project -->|PROCESSED_AT| Station
Project -->|SCHEDULED_IN| Week

Week -->|HAS_CAPACITY| Capacity
```
