# Factory Production Graph Schema

```mermaid
graph TD

Project -->|CONTAINS_PRODUCT| Product
Product -->|PRODUCED_AT| Station
Worker -->|ASSIGNED_TO| Station
Worker -->|CERTIFIED_FOR| Certification
Project -->|SCHEDULED_IN| Week
Station -->|OVERLOADED_IN| Week
Project -->|CAUSES_ALERT| Bottleneck
Worker -->|WORKS_ON| Project
Project -->|USES_STATION {planned_hours, actual_hours}| Station
Worker -->|WORKED_AT {hours, week}| Station

Project[Project]
Product[Product]
Station[Station]
Worker[Worker]
Week[Week]
Certification[Certification]
Bottleneck[Bottleneck]
```