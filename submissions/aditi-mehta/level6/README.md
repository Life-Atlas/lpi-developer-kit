# Factory Intelligence Dashboard 

This is a Level 6 project that transforms raw CSV manufacturing data into a **Neo4j knowledge graph** and visualizes it through an interactive **Streamlit dashboard**. It includes a full predictive workload forecast utilizing linear regression.

##  Live Deployment
The live dashboard is deployed on Streamlit Cloud.  
**URL:** https://factory-dashboard-aditi-mehta.streamlit.app


---

## 🛠️ Local Setup & Run Instructions

**1. Install Dependencies** Ensure you have Python installed, then run:

```bash
pip install -r requirements.txt
```

**2. Configure Environment Variables** 

Create a `.env` file in the root directory and add your Neo4j credentials. *(Note: This file is intentionally excluded from version control for security).*

```text
NEO4J_URI=neo4j+s://your-database-id.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
```

**3. Populate the Graph Database** 

Before running the dashboard for the first time, you must build the Neo4j graph from the provided CSV data. The script uses `MERGE` statements, making it safe and idempotent to run multiple times.

```bash
python seed_graph.py
```

**4. Launch the Dashboard** 

Start the Streamlit application:

```bash
streamlit run app.py
```

---
**Author:** Aditi Mehta