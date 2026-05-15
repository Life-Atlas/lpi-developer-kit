# Factory Graph Schema — Saima Afroz

See answers.md Q1 for full written explanation.

graph TD
  subgraph Canopy
    Project -->|PRODUCES qty,unit_factor| Product
    Project -->|SCHEDULED_AT planned_h,actual_h,week| Station
    Project -->|BELONGS_TO| Etapp
    Etapp -->|CONTAINS_BOP| BOP
    BOP -->|SPANS_WEEK| Week
    Station -->|ACTIVE_IN| Week
  end
  subgraph Geography
    Factory -->|LOCATED_IN| Country
    Station -->|IN_FACTORY| Factory
    Worker -->|EMPLOYED_IN| Country
  end
  subgraph Underground
    Worker -->|WORKS_AT| Station
    Worker -->|CAN_COVER valid_in_country,cert_valid,travel_days| Station
    Alert -->|TRIGGERED_BY variance_pct| Station
    Alert -->|AFFECTS| Project
  end