# Swedish Steel Factory — Neo4j Production Dashboard
**Author: Dia Vats**

A production-ready Streamlit + Neo4j dashboard for a Swedish steel fabrication factory, built on a fully normalised graph schema with 9 node labels, 11 relationship types, and 7 interactive dashboard pages.

---

## Project Structure

```
l6_dashboard/
├── app.py                    # Main Streamlit entry point (7-page sidebar nav)
├── db.py                     # Shared Neo4j driver (secrets → .env fallback)
├── seed_graph.py             # Graph seeder — run once before the dashboard
├── requirements.txt
├── .env.example              # Local env template
├── .streamlit/
│   └── secrets.toml.example  # Streamlit Cloud secrets template
├── pages_impl/
│   ├── page1_overview.py     # Project Overview
│   ├── page2_station.py      # Station Load Heatmap
│   ├── page3_capacity.py     # Capacity Tracker
│   ├── page4_workers.py      # Worker Coverage + SPOF
│   ├── page5_floor.py        # Factory Floor (Bonus B)
│   ├── page6_forecast.py     # Forecast (Bonus C)
│   └── page7_selftest.py     # Self-Test (20 pts)
└── README.md
```

Copy the three CSV files into this folder alongside `seed_graph.py`:
- `factory_production.csv`
- `factory_workers.csv`
- `factory_capacity.csv`

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Neo4j credentials

**Local (`.env`):**
```bash
cp .env.example .env
# Edit .env with your actual Neo4j URI, user, password
```

**Streamlit Cloud (`.streamlit/secrets.toml`):**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your credentials
```

### 3. Seed the graph
```bash
python seed_graph.py
```
This is safe to re-run — uses `MERGE` everywhere. Expected output includes node and relationship counts.

### 4. Launch the dashboard
```bash
streamlit run app.py
```

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 🗂️ Project Overview | Grouped bar chart, KPI cards, variance table (red if > 10%) |
| 🔥 Station Load | Plotly heatmap stations × weeks, green/yellow/red scale |
| ⚡ Capacity Tracker | Capacity vs demand bar chart, deficit weeks in red, insight text |
| 👷 Worker Coverage | SPOF detection, expandable station cards, downstream risk via FEEDS_INTO |
| 🏭 Factory Floor | Scatter-based floor plan, stations coloured by load severity |
| 📈 Forecast | Linear extrapolation to week 9, star markers, risk summary |
| ✅ Self-Test | 6 automated checks, 20-point score, runs on every load |

---

## Graph Schema

**9 Node Labels:** `Project`, `WorkOrder`, `Station`, `Product`, `Week`, `Worker`, `Certification`, `CapacitySnapshot`, `Etapp`

**11 Relationship Types:** `HAS_WORKORDER`, `AT_STATION`, `PRODUCES`, `SCHEDULED_IN`, `HAS_CAPACITY`, `ASSIGNED_TO`, `CAN_COVER`, `CERTIFIED_IN`, `REQUIRES`, `FEEDS_INTO`, `FOLLOWS`

**WorkOrder ID format:** `{project_id}_{station_code}_{week}_{product_type}` e.g. `P01_011_w1_IQB`

**Bottleneck rule:** `is_bottleneck = True` when `actual_hours > planned_hours × 1.1`

---

## Self-Test Scoring

| Check | Points | Criteria |
|-------|--------|----------|
| 1 | 3 | Neo4j connection alive |
| 2 | 3 | Node count ≥ 50 |
| 3 | 3 | Relationship count ≥ 100 |
| 4 | 3 | 6+ distinct node labels |
| 5 | 3 | 8+ distinct relationship types |
| 6 | 5 | Bottleneck query returns results |
| **Total** | **20** | |

---

*Made by Dia Vats*
