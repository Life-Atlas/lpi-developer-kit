# Level 6 — Factory Graph + Dashboard

This folder contains the Level 6 implementation for the factory knowledge graph challenge.

Final submission path:

```text
submissions/jv-singh/level6/
```

No real credentials are committed. Keep Neo4j credentials only in a local `.env` file or in Streamlit Cloud secrets.

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

## Git workflow to keep VS Code in sync

Use this flow after the PR is merged into your own GitHub repository/fork.

1. Open VS Code.
2. Open the terminal in the repository folder.
3. Confirm the remote points to your GitHub repository:

   ```bash
   git remote -v
   ```

4. Switch to the branch you want to keep updated. If you are using `main`:

   ```bash
   git checkout main
   ```

5. Pull the latest merged work:

   ```bash
   git pull
   ```

6. Confirm the Level 6 folder exists:

   ```bash
   test -d submissions/jv-singh/level6 && echo "Level 6 folder found"
   ```

## Step 1 — Environment setup

From the repository root:

```bash
cd submissions/jv-singh/level6/
cp .env.example .env
```

Edit `.env` and replace the placeholder values with your real Neo4j credentials:

```env
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

Important: never commit `.env`.

## Step 2 — Install dependencies and seed Neo4j

From `submissions/jv-singh/level6/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_graph.py
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

On Windows Command Prompt, use:

```bat
.venv\Scripts\activate.bat
```

Expected seed output is a summary similar to:

```text
Seed complete: <node count> nodes, <relationship count> relationships
Labels: ...
Relationship types: ...
```

The seed script is safe to run more than once. It creates uniqueness constraints and uses `MERGE` for nodes and relationships.

## Step 3 — Run the Streamlit app locally

From `submissions/jv-singh/level6/` with the virtual environment active:

```bash
streamlit run app.py
```

Then:

1. Open the browser URL printed by Streamlit.
2. Verify these sidebar pages load:
   - Project Overview
   - Station Load
   - Capacity Tracker
   - Worker Coverage
   - Self-Test
3. Open **Self-Test**.
4. Confirm the self-test score is passing and the checks are green.

## Step 4 — Deploy to Streamlit Community Cloud

1. Push the repository/branch to GitHub.
2. Go to <https://share.streamlit.io>.
3. Create a new app using:
   - repository: your `jvsing-life-atlas` repository/fork
   - branch: the branch containing this submission
   - main file path: `submissions/jv-singh/level6/app.py`
4. In Streamlit Cloud, open **Settings → Secrets**.
5. Add Neo4j credentials in TOML format:

   ```toml
   NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your-password-here"
   ```

6. Save the secrets and redeploy/reboot the Streamlit app if needed.
7. Open the deployed app URL.
8. Verify the **Self-Test** page passes in the deployed app, not only locally.

## Step 5 — Final touch: update the dashboard URL

Replace the placeholder in `DASHBOARD_URL.txt` with the deployed app URL.

Example:

```text
https://your-app-name.streamlit.app
```

Then commit the URL update:

```bash
git add submissions/jv-singh/level6/DASHBOARD_URL.txt
git commit -m "level-6: add deployed dashboard url"
git push
```

## Testing checklist before final PR

Run these commands from `submissions/jv-singh/level6/`.

### Syntax check

```bash
python -m py_compile seed_graph.py app.py
```

### Data validation

```bash
python - <<'PY'
import csv
from pathlib import Path
base=Path('data')
prod=list(csv.DictReader((base/'factory_production.csv').open()))
workers=list(csv.DictReader((base/'factory_workers.csv').open()))
cap=list(csv.DictReader((base/'factory_capacity.csv').open()))
print('production rows', len(prod))
print('projects', len({r['project_id'] for r in prod}))
print('products', len({r['product_type'] for r in prod}))
print('stations', len({r['station_code'] for r in prod}))
print('weeks', len({r['week'] for r in prod} | {r['week'] for r in cap}))
print('workers', len(workers))
print('capacity rows', len(cap))
print('rows with >10% overrun',
sum(float(r['actual_hours']) > float(r['planned_hours'])*1.1 for r in prod))
PY
```

Expected data validation output:

```text
production rows 68
projects 8
products 7
stations 10
weeks 8
workers 14
capacity rows 8
rows with >10% overrun 14
```

### Git whitespace check

Run this from the repository root after staging any final changes:

```bash
git diff --cached --check
```

A pandas import warning is acceptable only before dependencies are installed. After `pip install -r requirements.txt`, pandas should be available.

## Final PR submission

Use this PR title:

```text
level-6: JV Singh
```

Before submitting the final PR, confirm:

- [x] `seed_graph.py` implemented.
- [x] `app.py` implemented with 4 required dashboard pages plus Self-Test.
- [x] Required CSV data copied into `data/`.
- [x] No real credentials committed.
- [ ] Neo4j Aura/Desktop instance created.
- [ ] `python seed_graph.py` run against the Neo4j database.
- [ ] `streamlit run app.py` works locally.
- [ ] Local **Self-Test** page passes.
- [ ] Streamlit Cloud app deployed.
- [ ] Streamlit Cloud secrets added in TOML format.
- [ ] Deployed **Self-Test** page passes.
- [ ] `DASHBOARD_URL.txt` updated with the live dashboard URL.
- [ ] PR title is `level-6: JV Singh`.

## Troubleshooting

### `Missing Neo4j credentials`

Check that `.env` exists in `submissions/jv-singh/level6/` and contains `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.

### Streamlit Cloud cannot connect to Neo4j

Check Streamlit Cloud **Settings → Secrets**. Secrets must be TOML, not `.env` syntax. Use quotes around each value.

### Self-Test fails on node or relationship count

Run `python seed_graph.py` again. The script is idempotent, so rerunning is safe.

### Self-Test passes locally but fails after deployment

The deployed app is probably missing secrets or pointing at a different Neo4j database. Add the same credentials in Streamlit Cloud and reboot the app.
