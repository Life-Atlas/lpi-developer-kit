# Level 6 — Factory Production Knowledge Graph Dashboard

## Overview

This project transforms factory production planning data into an interactive knowledge graph dashboard using Neo4j and Streamlit.

The dataset models a Swedish steel fabrication company's production workflow across:

- 8 construction projects
- 9 production stations
- 13+ workers
- weekly capacity planning
- operational bottleneck analysis

Instead of relying on spreadsheets, this implementation uses graph relationships to model production dependencies, staffing coverage, overload risk, and operational intelligence.

---

## Architecture

### Tech Stack

- Neo4j Desktop (graph database)
- Cypher (graph queries)
- Python 3
- Streamlit
- Pandas
- Plotly

---

## Graph Schema

### Node Types

- `Project`
- `Product`
- `Station`
- `Worker`
- `Week`
- `Capacity`
- `Certification`

### Relationships

- `(:Project)-[:USES_PRODUCT]->(:Product)`
- `(:Project)-[:GOES_THROUGH {planned_hours, actual_hours, completed_units}]->(:Station)`
- `(:Worker)-[:PRIMARY_AT]->(:Station)`
- `(:Worker)-[:CAN_COVER]->(:Station)`
- `(:Worker)-[:HAS_CERTIFICATION]->(:Certification)`
- `(:Project)-[:ACTIVE_IN]->(:Week)`
- `(:Capacity)-[:HAS_CAPACITY]->(:Week)`

---

## Features Implemented

### 1. Executive KPI Dashboard

Displays:

- Total factory capacity
- Total planned production hours
- Net deficit
- overloaded project count
- max operational overrun

---

### 2. Planned vs Actual Station Analytics

Interactive comparison of:

- planned production hours
- actual production hours
- station-level bottleneck identification

---

### 3. Worker Coverage Intelligence

Graph-powered staffing analysis showing:

- workers by station
- cross-station coverage
- single-point failure detection
- staffing risk visibility

---

### 4. Overload Detection with Explainability

Projects exceeding planning thresholds are flagged.

Each alert explains:

- affected project
- station
- planned hours
- actual hours
- variance reason

This adds explainability rather than black-box alerting.

---

### 5. Operational Risk Classification

Risk levels:

- LOW
- MEDIUM
- HIGH

Calculated from variance percentage between planned vs actual execution.

---

### 6. Station Search Tool

Interactive lookup for:

- station code
- available certified workers
- staffing fallback coverage

Example:
Station 016 (Gjutning)

---

## Screenshots

### Neo4j Knowledge Graph

![Neo4j Graph](../../examples/factory_graph_dashboard/screenshots/neo4j-graph-schema.png)

---

### KPI Dashboard

![KPI Dashboard](../../examples/factory_graph_dashboard/screenshots/dashboard-kpi-overview.png)

---

### Planned vs Actual Analysis

![Planned vs Actual](../../examples/factory_graph_dashboard/screenshots/planned-vs-actual-stations.png)

---

### Worker Coverage Risk

![Worker Coverage](../../examples/factory_graph_dashboard/screenshots/worker-coverage-risk.png)

---

### Explainability Layer

![Explainability](../../examples/factory_graph_dashboard/screenshots/overloaded-projects-explainability.png)

---

### Operational Risk Dashboard

![Risk Dashboard](../../examples/factory_graph_dashboard/screenshots/operational-risk-analysis.png)

---

### Station Search

![Station Search](../../examples/factory_graph_dashboard/screenshots/station-search-016.png)

---

## Business Value

This replaces spreadsheet-driven operational tracking with:

- graph-based dependency modeling
- explainable overload alerts
- workforce resilience analysis
- operational decision intelligence
- searchable production knowledge graph

---

## Run Instructions

### Install dependencies

```bash
pip install streamlit pandas plotly neo4j
```

### Start Neo4j

Run local Neo4j Desktop instance.

### Load graph

```bash
python3 ingest_data.py
```

### Launch dashboard

```bash
streamlit run app.py
```

---

## Submission

Level 6 Knowledge Graph Dashboard
