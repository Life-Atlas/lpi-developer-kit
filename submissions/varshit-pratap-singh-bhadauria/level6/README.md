# Level 6: Factory Knowledge Graph Dashboard

This project is a Streamlit dashboard powered by a Neo4j knowledge graph. It replaces a 46-sheet Excel workbook for a steel fabrication company.

## Files Included:
- `seed_graph.py`: Standalone, idempotent script used to parse CSV data and populate the Neo4j Aura cloud database.
- `app.py`: The Streamlit application containing the dashboard UI and Cypher queries. 
- `DASHBOARD_URL.txt`: Contains the public link to the deployed Streamlit Cloud dashboard.

## Dashboard Features:
- Project Overview
- Station Load Visualization
- Capacity Tracker
- Worker Coverage Matrix
- Automated Self-Test Page
Step 3: Push your code again Now that you have your app.py, seed_graph.py, DASHBOARD_URL.txt, and your new README.md, you can run those git commands safely:
git add app.py
git add seed_graph.py
git add DASHBOARD_URL.txt
git add README.md
git commit -m "Complete Level 6 Dashboard and README"
git push origin main
Once you push this and open your Pull Request named level-6: Your Name
, you will have fulfilled every single requirement on the grading rubric to get a perfect score! Let me know if you run into any issues creating the PR.