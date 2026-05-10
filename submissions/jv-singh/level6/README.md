# Level 6 — Factory Graph + Dashboard

This folder contains my Level 6 implementation for the factory knowledge graph challenge.

## What is included

- `seed_graph.py` — loads the three factory CSV files into Neo4j using idempotent `MERGE` queries.
- `app.py` — Streamlit dashboard with five pages:
  - Project Overview
  - Station Load
  - Capacity Tracker
  - Worker Coverage
  - Self-Test
- `data/` — local copies of the required challenge CSV files.
- `.env.example` — safe credential template with no real secrets.
- `requirements.txt` — Python dependencies for local and Streamlit Cloud runs.
- `DASHBOARD_URL.txt` — placeholder to replace after deployment.

## Graph schema

### Node labels

- `Project`
- `Product`
- `Station`
- `Worker`
- `Week`
- `Etapp`
- `BOP`
- `Certification`
- `CapacityPlan`
- `BottleneckAlert`

### Relationship types

- `PRODUCES`
- `SCHEDULED_AT`
- `HAS_WORK_IN`
- `HAS_ETAPP`
- `USES_BOP`
- `REQUIRES_STATION`
- `ACTIVE_IN`
- `PRIMARY_AT`
- `CAN_COVER`
- `HAS_CERTIFICATION`
- `HAS_CAPACITY`
- `CAPACITY_PRESSURE_ON`
- `FLAGS_PROJECT`
- `FLAGS_STATION`
- `FLAGS_WEEK`

## Local setup

From this folder:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your Neo4j Aura, Neo4j Desktop, or Docker credentials:

```env
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

## Seed Neo4j

Run:

```bash
python seed_graph.py
```

Expected output is a summary similar to:

```text
Seed complete: <node count> nodes, <relationship count> relationships
Labels: ...
Relationship types: ...
```

The seed script is safe to run more than once. It creates uniqueness constraints and uses `MERGE` for nodes and relationships.

## Run the dashboard locally

Run:

```bash
streamlit run app.py
```

Open the local Streamlit URL, then use the sidebar to visit all pages. The **Self-Test** page should show green checks after the graph is seeded.

## Deploy to Streamlit Community Cloud

1. Push this repository/branch to GitHub.
2. Go to <https://share.streamlit.io>.
3. Create a new app using:
   - repository: your fork of `lpi-developer-kit`
   - branch: your submission branch
   - main file path: `submissions/jv-singh/level6/app.py`
4. In app settings, add Streamlit secrets:

   ```toml
   NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your-password-here"
   ```

5. Save the app URL in `DASHBOARD_URL.txt`.
6. Verify the deployed app loads and the **Self-Test** page passes.

## What is not completed yet

I completed the code and documentation in this folder, but I did **not** deploy the Streamlit app because deployment requires your GitHub/Streamlit account and your Neo4j credentials. Before final submission, replace the placeholder in `DASHBOARD_URL.txt` with the deployed Streamlit URL.

## Submission checklist

- [x] `seed_graph.py` implemented.
- [x] `app.py` implemented with 4 required dashboard pages plus Self-Test.
- [x] Required CSV data copied into `data/`.
- [x] No real credentials committed.
- [ ] Neo4j Aura/Desktop instance created by the submitter.
- [ ] `python seed_graph.py` run against the submitter's Neo4j database.
- [ ] Streamlit Cloud app deployed.
- [ ] `DASHBOARD_URL.txt` updated with the live dashboard URL.
- [ ] Pull request title uses `level-6: JV Singh`.
