# Factory Knowledge Graph Dashboard

## Overview

This project is a Neo4j-powered factory planning and production monitoring dashboard built using Streamlit.

The system models factory operations as a Knowledge Graph containing:
- Projects
- Products
- Stations
- Workers
- Capacity
- Certifications
- Weeks
- Etapp
- BOP

The dashboard enables visualization and analysis of:
- Project production planning
- Station workload
- Capacity tracking
- Worker coverage
- Production variance
- Graph validation checks

---

# Tech Stack

- Python
- Neo4j AuraDB
- Streamlit
- Pandas
- Plotly
- python-dotenv

---

# Knowledge Graph Schema

## Node Labels

- Project
- Product
- Station
- Worker
- Week
- Etapp
- BOP
- Certification
- Capacity

## Relationship Types

- PRODUCES
- SCHEDULED_AT
- OCCURS_IN
- PART_OF
- BELONGS_TO
- WORKS_AT
- CAN_COVER
- HAS_CERTIFICATION
- HAS_CAPACITY

---

# Dashboard Pages

## 1. Project Overview
Displays project-level planned vs actual production hours.

## 2. Station Load
Visualizes workload distribution across factory stations.

## 3. Capacity Tracker
Tracks planned production load against total available capacity.

## 4. Worker Coverage
Shows worker station coverage and flexibility.

## 5. Self-Test
Runs automated graph validation checks and generates a score out of 20.

---

# Setup Instructions

## 1. Create Virtual Environment

```bash
python -m venv venv
```

## 2. Activate Virtual Environment

### Windows

```bash
.\venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file:

```env
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
```

---

## 5. Seed Knowledge Graph

```bash
python seed_graph.py
```

---

## 6. Run Dashboard

```bash
streamlit run app.py
```

---

# Self-Test Criteria

The dashboard automatically validates:

- Neo4j connection
- Minimum node count
- Minimum relationship count
- Node label coverage
- Relationship type coverage
- Variance query functionality

Final score is displayed out of 20.

---

# Author

Aadyant Sood