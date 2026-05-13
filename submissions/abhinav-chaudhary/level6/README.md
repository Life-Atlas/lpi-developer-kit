# Factory Knowledge Graph Dashboard

A graph-based production dashboard for a Swedish steel fabrication factory.
Data from three CSVs is loaded into Neo4j as a knowledge graph, then explored through a Streamlit app with Plotly charts.

Built for the Level 6 factory graph challenge focused on Neo4j and Streamlit..

\---

## What it does

The factory runs 8 projects across 9 production stations with 13 workers.
Raw CSV data (production runs, worker assignments, weekly capacity) is converted into a Neo4j graph with 9 node labels and 12 relationship types.

The dashboard has five pages:

|Page|What it shows|
|-|-|
|**Project Overview**|Variance heatmap — which projects are ahead or behind plan, by week|
|**Station Load**|Planned vs actual hours per station, overrun highlighting|
|**Capacity Tracker**|Weekly capacity breakdown (own / hired / overtime) vs demand|
|**Worker Coverage**|Which workers can cover each station, cert gaps, full roster|
|**Self-Test**|Schema validation — connection, node counts, rel counts, edge properties|

\---

## Tech stack

* **Python 3.11+**
* **Neo4j 5.x** — graph database
* **Streamlit** — dashboard UI
* **Plotly** — interactive charts
* **Pandas** — dataframe wrangling
* **python-dotenv** — local credential management

\---

## Project structure

```
.
├── app.py                  # Streamlit dashboard
├── seed\_graph.py           # Loads CSVs → Neo4j graph
├── factory\_production.csv  # Production runs data
├── factory\_workers.csv     # Worker \& certification data
├── factory\_capacity.csv    # Weekly capacity snapshots
├── schema.md               # Graph schema (Mermaid diagram + reference tables)
├── answers.md              # Level 5/6 analysis write-up
├── .env                    # Your credentials (not committed)
└── README.md
```

\---

## Setup

### 1\. Clone and install dependencies

```bash
git clone <your-repo-url>
cd <your-repo>

python -m venv venv
source venv/bin/activate        # Windows: venv\\Scripts\\activate

pip install streamlit neo4j pandas plotly python-dotenv
```

### 2\. Start Neo4j

You can use [Neo4j Desktop](https://neo4j.com/download/), [AuraDB](https://neo4j.com/cloud/aura-free/) (free tier), or Docker:

```bash
docker run \\
  --name neo4j-factory \\
  -p 7474:7474 -p 7687:7687 \\
  -e NEO4J\_AUTH=neo4j/yourpassword \\
  neo4j:5
```

### 3\. Create your `.env`

Create a `.env` file in the project root:

```env
NEO4J\_URI=bolt://localhost:7687
NEO4J\_USER=neo4j
NEO4J\_PASSWORD=yourpassword
```

> For AuraDB, use the `neo4j+s://` URI from your instance dashboard.

### 4\. Seed the graph

This loads all three CSVs into Neo4j. Run it once (or re-run after a `MATCH (n) DETACH DELETE n` to reset):

```bash
python seed\_graph.py
```

### 5\. Run the dashboard

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

\---

## Streamlit Cloud deployment

1. Push the repo to GitHub (make sure `.env` is in `.gitignore`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Add your credentials under **Settings → Secrets**:

```toml
NEO4J\_URI = "neo4j+s://xxxx.databases.neo4j.io"
NEO4J\_USER = "neo4j"
NEO4J\_PASSWORD = "yourpassword"
```

The app reads `st.secrets` first, so no other changes needed.

\---

## Graph schema (quick reference)

**9 node labels:** `Project` · `ProductionEntry` · `Station` · `Product` · `Worker` · `Week` · `CapacitySnapshot` · `Certification` · `BOP`

**12 relationship types:** `HAS\_RUN` · `USES\_PRODUCT` · `PROCESSED\_AT` · `SCHEDULED\_IN` · `REQUIRES\_STATION` · `STRUCTURED\_BY` · `PRIMARILY\_AT` · `CAN\_COVER` · `WORKED\_ON` · `HOLDS` · `REQUIRES\_CERT` · `HAS\_SNAPSHOT`

Two relationships carry data properties:

* `PROCESSED\_AT` → `planned\_hours`, `actual\_hours`, `completed\_units`
* `SCHEDULED\_IN` → `planned\_hours`, `actual\_hours`

See `schema.md` for the full Mermaid diagram and relationship reference table.

\---

## Running the self-test

Navigate to the **Self-Test** page in the sidebar and click **▶ Run All Tests**.

It checks:

1. Neo4j connection
2. All 9 node labels present
3. All 12 relationship types present
4. Node count ≥ 50
5. Relationship count ≥ 100
6. Variance query returns results from `PROCESSED\_AT` edge properties

\---

## Notes

* Data is cached for 5 minutes (`@st.cache\_data(ttl=300)`) — refresh the page or restart Streamlit to force a reload.
* All dashboard queries run directly against Neo4j after the graph is seeded.
* `seed\_graph.py` is idempotent — it uses `MERGE` throughout, so re-running won't duplicate data.

