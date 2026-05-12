# Level 6 — Factory Production Knowledge Graph Dashboard

## Overview

For Level 6, I built a Neo4j-powered factory production knowledge graph dashboard using Streamlit and Neo4j AuraDB.

The goal of this project was to transform the provided factory CSV datasets into a graph-based operational analytics system capable of visualizing:

- production bottlenecks
- station workload
- project variance
- worker coverage
- capacity deficits
- factory relationships

Instead of relying on spreadsheet-based tracking, the graph structure enables connected operational reasoning across projects, workers, stations, and production timelines.

---

# Graph Architecture

## Node Labels

The dashboard models the factory using the following graph entities:

- `Project`
- `Product`
- `Station`
- `Worker`
- `Week`
- `Capacity`
- `Certification`
- `Bottleneck`

---

## Relationship Types

The graph contains multiple operational relationships including:

- `HAS_PRODUCT`
- `USES_STATION`
- `PROCESSED_AT`
- `WORKED_ON`
- `ASSIGNED_TO`
- `CERTIFIED_FOR`
- `SCHEDULED_IN`
- `HAS_CAPACITY`
- `HAS_BOTTLENECK`
- `OVERLOADED_IN`

Several relationships store operational properties such as:
- planned hours
- actual hours
- variance
- overload percentage
- workload values

This makes the graph useful for production analytics instead of only structural modeling.

---

# Dashboard Features

## 1. Project Overview

Displays:
- all projects
- planned vs actual production hours
- project variance
- operational performance metrics

This helps management quickly identify projects exceeding production estimates.

---

## 2. Station Load Dashboard

Visualizes station workload across the factory using charts and aggregated workload calculations.

This makes bottlenecks and overloaded stations immediately visible without manually analyzing spreadsheets.

---

## 3. Capacity Tracker

Tracks:
- weekly factory capacity
- planned demand
- overload deficits

Weeks exceeding capacity thresholds are highlighted for operational visibility.

---

## 4. Worker Coverage Dashboard

Shows:
- worker certifications
- station assignments
- operational backup coverage

This helps identify single points of failure and staffing risks.

---

## 5. Self-Test Dashboard

A dedicated self-test page validates:
- Neo4j connectivity
- graph node counts
- relationship counts
- label counts
- relationship type counts
- Cypher query execution

This ensures the graph was seeded successfully and the dashboard is functioning correctly.

---

# Neo4j Integration

The dashboard uses:
- Neo4j AuraDB
- Cypher queries
- Neo4j Python Driver

Graph seeding is handled through:

```python
seed_graph.py
```

The seeding process uses `MERGE` statements to ensure idempotent graph creation and avoid duplicate nodes.

---

# Streamlit Deployment

The dashboard was deployed using Streamlit Community Cloud.

Deployment includes:
- environment configuration
- Neo4j AuraDB integration
- cloud-hosted dashboard access

The deployment link is included in:

```text
DASHBOARD_URL.txt
```

---

# Technical Stack

## Backend
- Python
- Neo4j
- Cypher
- Pandas

## Frontend
- Streamlit
- Plotly

## Database
- Neo4j AuraDB

---

# Key Learnings

This project significantly improved my understanding of:
- graph database modeling
- Cypher query design
- operational analytics
- production bottleneck analysis
- hybrid graph visualization
- dashboard engineering

One major realization during this project was how naturally graph databases represent operational dependency chains compared to traditional relational tables.

Using graph relationships made it much easier to reason about:
- bottlenecks
- staffing dependencies
- overloaded stations
- downstream production impact

---

# Challenges Faced

Some of the biggest challenges included:

- designing a scalable graph schema
- modeling overload propagation
- connecting Streamlit with AuraDB
- optimizing Cypher queries
- handling production variance calculations
- building operational dashboards instead of static tables

Another challenge was ensuring the graph structure remained useful for both analytics and visualization instead of becoming a simple CSV import system.

---

# Conclusion

This project demonstrates how graph databases can replace spreadsheet-driven production tracking with connected operational intelligence.

By combining:
- Neo4j
- Streamlit
- Cypher analytics
- graph modeling

the dashboard provides a much more scalable and explainable system for factory production monitoring and operational analysis.