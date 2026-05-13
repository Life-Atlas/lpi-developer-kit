from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# =========================
# CONNECT TO NEO4J
# =========================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

# =========================
# READ CSV FILES
# =========================

production_df = pd.read_csv("data/factory_production.csv")
workers_df = pd.read_csv("data/factory_workers.csv")
capacity_df = pd.read_csv("data/factory_capacity.csv")

# =========================
# SEED GRAPH
# =========================

with driver.session() as session:

    # =========================
    # CREATE CONSTRAINTS
    # =========================

    session.run("""
    CREATE CONSTRAINT project_id IF NOT EXISTS
    FOR (p:Project)
    REQUIRE p.project_id IS UNIQUE
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
    CREATE CONSTRAINT week_value IF NOT EXISTS
    FOR (w:Week)
    REQUIRE w.week IS UNIQUE
    """)

    session.run("""
    CREATE CONSTRAINT product_type IF NOT EXISTS
    FOR (p:Product)
    REQUIRE p.product_type IS UNIQUE
    """)

    # =========================
    # LOAD PRODUCTION DATA
    # =========================

    print("Loading production data...")

    for _, row in production_df.iterrows():

        session.run("""

        MERGE (p:Project {project_id:$project_id})
        SET p.name = $project_name,
            p.project_number = $project_number

        MERGE (prod:Product {product_type:$product_type})
        SET prod.unit = $unit

        MERGE (s:Station {station_code:$station_code})
        SET s.name = $station_name,
            s.etapp = $etapp,
            s.bop = $bop

        MERGE (w:Week {week:$week})

        MERGE (p)-[:PRODUCES {
            quantity:$quantity,
            unit_factor:$unit_factor
        }]->(prod)

        MERGE (prod)-[:PROCESSED_AT]->(s)

        MERGE (p)-[:USES_STATION {
            week:$week,
            planned_hours:$planned_hours,
            actual_hours:$actual_hours,
            completed_units:$completed_units
        }]->(s)

        MERGE (p)-[:SCHEDULED_IN]->(w)

        """,

                    project_id=row["project_id"],
                    project_name=row["project_name"],
                    project_number=row["project_number"],
                    product_type=row["product_type"],
                    unit=row["unit"],
                    quantity=row["quantity"],
                    unit_factor=row["unit_factor"],
                    station_code=row["station_code"],
                    station_name=row["station_name"],
                    etapp=row["etapp"],
                    bop=row["bop"],
                    week=row["week"],
                    planned_hours=row["planned_hours"],
                    actual_hours=row["actual_hours"],
                    completed_units=row["completed_units"]
                    )

    # =========================
    # LOAD WORKER DATA
    # =========================

    print("Loading worker data...")

    for _, row in workers_df.iterrows():

        session.run("""

        MERGE (w:Worker {worker_id:$worker_id})
        SET w.name = $name,
            w.hours_per_week = $hours_per_week

        MERGE (role:Role {name:$role})

        MERGE (etype:EmploymentType {name:$employment_type})

        MERGE (s:Station {station_code:$primary_station})

        MERGE (w)-[:HAS_ROLE]->(role)

        MERGE (w)-[:EMPLOYED_AS]->(etype)

        MERGE (w)-[:ASSIGNED_TO]->(s)

        """,

                    worker_id=row["worker_id"],
                    name=row["name"],
                    hours_per_week=row["hours_per_week"],
                    role=row["role"],
                    employment_type=row["type"],
                    primary_station=row["primary_station"]
                    )

        # =========================
        # CERTIFICATIONS
        # =========================

        certs = str(row["certifications"]).split(",")

        for cert in certs:

            cert = cert.strip()

            if cert != "" and cert.lower() != "nan":

                session.run("""

                MATCH (w:Worker {worker_id:$worker_id})

                MERGE (c:Certification {name:$cert})

                MERGE (w)-[:HAS_CERTIFICATION]->(c)

                """,

                            worker_id=row["worker_id"],
                            cert=cert
                            )

        # =========================
        # COVER STATIONS
        # =========================

        stations = str(row["can_cover_stations"]).split(",")

        for station in stations:

            station = station.strip()

            if station != "" and station.lower() != "nan":

                session.run("""

                MATCH (w:Worker {worker_id:$worker_id})

                MERGE (s:Station {station_code:$station})

                MERGE (w)-[:CAN_COVER]->(s)

                """,

                            worker_id=row["worker_id"],
                            station=station
                            )

    # =========================
    # LOAD CAPACITY DATA
    # =========================

    print("Loading capacity data...")

    for _, row in capacity_df.iterrows():

        session.run("""

        MERGE (w:Week {week:$week})

        CREATE (c:Capacity {
            own_staff_count:$own_staff_count,
            hired_staff_count:$hired_staff_count,
            own_hours:$own_hours,
            hired_hours:$hired_hours,
            overtime_hours:$overtime_hours,
            total_capacity:$total_capacity,
            total_planned:$total_planned,
            deficit:$deficit
        })

        MERGE (w)-[:HAS_CAPACITY]->(c)

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

# =========================
# CLOSE CONNECTION
# =========================

driver.close()

print("Graph successfully seeded into Neo4j.")
