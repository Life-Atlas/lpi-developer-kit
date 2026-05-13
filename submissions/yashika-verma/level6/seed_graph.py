from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

# =========================
# LOAD CSV FILES
# =========================

production_df = pd.read_csv(
    "data/factory_production.csv"
)

workers_df = pd.read_csv(
    "data/factory_workers.csv"
)

capacity_df = pd.read_csv(
    "data/factory_capacity.csv"
)

# =========================
# CREATE CONSTRAINTS
# =========================

def create_constraints(tx):

    tx.run("""
    CREATE CONSTRAINT project_id IF NOT EXISTS
    FOR (p:Project)
    REQUIRE p.id IS UNIQUE
    """)

    tx.run("""
    CREATE CONSTRAINT station_code IF NOT EXISTS
    FOR (s:Station)
    REQUIRE s.code IS UNIQUE
    """)

    tx.run("""
    CREATE CONSTRAINT worker_id IF NOT EXISTS
    FOR (w:Worker)
    REQUIRE w.id IS UNIQUE
    """)

# =========================
# LOAD PRODUCTION DATA
# =========================

def load_production(tx):

    for _, row in production_df.iterrows():

        variance = 0

        if row["planned_hours"] > 0:

            variance = (
                (
                    row["actual_hours"]
                    - row["planned_hours"]
                )
                / row["planned_hours"]
            ) * 100

        tx.run("""
        MERGE (p:Project {
            id: $project_id
        })

        MERGE (prod:Product {
            name: $product
        })

        MERGE (s:Station {
            code: $station_code
        })

        SET s.name = $station_name

        MERGE (w:Week {
            name: $week
        })

        MERGE (e:Etapp {
            name: $etapp
        })

        MERGE (p)-[:PRODUCES]->(prod)

        MERGE (prod)-[:PROCESSED_AT]->(s)

        MERGE (p)-[:USES_STATION]->(s)

        MERGE (p)-[:PART_OF_ETAPP]->(e)

        MERGE (p)-[:SCHEDULED_IN]->(w)

        MERGE (p)-[r:SCHEDULED_AT {
            week: $week
        }]->(s)

        SET r.planned_hours = $planned_hours,
            r.actual_hours = $actual_hours,
            r.variance_percent = $variance,
            r.overloaded = $variance > 3
        """,
        project_id=row["project_id"],
        product=row["product_type"],
        station_code=row["station_code"],
        station_name=row["station_name"],
        week=row["week"],
        etapp=row["etapp"],
        planned_hours=float(row["planned_hours"]),
        actual_hours=float(row["actual_hours"]),
        variance=round(variance, 2)
        )

# =========================
# LOAD WORKERS
# =========================

def load_workers(tx):

    for _, row in workers_df.iterrows():

        tx.run("""
        MERGE (w:Worker {
            id: $worker_id
        })

        SET w.name = $worker_name,
            w.role = $role,
            w.hours_per_week = $hours_per_week,
            w.type = $worker_type

        MERGE (s:Station {
            name: $primary_station
        })

        MERGE (w)-[:WORKS_AT]->(s)
        """,
        worker_id=row["worker_id"],
        worker_name=row["name"],
        role=row["role"],
        hours_per_week=float(row["hours_per_week"]),
        worker_type=row["type"],
        primary_station=row["primary_station"]
        )

        # CAN COVER STATIONS

        if pd.notna(row["can_cover_stations"]):

            stations = str(
                row["can_cover_stations"]
            ).split(",")

            for station in stations:

                tx.run("""
                MERGE (w:Worker {
                    id: $worker_id
                })

                MERGE (s:Station {
                    name: $station_name
                })

                MERGE (w)-[:CAN_COVER]->(s)
                """,
                worker_id=row["worker_id"],
                station_name=station.strip()
                )

        # CERTIFICATIONS

        if pd.notna(row["certifications"]):

            certs = str(
                row["certifications"]
            ).split(",")

            for cert in certs:

                tx.run("""
                MERGE (w:Worker {
                    id: $worker_id
                })

                MERGE (c:Certification {
                    name: $cert_name
                })

                MERGE (w)-[:HAS_CERTIFICATION]->(c)
                """,
                worker_id=row["worker_id"],
                cert_name=cert.strip()
                )

        # EXTRA RELATIONSHIP TYPE

        tx.run("""
        MATCH (p:Project)
        WITH p LIMIT 1

        MERGE (w:Worker {
            id: $worker_id
        })

        MERGE (w)-[:ASSIGNED_TO]->(p)
        """,
        worker_id=row["worker_id"]
        )

# =========================
# LOAD CAPACITY
# =========================

def load_capacity(tx):

    for _, row in capacity_df.iterrows():

        tx.run("""
        MERGE (w:Week {
            name: $week
        })

        SET w.own_staff_count = $own_staff,
            w.hired_staff_count = $hired_staff,
            w.overtime_hours = $overtime,
            w.total_capacity = $total_capacity,
            w.total_planned = $total_planned,
            w.deficit = $deficit
        """,
        week=row["week"],
        own_staff=int(row["own_staff_count"]),
        hired_staff=int(row["hired_staff_count"]),
        overtime=float(row["overtime_hours"]),
        total_capacity=float(row["total_capacity"]),
        total_planned=float(row["total_planned"]),
        deficit=float(row["deficit"])
        )

# =========================
# EXECUTE LOAD
# =========================

with driver.session() as session:

    session.execute_write(
        create_constraints
    )

    session.execute_write(
        load_production
    )

    session.execute_write(
        load_workers
    )

    session.execute_write(
        load_capacity
    )

print("Graph successfully loaded!")