# Factory Production Knowledge Graph Dashboard

A Neo4j + Streamlit based knowledge graph dashboard built for the Life Atlas L6 challenge.  
This project models factory production data using graph relationships to analyze project workloads, worker coverage, station utilization, and production bottlenecks.

---

# Project Overview

The dashboard transforms traditional factory production CSV datasets into a graph-powered analytics system using Neo4j AuraDB.

The system models:

- Projects
- Products
- Production stations
- Workers
- Capacity planning
- Weekly production tracking
- Certifications
- Bottlenecks

The application provides interactive visualization and graph-powered querying for factory operations and production planning.

---

# Features

## Knowledge Graph Modeling
- Graph-based production planning system
- Neo4j AuraDB backend
- Relationship-driven analytics

## Interactive Dashboard
- Streamlit-based UI
- Multi-page navigation
- Interactive charts and analytics

## Analytics Pages
- Project Overview
- Station Load Analysis
- Capacity Tracker
- Worker Coverage Matrix
- Self-Test Validation

## Automated Validation
- Node count checks
- Relationship validation
- Graph schema verification
- Cypher query testing

---

# Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend logic |
| Neo4j AuraDB | Graph database |
| Streamlit | Dashboard frontend |
| Pandas | Data processing |
| Plotly | Interactive charts |
| Cypher | Graph querying |

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

---

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

# Dataset

The project uses factory production datasets provided in the challenge.

## CSV Files

### factory_production.csv
Contains:
- Project names
- Product types
- Stations
- Planned hours
- Actual hours
- Weekly tracking

### factory_workers.csv
Contains:
- Worker information
- Roles
- Certifications
- Station assignments

### factory_capacity.csv
Contains:
- Weekly capacity
- Planned demand
- Deficit calculations

---

# Dashboard Pages

## 1. Project Overview

Displays:
- Planned vs actual production hours
- Variance analysis
- Project performance metrics

---

## 2. Station Load

Displays:
- Station workload distribution
- Overloaded stations
- Production intensity visualization

---

## 3. Capacity Tracker

Displays:
- Weekly capacity trends
- Demand vs available capacity
- Deficit detection

---

## 4. Worker Coverage

Displays:
- Worker certification matrix
- Station staffing coverage
- SPOF (Single Point of Failure) analysis

---

## 5. Self-Test

Automated graph validation system that checks:

- Neo4j connectivity
- Node counts
- Relationship counts
- Schema compliance
- Query functionality

---

# Setup Instructions

## 1. Clone Repository

```bash 
git clone <your-repository-url>
cd factory-graph-dashboard
```
## 2.Install Dependencies

```bash 
pip install -r requirements.txt
```

### 3. Configure Neo4j AuraDB

Create a .env file in the root folder.

Example:

NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password

## 4. Seed the Graph Database

Run:

python seed_graph.py

This imports all CSV datasets into Neo4j and creates the graph schema.

## 5. Launch Dashboard

Run:

streamlit run app.py

The dashboard will open in your browser automatically.

## Self-Test Score

The application includes a self-test page that validates:

Neo4j connection
Graph completeness
Node and relationship counts
Cypher query execution

## Deployment

The application is designed for deployment using:

Streamlit Cloud
Neo4j AuraDB