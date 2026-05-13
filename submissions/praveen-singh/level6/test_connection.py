from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

with driver.session() as session:
    result = session.run("RETURN 'Neo4j Connected!' AS msg")
    print(result.single()["msg"])

driver.close()