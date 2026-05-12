from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

production_df = pd.read_csv("factory_production.csv")
workers_df = pd.read_csv("factory_workers.csv")
capacity_df = pd.read_csv("factory_capacity.csv")


def create_constraints(tx):
    tx.run("""
    CREATE CONSTRAINT project_id IF NOT EXISTS
    FOR (p:Project)
    REQUIRE p.id IS UNIQUE
    """)

    tx.run("""
    CREATE CONSTRAINT worker_id IF NOT EXISTS
    FOR (w:Worker)
    REQUIRE w.id IS UNIQUE
    """)

    tx.run("""
    CREATE CONSTRAINT station_code IF NOT EXISTS
    FOR (s:Station)
    REQUIRE s.code IS UNIQUE
    """)


def load_production(tx):
    for _, row in production_df.iterrows():

        tx.run("""
        MERGE (p:Project {id:$project_id})
        SET p.name=$project_name,
            p.project_number=$project_number

        MERGE (prod:Product {type:$product_type})
        SET prod.unit=$unit,
            prod.quantity=$quantity

        MERGE (s:Station {code:$station_code})
        SET s.name=$station_name

        MERGE (w:Week {name:$week})

        MERGE (e:Etapp {name:$etapp})

        MERGE (p)-[:USES_PRODUCT]->(prod)

        MERGE (p)-[r:SCHEDULED_AT]->(s)
        SET r.planned_hours=$planned_hours,
            r.actual_hours=$actual_hours,
            r.completed_units=$completed_units

        MERGE (p)-[:IN_WEEK]->(w)

        MERGE (p)-[:HAS_ETAPP]->(e)

        MERGE (prod)-[:PRODUCED_AT]->(s)

        MERGE (s)-[:ACTIVE_IN]->(w)
        """,
        project_id=row["project_id"],
        project_name=row["project_name"],
        project_number=row["project_number"],
        product_type=row["product_type"],
        unit=row["unit"],
        quantity=int(row["quantity"]),
        station_code=str(row["station_code"]),
        station_name=row["station_name"],
        week=row["week"],
        etapp=row["etapp"],
        planned_hours=float(row["planned_hours"]),
        actual_hours=float(row["actual_hours"]),
        completed_units=int(row["completed_units"])
        )


def load_workers(tx):
    for _, row in workers_df.iterrows():

        tx.run("""
        MERGE (w:Worker {id:$worker_id})
        SET w.name=$name,
            w.role=$role,
            w.hours_per_week=$hours_per_week,
            w.type=$type

        MERGE (s:Station {code:$primary_station})

        MERGE (w)-[:WORKS_AT]->(s)
        """,
        worker_id=row["worker_id"],
        name=row["name"],
        role=row["role"],
        hours_per_week=int(row["hours_per_week"]),
        type=row["type"],
        primary_station=str(row["primary_station"])
        )

        cover_stations = str(row["can_cover_stations"]).split(",")

        for station in cover_stations:
            tx.run("""
            MERGE (w:Worker {id:$worker_id})
            MERGE (s:Station {code:$station})

            MERGE (w)-[:CAN_COVER]->(s)
            """,
            worker_id=row["worker_id"],
            station=station.strip()
            )

        certs = str(row["certifications"]).split(",")

        for cert in certs:
            tx.run("""
            MERGE (w:Worker {id:$worker_id})

            MERGE (c:Certification {name:$cert})

            MERGE (w)-[:CERTIFIED_FOR]->(c)
            """,
            worker_id=row["worker_id"],
            cert=cert.strip()
            )


def load_capacity(tx):
    for _, row in capacity_df.iterrows():

        tx.run("""
        MERGE (w:Week {name:$week})

        MERGE (c:Capacity {week:$week})

        SET c.own_staff_count=$own_staff_count,
            c.hired_staff_count=$hired_staff_count,
            c.own_hours=$own_hours,
            c.hired_hours=$hired_hours,
            c.overtime_hours=$overtime_hours,
            c.total_capacity=$total_capacity,
            c.total_planned=$total_planned,
            c.deficit=$deficit

        MERGE (w)-[:HAS_CAPACITY]->(c)
        """,
        week=row["week"],
        own_staff_count=int(row["own_staff_count"]),
        hired_staff_count=int(row["hired_staff_count"]),
        own_hours=int(row["own_hours"]),
        hired_hours=int(row["hired_hours"]),
        overtime_hours=int(row["overtime_hours"]),
        total_capacity=int(row["total_capacity"]),
        total_planned=int(row["total_planned"]),
        deficit=int(row["deficit"])
        )


with driver.session() as session:

    session.execute_write(create_constraints)

    session.execute_write(load_production)

    session.execute_write(load_workers)

    session.execute_write(load_capacity)

print("Graph seeded successfully!")

driver.close()