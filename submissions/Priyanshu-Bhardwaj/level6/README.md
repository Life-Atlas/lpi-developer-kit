# 🏭 Factory Production Knowledge Graph

**A Streamlit Dashboard powered by a Neo4j Knowledge Graph for factory production and capacity planning.**

This project transforms a complex, 46-sheet Excel-based manufacturing schedule into a connected graph database. It visualizes project load, identifies operational bottlenecks, tracks weekly capacity constraints, and highlights single points of failure in workforce coverage.

### 🚀 Live Deployment
**Access the deployed dashboard here:** [streamlit app](https://lpi-l6-7v5vyywp4psdzyvgtzyxka.streamlit.app/)

---

## ✨ Key Features (Dashboard Panels)

1. **📊 Project Overview:** Tracks planned vs. actual hours and completion efficiency across all 8 major construction projects.
2. **⚙️ Station Load Matrix:** Interactive visualizations highlighting overloaded production stations week-by-week.
3. **📈 Capacity Tracker:** Monitors total factory capacity against planned demand, explicitly flagging weeks operating in a deficit.
4. **👷 Worker Coverage:** A matrix identifying which workers are certified for which stations, successfully pinpointing Single-Point-of-Failure (SPOF) vulnerabilities.
5. **✅ Automated Self-Test:** A built-in validation suite that tests the live Neo4j connection, verifies node/relationship counts, and executes variance Cypher queries.

## 🛠️ Technology Stack
* **Frontend:** Streamlit, Plotly Express
* **Database:** Neo4j Aura (Graph Database)
* **Data Processing:** Python, Pandas, Cypher query language
* **Environment:** Python `python-dotenv`

---

## 💻 Local Setup & Installation

Follow these steps to run the Knowledge Graph and Dashboard on your local machine.

### 1. Prerequisites
* Python 3.8+ installed.
* A free [Neo4j Aura](https://neo4j.com/cloud/aura/) database instance.

### 2. Clone the Repository
```bash
git clone https://github.com/PriyanshuBHardwaj20/lpi-l6.git
cd lpi-l6
```

### 3. Set Up the Virtual Environment

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named .env in the root directory of the project. Never commit this file to version control. Add your Neo4j Aura credentials:

```
NEO4J_URI=neo4j+ssc://<YOUR_DB_ID>.databases.neo4j.io
NEO4J_USERNAME=<YOUR_USERNAME>
NEO4J_PASSWORD=<YOUR_PASSWORD>
```
### 5. Seed the Knowledge Graph

Before running the dashboard, you must populate the Neo4j database with the CSV data. The seeding script creates uniqueness constraints and uses MERGE operations, making it safe to run multiple times without duplicating data.
```
python seed_graph.py
```
Run the script and wait for the "Graph seeding complete! ✅" confirmation message.

### 6. Run the Dashboard

Once the database is seeded, launch the Streamlit application:
```
streamlit run app.py
```
The dashboard will automatically open in your default web browser at http://localhost:8501.
