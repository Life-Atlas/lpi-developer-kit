# Level 6 — Factory Production Knowledge Graph Dashboard

## Overview

Built a Neo4j + Streamlit knowledge graph dashboard for factory production analytics using the provided production, worker, and capacity datasets.

The project models relationships between projects, workers, products, stations, weeks, and capacity planning using graph structures in Neo4j AuraDB.

The dashboard provides interactive analytics, bottleneck detection, worker coverage analysis, and production workload visualization.

---

# Features Implemented

## Graph Database
- Neo4j AuraDB integration
- Graph schema with 8+ node labels
- 10+ relationship types
- Relationship properties for workload tracking

## Dashboard Pages
- Project Overview
- Station Load
- Capacity Tracker
- Worker Coverage
- Self-Test Validation

## Analytics
- Planned vs actual hour variance
- Capacity deficit tracking
- Station overload detection
- Worker certification coverage
- Graph-powered Cypher queries

---

# Tech Stack

- Python
- Neo4j AuraDB
- Streamlit
- Pandas
- Plotly
- Cypher Query Language

---

# Graph Schema

## Node Labels
- Project
- Product
- Station
- Worker
- Week
- Capacity
- Certification
- Bottleneck

## Relationship Types
- HAS_PRODUCT
- USES_STATION
- WORKED_ON
- CERTIFIED_FOR
- ASSIGNED_TO
- HAS_CAPACITY
- OVERLOADED_IN
- TRACKED_IN
- DEPENDS_ON
- CAUSED_BOTTLENECK

---

# Self-Test Results

✅ Neo4j connected  
✅ 90+ nodes created  
✅ 200+ relationships created  
✅ 8+ labels detected  
✅ 10+ relationship types detected  
✅ Variance query functional  

Self-Test Score: 20/20

---

# Dashboard Capabilities

## Project Overview
Displays project-level planned vs actual production hours and variance metrics.

## Station Load
Shows workload distribution across all factory stations using interactive charts.

## Capacity Tracker
Tracks weekly production capacity deficits and highlights overload periods.

## Worker Coverage
Displays worker certifications and station staffing coverage.

## Self-Test
Validates graph integrity, schema completeness, and query execution.

---

# Cypher Example

```cypher
MATCH (p:Project)-[r:USES_STATION]->(s:Station)
WHERE r.actual_hours > r.planned_hours * 1.1
RETURN p.name, s.name, r.actual_hours, r.planned_hours
```

# Learning Outcomes

This project improved my understanding of:

Knowledge graph modeling
Neo4j graph databases
Cypher query design
Graph-based production analytics
Streamlit dashboard engineering
Capacity planning visualization
Factory workflow modeling
Repository

See:

repo_link.txt
DASHBOARD_URL.txt


Author
Kailash Narayana Prasad