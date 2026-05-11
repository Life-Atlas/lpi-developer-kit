Factory Workforce Dashboard
Overview
The Factory Workforce Dashboard is a graph-powered workforce analytics system built using Neo4j Aura, Python, and Streamlit.

This project models factory operations using a graph database and provides an interactive dashboard to monitor:

workforce allocation
project tracking
production relationships
factory operations analytics
The system transforms traditional CSV-based production data into a connected graph structure using Neo4j.

Problem Statement
Traditional factory production planning systems often rely on large Excel sheets and disconnected data sources. This makes it difficult to:

track worker allocation
identify overloaded resources
understand project relationships
analyze factory operations efficiently
This project solves the problem by:

converting factory datasets into a graph database
visualizing relationships between workers, stations, projects, and schedules
providing real-time dashboard insights
Features
Graph Database Integration
Uses Neo4j Aura cloud database
Stores connected factory data as graph relationships
Models workers, stations, projects, and schedules
Workforce Monitoring
Displays overworked workers
Tracks workforce allocation
Helps identify staffing imbalances
Project Analytics
Displays factory projects
Visualizes project-related graph data
Tracks project scheduling relationships
Interactive Dashboard
Built using Streamlit
Modern responsive UI
Real-time data visualization
Technologies Used
Technology	Purpose
Python	Backend logic
Neo4j Aura	Graph database
Cypher Query Language	Graph queries
Streamlit	Dashboard frontend
Pandas	CSV data handling
Git & GitHub	Version control
Graph Database Schema
The project models the following entities:

Worker
Project
Station
Week
Capacity
Relationships include:

WORKS_AT
SCHEDULED_AT
SCHEDULED_IN
Dataset Used
The dashboard uses factory production datasets provided in CSV format:

factory_workers.csv
factory_production.csv
factory_capacity.csv
These datasets contain:

worker allocation information
production schedules
station assignments
capacity planning data
Project Structure
Factory-Workforce-Dashboard/
│
├── app.py
├── queries.py
├── seed_graph.py
├── requirements.txt
├── README.md
├── .env.example
├── factory_workers.csv
├── factory_capacity.csv
├── factory_production.csv
Installation & Setup
1. Clone Repository
git clone https://github.com/g-khushi/Factory-Workforce-Dashboard.git
2. Navigate to Project
cd Factory-Workforce-Dashboard
3. Create Virtual Environment
python -m venv venv
Activate environment:

Mac/Linux
source venv/bin/activate
Windows
venv\\Scripts\\activate
4. Install Dependencies
pip install -r requirements.txt
5. Configure Environment Variables
Create a .env file:

NEO4J_URI=neo4j+s://your-database-id.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
6. Load Graph Data
python seed_graph.py
7. Run Dashboard
streamlit run app.py
Sample Cypher Queries
Display Graph Relationships
MATCH (n)-[r]->(m)
RETURN n,r,m
LIMIT 50
Get Workers
MATCH (w:Worker)
RETURN w
Get Projects
MATCH (p:Project)
RETURN p
Dashboard Preview
The dashboard includes:

workforce insights
project tracking
graph-powered analytics
Neo4j-connected visualizations
Future Improvements
Potential future enhancements:

capacity heatmaps
worker overload alerts
advanced analytics
ML-based forecasting
project scheduling optimization
role-based authentication
Learning Outcomes
Through this project, the following concepts were learned:

graph databases
Neo4j Aura
Cypher queries
Streamlit dashboard development
GitHub workflow
data visualization
graph modeling
