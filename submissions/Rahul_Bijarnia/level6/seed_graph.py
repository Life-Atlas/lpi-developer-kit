from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

workers = pd.read_csv(
    "data/factory_workers.csv",
    dtype=str
)

def create_worker_graph(tx, worker):

    query = """

    MERGE (w:Worker {
        worker_id: $worker_id
    })

    SET
        w.name = $name,
        w.role = $role,
        w.hours_per_week = $hours_per_week

    MERGE (s:Station {
        station_id: $primary_station
    })

    MERGE (w)-[:WORKS_AT]->(s)

    """

    tx.run(
        query,

        worker_id=worker["worker_id"],
        name=worker["name"],
        role=worker["role"],
        primary_station=worker["primary_station"],
        hours_per_week=worker["hours_per_week"]
    )

with driver.session() as session:

    for _, worker in workers.iterrows():

        session.execute_write(
            create_worker_graph,
            worker
        )

print("Graph Seeded Successfully!")

driver.close()