# Factory Knowledge Graph Dashboard

## Overview

A Neo4j + Streamlit dashboard for factory production planning and workforce analysis using a knowledge graph model.

The system represents factory operations as interconnected graph entities to support operational monitoring, capacity planning, staffing analysis, and forecasting.

---

## Tech Stack

- Python
- Neo4j AuraDB
- Streamlit
- Pandas
- Plotly
- NumPy
- python-dotenv

---

## Knowledge Graph Model

### Node Labels
- Project
- Product
- Station
- Worker
- Week
- Etapp
- BOP
- Certification
- Capacity

### Relationship Types
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

## Dashboard Features

### Project Overview
Project-wise planned vs actual production hour comparison with variance analysis.

### Station Load
Station workload monitoring with overloaded station detection.

### Capacity Tracker
Weekly capacity vs planned demand analysis with deficit visualization.

### Worker Coverage
Cross-station worker coverage analysis with single point of failure detection.

### Production Forecast (Bonus)
Trend-based workload forecasting with confidence bands for future planning.

### Self-Test
Automated Neo4j validation checks with scoring out of 20.

---

## Local Setup

### Install dependencies
```bash
pip install -r requirements.txt
```

### Configure environment variables
Create a `.env` file:

```env
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
```

### Seed the graph
```bash
python seed_graph.py
```

### Run dashboard
```bash
streamlit run app.py
```

---

## Deployment

Live Dashboard:  
https://lpi-developer-kit-exok2achm8rvscbqwf4gyc.streamlit.app/

---

## Author

Aadyant Sood