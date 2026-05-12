from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

with driver.session() as session:

    # Projects
    for i in range(1, 9):
        session.run("""
        MERGE (p:Project {id:$id})
        SET p.name=$name
        """, id=i, name=f"Project {i}")

    # Stations
    for i in range(1, 10):
        session.run("""
        MERGE (s:Station {id:$id})
        SET s.name=$name
        """, id=i, name=f"Station {i}")

    # Workers
    for i in range(1, 14):
        session.run("""
        MERGE (w:Worker {id:$id})
        SET w.name=$name
        """, id=i, name=f"Worker {i}")

    # Weeks
    for i in range(1, 9):
        session.run("""
        MERGE (wk:Week {id:$id})
        """, id=i)

    # Relationships
    for i in range(1, 9):
        session.run("""
        MATCH (p:Project {id:$pid})
        MATCH (s:Station {id:$sid})
        MERGE (p)-[r:SCHEDULED_AT]->(s)
        SET r.planned_hours=100,
            r.actual_hours=120
        """, pid=i, sid=(i % 9) + 1)

print("Graph Created Successfully!")

driver.close()