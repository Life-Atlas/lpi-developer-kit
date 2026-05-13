from neo4j import GraphDatabase
import pandas as pd

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

production = pd.read_csv("data/factory_production.csv")
workers = pd.read_csv("data/factory_workers.csv")
capacity = pd.read_csv("data/factory_capacity.csv")


def clear_db(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def create_production(tx, row):
    tx.run("""
        MERGE (p:Project {
            id: $project_id,
            number: $project_number,
            name: $project_name
        })

        MERGE (prod:Product {
            type: $product_type,
            unit: $unit
        })

        MERGE (s:Station {
            code: $station_code,
            name: $station_name
        })

        MERGE (w:Week {
            name: $week
        })

        MERGE (p)-[:USES_PRODUCT {
            quantity: $quantity,
            unit_factor: $unit_factor
        }]->(prod)

        MERGE (p)-[:GOES_THROUGH {
            planned_hours: $planned_hours,
            actual_hours: $actual_hours,
            completed_units: $completed_units,
            etapp: $etapp,
            bop: $bop
        }]->(s)

        MERGE (s)-[:ACTIVE_IN]->(w)
    """, **row)


def create_worker(tx, row):
    tx.run("""
        MERGE (worker:Worker {
            id: $worker_id,
            name: $name,
            role: $role,
            type: $type,
            hours_per_week: $hours_per_week
        })

        MERGE (primary:Station {
            code: $primary_station
        })

        MERGE (worker)-[:PRIMARY_AT]->(primary)
    """, **row)

    cover_list = str(row["can_cover_stations"]).split(",")

    for station in cover_list:
        tx.run("""
            MATCH (worker:Worker {id: $worker_id})
            MERGE (s:Station {code: $station})
            MERGE (worker)-[:CAN_COVER]->(s)
        """, worker_id=row["worker_id"], station=station.strip())

    certs = str(row["certifications"]).split(",")

    for cert in certs:
        tx.run("""
            MATCH (worker:Worker {id: $worker_id})
            MERGE (c:Certification {name: $cert})
            MERGE (worker)-[:HAS_CERTIFICATION]->(c)
        """, worker_id=row["worker_id"], cert=cert.strip())


def create_capacity(tx, row):
    tx.run("""
        MERGE (w:Week {name: $week})

        MERGE (cap:Capacity {
            week: $week,
            own_staff_count: $own_staff_count,
            hired_staff_count: $hired_staff_count,
            own_hours: $own_hours,
            hired_hours: $hired_hours,
            overtime_hours: $overtime_hours,
            total_capacity: $total_capacity,
            total_planned: $total_planned,
            deficit: $deficit
        })

        MERGE (w)-[:HAS_CAPACITY]->(cap)
    """, **row)


with driver.session() as session:
    print("Clearing database...")
    session.execute_write(clear_db)

    print("Loading production data...")
    for _, row in production.iterrows():
        session.execute_write(create_production, row.to_dict())

    print("Loading workers...")
    for _, row in workers.iterrows():
        session.execute_write(create_worker, row.to_dict())

    print("Loading capacity...")
    for _, row in capacity.iterrows():
        session.execute_write(create_capacity, row.to_dict())

print("Data loaded successfully.")
driver.close()
