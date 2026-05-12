# Level 5: Graph Schema Diagram
**Author:** Aditi Mehta

```mermaid
graph TD
    %% Nodes (8 Labels)
    Project((Project))
    Product((Product))
    Station((Station))
    Worker((Worker))
    Week((Week))
    Etapp((Etapp))
    Skill((Skill))
    Factory((Factory))

    %% Relationships (8 Types) with Data Properties
    Project -- "PRODUCES {quantity, unit_factor}" --> Product
    Project -- "SCHEDULED_AT {week, planned_hours, actual_hours}" --> Station
    Project -- "BELONGS_TO" --> Etapp
    Project -- "PLANNED_IN" --> Week
    
    Worker -- "WORKS_AT" --> Station
    Worker -- "CAN_COVER" --> Station
    
    
    Worker -- "CERTIFIED_FOR" --> Skill
    Week -- "HAS_CAPACITY {own, hired, overtime, deficit}" --> Factory