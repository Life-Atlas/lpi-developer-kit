# Factory Production Dashboard - Level 6

## Overview

This project is a Streamlit-based factory analytics dashboard built using real manufacturing CSV datasets. The dashboard provides insights into production planning, worker coverage, station load, and factory capacity analysis.

The project uses:
- Streamlit for dashboard UI
- Plotly for interactive charts
- Pandas for CSV data analysis
- Neo4j concepts for graph-based manufacturing modeling

---

## Features

### 1. Project Overview
- Planned vs actual production hours
- Completed units by project
- Project performance comparison

### 2. Capacity Analysis
- Weekly factory capacity tracking
- Planned workload comparison
- Deficit and surplus analysis

### 3. Worker Coverage
- Permanent vs hired worker distribution
- Worker role analysis
- Workforce coverage insights

### 4. Station Load
- Station-wise actual production hours
- Completed units by station
- Manufacturing bottleneck analysis

### 5. Self Test Page
- Verifies dashboard functionality
- Checks CSV loading
- Confirms Plotly integration
- Validates multi-page dashboard setup

---

## Files Included

- `app.py` → Main Streamlit dashboard
- `seed_graph.py` → CSV loading and graph preparation
- `factory_production.csv` → Production dataset
- `factory_capacity.csv` → Capacity planning dataset
- `factory_workers.csv` → Worker dataset
- `requirements.txt` → Python dependencies

---

## Technologies Used

- Python
- Streamlit
- Plotly
- Pandas
- Neo4j
- CSV Data Processing

---

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run Streamlit app:

```bash
streamlit run app.py
```

---

## Dashboard Goals

This dashboard was designed to:
- Analyze factory production efficiency
- Identify manufacturing bottlenecks
- Monitor workforce coverage
- Compare planned vs actual performance
- Support operational decision making