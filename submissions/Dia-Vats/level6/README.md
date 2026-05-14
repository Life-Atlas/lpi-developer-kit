# Steel Factory Production Dashboard
**Dia Vats | Level 6 - LifeAtlas LPI Developer Kit**
**Live: https://diavats-l6.streamlit.app**

---

## What I Built

The raw data was 3 CSVs describing a Swedish steel factory - 8 projects, 9 stations, 14 workers, 8 weeks. I turned it into a Neo4j knowledge graph and built a 7-page Streamlit dashboard on top of it.

The point wasn't to build a chart on top of a spreadsheet. The graph models actual operational dependencies - which work orders flow through which stations, which workers can cover which stations if someone's out, and where downstream risk accumulates when a station overruns. The dashboard surfaces that reasoning directly.

I also completed 2 bonus pages (Bonus B — Factory Floor, Bonus C — Forecast).

**Graph stats: 148 nodes, 446 relationships, 9 labels, 12 relationship types.**

---

## Graph Schema

**Nodes:** Project, WorkOrder, Station, Product, Week, Worker, Certification, CapacitySnapshot, Etapp

**Relationships:** HAS_WORKORDER, AT_STATION, PRODUCES, SCHEDULED_IN, HAS_CAPACITY, ASSIGNED_TO, CAN_COVER, CERTIFIED_IN, REQUIRES, FEEDS_INTO, FOLLOWS, IN_ETAPP

A few things worth noting:

- WorkOrder is the core unit - one node per row in the production CSV. It sits between Project and Station and carries planned hours, actual hours, variance %, and bottleneck flag.
- FEEDS_INTO chains stations in physical flow order (011 → 012 → ... → 021). This lets you trace downstream impact from any overrunning station.
- FOLLOWS links the same project-station pair across consecutive weeks so you can traverse time without aggregating in every query.
- Bottleneck rule: `actual_hours > planned_hours × 1.1`
- WorkOrder ID format: `P01_011_w1_IQB`

---

## Dashboard Pages

**Page 1 - Project Overview**
KPI cards, grouped bar chart (planned vs actual per project), variance table with red highlights where variance exceeds 10%.

**Page 2 - Station Load**
Plotly heatmap, stations vs weeks, coloured green/yellow/red by variance. Station 016 shows up clearly as the recurring problem.

**Page 3 - Capacity Tracker**
Weekly capacity vs planned demand. Deficit weeks in red. Calls out that 5 of 8 weeks run over capacity, worst at -132 hours in week 1.

**Page 4 - Worker Coverage**
Shows who covers which station and flags single points of failure. Station 016 is marked CRITICAL — Victor Elm is the only backup for Per Hansen, and 4 projects run through that station.

**Page 5 - Factory Floor (Bonus B)**
Scatter-based floor plan with stations on a physical grid, coloured by load severity. Hover shows active projects and overload %.

**Page 6 - Forecast (Bonus C)**
Linear extrapolation from weeks 1–8 per station, projecting week 9. Shows which stations are trending toward overload.

**Page 7 - Self-Test**
6 automated Neo4j checks, scored out of 20. Runs on every page load.

---

## Project Structure

```
submissions/Dia-Vats/level6/
├── app.py
├── db.py
├── seed_graph.py
├── requirements.txt
├── .env.example
├── DASHBOARD_URL.txt
├── README.md
├── data/
│   ├── factory_production.csv
│   ├── factory_workers.csv
│   └── factory_capacity.csv
├── pages_impl/
│   ├── page1_overview.py
│   ├── page2_station.py
│   ├── page3_capacity.py
│   ├── page4_workers.py
│   ├── page5_floor.py
│   ├── page6_forecast.py
│   └── page7_selftest.py
└── .streamlit/
    └── secrets.toml.example
```

---

## Running It

```bash
pip install -r requirements.txt
python seed_graph.py
streamlit run app.py
```

For Streamlit Cloud, add credentials under Settings > Secrets:
```toml
NEO4J_URI = "neo4j+s://your-instance.databases.neo4j.io"
NEO4J_USER = "your-username"
NEO4J_PASSWORD = "your-password"
```

`seed_graph.py` uses MERGE everywhere — safe to re-run without duplicating data.

---

*Made by Dia Vats*