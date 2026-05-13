# Dataset Inspection Notes

## factory_production.csv

Observed columns:
- project_id
- product_type
- station_code
- station_name
- week
- planned_hours
- actual_hours

Key observations:
- Multiple projects use the same stations
- Products move through several production stations
- Actual hours sometimes exceed planned hours
- Weekly production flow is important for bottleneck analysis

Possible graph entities:
- Project
- Product
- Station
- Week

Possible relationship properties:
- planned_hours
- actual_hours
- variance_percent
- week


---

## factory_workers.csv

Observed columns:
- worker_name
- primary_station
- certifications
- role
- cover_stations

Key observations:
- Workers can cover multiple stations
- Certifications determine substitution capability
- Some stations depend on a small number of workers

Possible graph entities:
- Worker
- Certification
- Station

Possible relationships:
- PRIMARY_OPERATOR_AT
- CAN_COVER
- HAS_CERTIFICATION


---

## factory_capacity.csv

Observed columns:
- week
- station
- planned_capacity
- actual_demand
- deficit

Key observations:
- Some stations exceed weekly capacity
- Capacity deficits vary across weeks
- Weekly overload patterns can trigger alerts

Possible graph entities:
- Capacity
- Week
- Station
- Alert

Possible relationships:
- HAS_CAPACITY
- OVERLOADED_AT
- TRIGGERED_FOR


---

# Initial Graph Modeling Thoughts

The system naturally fits a graph structure because:
- projects connect to products and stations
- workers connect to certifications and coverage stations
- weekly capacity creates temporal operational dependencies
- bottlenecks propagate across multiple connected entities

Graph traversal makes staffing impact and overload analysis easier than multi-table relational joins.