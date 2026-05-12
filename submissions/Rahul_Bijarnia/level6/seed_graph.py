from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

# Load environment variables
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Neo4j connection
driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# Load CSV
workers = pd.read_csv("data/factory_workers.csv")

# Create Worker + Station + Relationship
def create_worker_graph(tx, worker):

    query = """
    MERGE (w:Worker {worker_id: $worker_id})

    SET w.name = $name,
        w.role = $role,
        w.hours_per_week = $hours_per_week,
        w.type = $type

    MERGE (s:Station {station_id: $primary_station})

    MERGE (w)-[:WORKS_AT]->(s)
    """

    tx.run(
        query,
        worker_id=worker["worker_id"],
        name=worker["name"],
        role=worker["role"],
        primary_station=str(worker["primary_station"]),
        hours_per_week=worker["hours_per_week"],
        type=worker["type"]
    )

# Insert data into Neo4j
with driver.session() as session:
    for _, worker in workers.iterrows():
        session.execute_write(create_worker_graph, worker)

print("Workers and relationships inserted successfully!")

driver.close()