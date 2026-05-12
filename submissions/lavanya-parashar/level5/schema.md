---
config:
  layout: dagre
  look: classic
---
flowchart TB
    Project[" Project
    ───────────
    project_id
    project_number
    project_name"] -- PRODUCES --> Product[" Product
    ───────────
    product_type
    unit
    quantity
    unit_factor"]
    Project -- SCHEDULED_AT {planned_hours, actual_hours, completed_units, bop} --> Station[" Station
    ───────────
    station_code
    station_name"]
    Project -- RUNS_IN --> Week[" Week
    ───────────
    week"]
    Project -- IN_ETAPP --> Etapp[" Etapp
    ───────────
    etapp"]
    Product -. PROCESSED_AT .-> Station
    Worker[" Worker
    ───────────
    worker_id
    name
    role
    hours_per_week
    type"] -- WORKS_AT --> Station
    Worker -. CAN_COVER .-> Station
    Worker -- AVAILABLE_IN {hours_per_week} --> Week
    Week -- HAS_CAPACITY --> Capacity[" Capacity
    ───────────
    own_staff_count
    hired_staff_count
    own_hours
    hired_hours
    overtime_hours
    total_capacity
    total_planned
    deficit"]

    style Project fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a
    style Product fill:#dcfce7,stroke:#16a34a,color:#14532d
    style Station fill:#fef9c3,stroke:#ca8a04,color:#713f12
    style Week fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    style Etapp fill:#ffedd5,stroke:#ea580c,color:#7c2d12
    style Worker fill:#fce7f3,stroke:#db2777,color:#831843
    style Capacity fill:#ccfbf1,stroke:#0d9488,color:#134e4a