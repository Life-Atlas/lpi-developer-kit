# Factory Knowledge Graph Dashboard

A Neo4j knowledge graph + Streamlit dashboard built for a Swedish steel fabrication company managing **8 construction projects** across **10 production stations**.

---

## Graph Schema

### Node Labels (7)

| Label | Description | Key Properties |
|---|---|---|
| `Project` | Construction projects | `project_id`, `project_name`, `project_number` |
| `Station` | Production stations in the factory | `station_code`, `station_name` |
| `Product` | Product types manufactured | `product_type`, `unit` |
| `Worker` | Factory workers and inspectors | `worker_id`, `name`, `role`, `type`, `hours_per_week` |
| `Certification` | Skills/certifications a worker holds | `name` |
| `Week` | Weekly schedule with capacity data | `week_id`, `total_capacity`, `total_planned`, `deficit` |
| `Etapp` | Production phase (ET1 or ET2) | `etapp_id` |

---

### Relationship Types (8)

| Relationship | Direction | Description | Properties |
|---|---|---|---|
| `SCHEDULED_AT` | `Project → Station` | Project is scheduled at a station for a specific week | `week`, `planned_hours`, `actual_hours`, `completed_units`, `etapp`, `bop` |
| `PRODUCES` | `Project → Product` | Project manufactures a product type | `quantity`, `unit_factor`, `unit` |
| `PROCESSED_AT` | `Product → Station` | Product type is processed at a station | — |
| `WORKS_AT` | `Worker → Station` | Worker's primary assigned station | — |
| `CAN_COVER` | `Worker → Station` | Worker is certified to cover this station | — |
| `HAS_CERTIFICATION` | `Worker → Certification` | Worker holds this certification/skill | — |
| `BELONGS_TO` | `Project → Etapp` | Project belongs to a production phase | — |
| `SCHEDULED_IN` | `Project → Week` | Project has work scheduled in this week | — |

---

### Graph Stats

| Metric | Count |
|---|---|
| Total Nodes | 72 |
| Total Relationships | 219 |
| Node Labels | 7 |
| Relationship Types | 8 |

---

## Running Locally (after cloning)

### Prerequisites
- Python 3.10+
- A running Neo4j instance (Aura Free, Desktop, or Docker)
- The 3 CSV data files in the project folder

### Step 1 — Clone and set up environment

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd level6

python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2 — Add your Neo4j credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your details:

```
NEO4J_URI=neo4j+ssc://your-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

> **URI scheme guide:**
> - **Aura Free** (cloud): `neo4j+s://xxxxxxxx.databases.neo4j.io`
> - **Self-hosted / self-signed cert**: `neo4j+ssc://your-ip:7687`
> - **Neo4j Desktop** (local): `bolt://localhost:7687`

### Step 3 — Place the CSV files

Make sure these 3 files are in the same folder as `seed_graph.py`:

```
factory_production.csv
factory_workers.csv
factory_capacity.csv
```

### Step 4 — Seed the graph

```bash
python seed_graph.py
```

This creates all nodes and relationships in Neo4j. It is fully **idempotent** — safe to run multiple times without creating duplicates. Expected output:

```
✓ Constraints created
✓ 8 Project nodes
✓ 10 Station nodes
✓ 7 Product nodes
✓ 2 Etapp nodes
✓ 8 Week nodes
✓ 14 Worker nodes + certifications + WORKS_AT + CAN_COVER

  SCHEDULED_AT:      68
  PRODUCES:          32
  PROCESSED_AT:      16
  ...

── Graph Summary ──────────────────────
  Nodes:              72
  Relationships:      219
  Node labels (7):    [...]
  Rel types   (8):    [...]
───────────────────────────────────────
✅ Done — graph is ready!
```

### Step 5 — Run the dashboard

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

Navigate using the **sidebar** to explore all 5 pages:

| Page | What it shows |
|---|---|
| 📊 Project Overview | Planned vs actual hours, variance %, products per project |
| 🏭 Station Load | Interactive bar chart + heatmap; over-plan stations highlighted red |
| 📅 Capacity Tracker | 8-week workforce capacity vs demand; deficit weeks in red |
| 👷 Worker Coverage | Who covers which station; single-point-of-failure alerts |
| ✅ Self-Test | Automated Neo4j checks with green/red scoring |

---

## Common Issues

**SSL certificate error on `seed_graph.py`**
Change your URI scheme in `.env` from `neo4j+s://` to `neo4j+ssc://` to skip certificate verification for self-signed certs.

**`ModuleNotFoundError`**
Make sure your virtual environment is activated before running any commands.

**`KeyError` on secrets in `app.py`**
When running locally, the app falls back to `.env`. Make sure `.env` exists and is filled in correctly.