from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

# Load environment variables
load_dotenv(".env")

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Fix SSL certificate issue
URI = URI.replace("neo4j+s://", "neo4j+ssc://")

# Connect Neo4j
driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# Load CSV files
production_df = pd.read_csv("factory_production.csv")
workers_df = pd.read_csv("factory_workers.csv")
capacity_df = pd.read_csv("factory_capacity.csv")

# Neo4j Session
with driver.session() as session:

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    session.run("""
    CREATE CONSTRAINT project_id IF NOT EXISTS
    FOR (p:Project)
    REQUIRE p.project_id IS UNIQUE
    """)

    session.run("""
    CREATE CONSTRAINT product_name IF NOT EXISTS
    FOR (p:Product)
    REQUIRE p.product_type IS UNIQUE
    """)

    session.run("""
    CREATE CONSTRAINT station_code IF NOT EXISTS
    FOR (s:Station)
    REQUIRE s.station_code IS UNIQUE
    """)

    session.run("""
    CREATE CONSTRAINT worker_id IF NOT EXISTS
    FOR (w:Worker)
    REQUIRE w.worker_id IS UNIQUE
    """)

    session.run("""
    CREATE CONSTRAINT week_name IF NOT EXISTS
    FOR (w:Week)
    REQUIRE w.week IS UNIQUE
    """)

    # =========================================================
    # PROJECT NODES
    # =========================================================

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

    # =========================================================
    # PRODUCT NODES
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MERGE (p:Product {product_type: $product_type})

        SET p.unit = $unit
        """,
        product_type=row["product_type"],
        unit=row["unit"]
        )

    # =========================================================
    # STATION NODES
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MERGE (s:Station {station_code: $station_code})

        SET s.station_name = $station_name
        """,
        station_code=row["station_code"],
        station_name=row["station_name"]
        )

    # =========================================================
    # WEEK NODES
    # =========================================================

    for week in production_df["week"].unique():

        session.run("""
        MERGE (w:Week {week: $week})
        """,
        week=week
        )

    # =========================================================
    # ETAPP NODES
    # =========================================================

    for etapp in production_df["etapp"].unique():

        session.run("""
        MERGE (e:Etapp {name: $etapp})
        """,
        etapp=etapp
        )

    # =========================================================
    # BOP NODES
    # =========================================================

    for bop in production_df["bop"].unique():

        session.run("""
        MERGE (b:BOP {name: $bop})
        """,
        bop=bop
        )

    # =========================================================
    # WORKER NODES
    # =========================================================

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

    # =========================================================
    # CERTIFICATION NODES
    # =========================================================

    certifications = set()

    for certs in workers_df["certifications"]:

        for cert in certs.split(","):
            certifications.add(cert.strip())

    for cert in certifications:

        session.run("""
        MERGE (c:Certification {name: $cert})
        """,
        cert=cert
        )

    # =========================================================
    # CAPACITY NODES
    # =========================================================

    for _, row in capacity_df.iterrows():

        session.run("""
        MERGE (c:Capacity {week: $week})

        SET c.own_staff_count = $own_staff_count,
            c.hired_staff_count = $hired_staff_count,
            c.own_hours = $own_hours,
            c.hired_hours = $hired_hours,
            c.overtime_hours = $overtime_hours,
            c.total_capacity = $total_capacity,
            c.total_planned = $total_planned,
            c.deficit = $deficit
        """,
        week=row["week"],
        own_staff_count=row["own_staff_count"],
        hired_staff_count=row["hired_staff_count"],
        own_hours=row["own_hours"],
        hired_hours=row["hired_hours"],
        overtime_hours=row["overtime_hours"],
        total_capacity=row["total_capacity"],
        total_planned=row["total_planned"],
        deficit=row["deficit"]
        )

    # =========================================================
    # PRODUCES RELATIONSHIP
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (pr:Product {product_type: $product_type})

        MERGE (p)-[r:PRODUCES]->(pr)

        SET r.qty = $quantity,
            r.unit_factor = $unit_factor
        """,
        project_id=row["project_id"],
        product_type=row["product_type"],
        quantity=row["quantity"],
        unit_factor=row["unit_factor"]
        )

    # =========================================================
    # SCHEDULED_AT RELATIONSHIP
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (s:Station {station_code: $station_code})

        MERGE (p)-[r:SCHEDULED_AT {
            week: $week
        }]->(s)

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

    # =========================================================
    # OCCURS_IN RELATIONSHIP
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MATCH (p:Project {project_id: $project_id})
        MATCH (w:Week {week: $week})

        MERGE (p)-[:OCCURS_IN]->(w)
        """,
        project_id=row["project_id"],
        week=row["week"]
        )

    # =========================================================
    # PART_OF RELATIONSHIP
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MATCH (pr:Product {product_type: $product_type})
        MATCH (e:Etapp {name: $etapp})

        MERGE (pr)-[:PART_OF]->(e)
        """,
        product_type=row["product_type"],
        etapp=row["etapp"]
        )

    # =========================================================
    # BELONGS_TO RELATIONSHIP
    # =========================================================

    for _, row in production_df.iterrows():

        session.run("""
        MATCH (e:Etapp {name: $etapp})
        MATCH (b:BOP {name: $bop})

        MERGE (e)-[:BELONGS_TO]->(b)
        """,
        etapp=row["etapp"],
        bop=row["bop"]
        )

    # =========================================================
    # WORKS_AT RELATIONSHIP
    # =========================================================

    for _, row in workers_df.iterrows():

        station_code = int(row["primary_station"]) if row["primary_station"] != "all" else None

        if station_code:

            session.run("""
            MATCH (w:Worker {worker_id: $worker_id})
            MATCH (s:Station {station_code: $station})

            MERGE (w)-[:WORKS_AT]->(s)
            """,
            worker_id=row["worker_id"],
            station=station_code
            )

    # =========================================================
    # CAN_COVER RELATIONSHIP
    # =========================================================

    for _, row in workers_df.iterrows():

        stations = str(row["can_cover_stations"]).split(",")

        for station in stations:

            station = station.strip()

            if station.isdigit():

                station_code = int(station)

                session.run("""
                MATCH (w:Worker {worker_id: $worker_id})
                MATCH (s:Station {station_code: $station})

                MERGE (w)-[:CAN_COVER]->(s)
                """,
                worker_id=row["worker_id"],
                station=station_code
                )

    # =========================================================
    # HAS_CERTIFICATION RELATIONSHIP
    # =========================================================

    for _, row in workers_df.iterrows():

        certs = str(row["certifications"]).split(",")

        for cert in certs:

            session.run("""
            MATCH (w:Worker {worker_id: $worker_id})
            MATCH (c:Certification {name: $cert})

            MERGE (w)-[:HAS_CERTIFICATION]->(c)
            """,
            worker_id=row["worker_id"],
            cert=cert.strip()
            )

    # =========================================================
    # HAS_CAPACITY RELATIONSHIP
    # =========================================================

    for _, row in capacity_df.iterrows():

        session.run("""
        MATCH (w:Week {week: $week})
        MATCH (c:Capacity {week: $week})

        MERGE (w)-[r:HAS_CAPACITY]->(c)

        SET r.deficit = $deficit,
            r.overtime = $overtime
        """,
        week=row["week"],
        deficit=row["deficit"],
        overtime=row["overtime_hours"]
        )

print("Knowledge Graph Created Successfully!")

driver.close()