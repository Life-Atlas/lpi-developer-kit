from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv(".env")

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

production_df = pd.read_csv("factory_production.csv", dtype={"station_code": str})
workers_df = pd.read_csv("factory_workers.csv", dtype={"primary_station": str})
capacity_df = pd.read_csv("factory_capacity.csv")


with driver.session() as session:

    # =========================
    # CONSTRAINTS
    # =========================

    constraints = [
        ("Project", "project_id"),
        ("Product", "product_type"),
        ("Station", "station_code"),
        ("Worker", "worker_id"),
        ("Week", "week"),
    ]

    for label, prop in constraints:
        session.run(f"""
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (n:{label})
        REQUIRE n.{prop} IS UNIQUE
        """)

    # =========================
    # PROJECTS
    # =========================

    for _, row in production_df.iterrows():
        session.run("""
        MERGE (p:Project {project_id: $project_id})
        SET p.project_number = $project_number,
            p.project_name = $project_name
        """,
        project_id=row["project_id"],
        project_number=row["project_number"],
        project_name=row["project_name"]
        )

    # =========================
    # PRODUCTS
    # =========================

    for _, row in production_df.iterrows():
        session.run("""
        MERGE (p:Product {product_type: $product_type})
        SET p.unit = $unit
        """,
        product_type=row["product_type"],
        unit=row["unit"]
        )

    # =========================
    # STATIONS
    # =========================

    for _, row in production_df.iterrows():
        session.run("""
        MERGE (s:Station {station_code: $station_code})
        SET s.station_name = $station_name
        """,
        station_code=row["station_code"],
        station_name=row["station_name"]
        )

    # =========================
    # WEEKS
    # =========================

    for week in production_df["week"].unique():
        session.run("""
        MERGE (w:Week {week: $week})
        """, week=week)

    # =========================
    # ETAPP
    # =========================

    for etapp in production_df["etapp"].unique():
        session.run("""
        MERGE (e:Etapp {name: $etapp})
        """, etapp=etapp)

    # =========================
    # BOP
    # =========================

    for bop in production_df["bop"].unique():
        session.run("""
        MERGE (b:BOP {name: $bop})
        """, bop=bop)

    # =========================
    # WORKERS
    # =========================

    for _, row in workers_df.iterrows():
        session.run("""
        MERGE (w:Worker {worker_id: $worker_id})
        SET w.name = $name,
            w.role = $role,
            w.type = $type,
            w.hours_per_week = $hours_per_week
        """,
        worker_id=row["worker_id"],
        name=row["name"],
        role=row["role"],
        type=row["type"],
        hours_per_week=row["hours_per_week"]
        )

    # =========================
    # CERTIFICATIONS
    # =========================

    certs = set()

    for cert_list in workers_df["certifications"]:
        for cert in str(cert_list).split(","):
            certs.add(cert.strip())

    for cert in certs:
        session.run("""
        MERGE (c:Certification {name: $cert})
        """, cert=cert)

    # =========================
    # CAPACITY
    # =========================

    for _, row in capacity_df.iterrows():
        session.run("""
        MERGE (c:Capacity {week: $week})
        SET c.own_staff_count = $own_staff_count,
            c.hired_staff_count = $hired_staff_count
        """,
        week=row["week"],
        own_staff_count=row["own_staff_count"],
        hired_staff_count=row["hired_staff_count"]
        )

    # =========================
    # RELATIONSHIPS
    # =========================

    for _, row in production_df.iterrows():

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (pr:Product {product_type: $product_type})
        MERGE (p)-[r:PRODUCES]->(pr)
        SET r.quantity = $quantity,
            r.unit_factor = $unit_factor
        """,
        project_id=row["project_id"],
        product_type=row["product_type"],
        quantity=row["quantity"],
        unit_factor=row["unit_factor"]
        )

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (s:Station {station_code: $station_code})
        MERGE (p)-[r:SCHEDULED_AT {week: $week}]->(s)
        SET r.planned_hours = $planned_hours,
            r.actual_hours = $actual_hours,
            r.completed_units = $completed_units
        """,
        project_id=row["project_id"],
        station_code=row["station_code"],
        week=row["week"],
        planned_hours=row["planned_hours"],
        actual_hours=row["actual_hours"],
        completed_units=row["completed_units"]
        )

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (w:Week {week: $week})
        MERGE (p)-[:OCCURS_IN]->(w)
        """,
        project_id=row["project_id"],
        week=row["week"]
        )

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (e:Etapp {name: $etapp})
        MERGE (p)-[:PART_OF]->(e)
        """,
        project_id=row["project_id"],
        etapp=row["etapp"]
        )

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (b:BOP {name: $bop})
        MERGE (p)-[:BELONGS_TO]->(b)
        """,
        project_id=row["project_id"],
        bop=row["bop"]
        )

    # =========================
    # WORKER RELATIONSHIPS
    # =========================

    for _, row in workers_df.iterrows():

        primary = str(row["primary_station"]).zfill(3)

        if primary.lower() != "all":
            session.run("""
            MATCH (w:Worker {worker_id: $worker_id})
            MATCH (s:Station {station_code: $station})
            MERGE (w)-[:WORKS_AT]->(s)
            """,
            worker_id=row["worker_id"],
            station=primary
            )

        for station in str(row["can_cover_stations"]).split(","):
            code = station.strip()

            if code.isdigit():
                code = code.zfill(3)

                session.run("""
                MATCH (w:Worker {worker_id: $worker_id})
                MATCH (s:Station {station_code: $station})
                MERGE (w)-[:CAN_COVER]->(s)
                """,
                worker_id=row["worker_id"],
                station=code
                )

        for cert in str(row["certifications"]).split(","):
            session.run("""
            MATCH (w:Worker {worker_id: $worker_id})
            MATCH (c:Certification {name: $cert})
            MERGE (w)-[:HAS_CERTIFICATION]->(c)
            """,
            worker_id=row["worker_id"],
            cert=cert.strip()
            )

    # =========================
    # CAPACITY RELATIONSHIPS
    # =========================

    for _, row in capacity_df.iterrows():
        session.run("""
        MATCH (w:Week {week: $week})
        MATCH (c:Capacity {week: $week})
        MERGE (w)-[r:HAS_CAPACITY]->(c)
        SET r.own_hours = $own_hours,
            r.hired_hours = $hired_hours,
            r.overtime_hours = $overtime_hours,
            r.total_capacity = $total_capacity,
            r.total_planned = $total_planned,
            r.deficit = $deficit
        """,
        week=row["week"],
        own_hours=row["own_hours"],
        hired_hours=row["hired_hours"],
        overtime_hours=row["overtime_hours"],
        total_capacity=row["total_capacity"],
        total_planned=row["total_planned"],
        deficit=row["deficit"]
        )

print("Knowledge Graph Created Successfully!")
driver.close()