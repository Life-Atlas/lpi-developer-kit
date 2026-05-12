from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

production = pd.read_csv("../../../challenges/data/factory_production.csv")
workers = pd.read_csv("../../../challenges/data/factory_workers.csv")
capacity = pd.read_csv("../../../challenges/data/factory_capacity.csv")

def create_constraints(tx):
    tx.run("CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT worker_id IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT station_code IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE")

def seed_projects(tx):
    for _, row in production.iterrows():

        tx.run("""
        MERGE (p:Project {id:$project_id})
        SET p.name = $project_name,
            p.number = $project_number

        MERGE (prod:Product {type:$product_type})

        MERGE (s:Station {code:$station_code})
        SET s.name = $station_name

        MERGE (w:Week {name:$week})

        MERGE (e:Etapp {name:$etapp})

        MERGE (p)-[:PRODUCES {
            quantity:$quantity,
            unit:$unit,
            unit_factor:$unit_factor
        }]->(prod)

        MERGE (p)-[:SCHEDULED_AT {
            planned_hours:$planned_hours,
            actual_hours:$actual_hours,
            completed_units:$completed_units,
            week:$week
        }]->(s)

        MERGE (prod)-[:PROCESSED_AT]->(s)
        MERGE (s)-[:ACTIVE_IN]->(w)
        MERGE (p)-[:IN_WEEK]->(w)
        MERGE (p)-[:PART_OF]->(e)
        """,
        project_id=row["project_id"],
        project_name=row["project_name"],
        project_number=row["project_number"],
        product_type=row["product_type"],
        quantity=float(row["quantity"]),
        unit=row["unit"],
        unit_factor=float(row["unit_factor"]),
        station_code=row["station_code"],
        station_name=row["station_name"],
        week=row["week"],
        planned_hours=float(row["planned_hours"]),
        actual_hours=float(row["actual_hours"]),
        completed_units=int(row["completed_units"]),
        etapp=row["etapp"]
        )

def seed_workers(tx):
    for _, row in workers.iterrows():

        tx.run("""
        MERGE (w:Worker {id:$worker_id})
        SET w.name = $name,
            w.role = $role,
            w.type = $type,
            w.hours_per_week = $hours_per_week

        MERGE (s:Station {code:$primary_station})

        MERGE (w)-[:WORKS_AT]->(s)
        """,
        worker_id=row["worker_id"],
        name=row["name"],
        role=row["role"],
        type=row["type"],
        hours_per_week=int(row["hours_per_week"]),
        primary_station=row["primary_station"]
        )

def seed_capacity(tx):
    for _, row in capacity.iterrows():

        tx.run("""
        MERGE (w:Week {name:$week})

        MERGE (c:Capacity {week:$week})
        SET c.total_capacity = $total_capacity,
            c.total_planned = $total_planned,
            c.deficit = $deficit

        MERGE (w)-[:HAS_CAPACITY]->(c)
        """,
        week=row["week"],
        total_capacity=float(row["total_capacity"]),
        total_planned=float(row["total_planned"]),
        deficit=float(row["deficit"])
        )

with driver.session() as session:

    session.execute_write(create_constraints)

    session.execute_write(seed_projects)

    session.execute_write(seed_workers)

    session.execute_write(seed_capacity)

print("Graph seeded successfully!")

driver.close()