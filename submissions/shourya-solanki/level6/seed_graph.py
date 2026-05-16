#!/usr/bin/env python3
"""
seed_graph.py — Factory Production Knowledge Graph
Populates Neo4j with data from 3 CSV files.
Run once: python seed_graph.py
Safe to run multiple times (uses MERGE).
"""

import os
import csv
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def load_csv(filename):
    with open(filename, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def seed(driver):
    production = load_csv("factory_production.csv")
    workers = load_csv("factory_workers.csv")
    capacity = load_csv("factory_capacity.csv")

    with driver.session() as s:
        print("Creating constraints...")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.station_code IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.worker_id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_type IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:Week) REQUIRE w.week_id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp) REQUIRE e.etapp_id IS UNIQUE")

        print("Creating Project and Station nodes...")
        for row in production:
            s.run("""
                MERGE (p:Project {project_id: $project_id})
                SET p.project_number = $project_number,
                    p.project_name = $project_name

                MERGE (st:Station {station_code: $station_code})
                SET st.station_name = $station_name

                MERGE (pr:Product {product_type: $product_type})
                SET pr.unit = $unit,
                    pr.unit_factor = toFloat($unit_factor)

                MERGE (w:Week {week_id: $week})

                MERGE (e:Etapp {etapp_id: $etapp})

                MERGE (p)-[:SCHEDULED_AT {
                    week: $week,
                    planned_hours: toFloat($planned_hours),
                    actual_hours: toFloat($actual_hours),
                    completed_units: toInteger($completed_units)
                }]->(st)

                MERGE (p)-[:PRODUCES {
                    quantity: toFloat($quantity),
                    unit_factor: toFloat($unit_factor)
                }]->(pr)

                MERGE (p)-[:IN_WEEK]->(w)
                MERGE (p)-[:HAS_ETAPP]->(e)
                MERGE (st)-[:PROCESSES]->(pr)
            """, **row)

        print("Creating Worker nodes...")
        for row in workers:
            s.run("""
                MERGE (w:Worker {worker_id: $worker_id})
                SET w.name = $name,
                    w.role = $role,
                    w.hours_per_week = toInteger($hours_per_week),
                    w.type = $type

                WITH w
                MATCH (st:Station {station_code: $primary_station})
                MERGE (w)-[:WORKS_AT]->(st)
            """, **row)

            # CAN_COVER relationships
            stations = [s.strip() for s in row["can_cover_stations"].split(",")]
            for station_code in stations:
                if station_code and station_code != "all":
                    s.run("""
                        MATCH (w:Worker {worker_id: $worker_id})
                        MATCH (st:Station {station_code: $station_code})
                        MERGE (w)-[:CAN_COVER]->(st)
                    """, worker_id=row["worker_id"], station_code=station_code.strip())

            # HAS_CERTIFICATION relationships
            certs = [c.strip() for c in row["certifications"].split(",")]
            for cert in certs:
                if cert:
                    s.run("""
                        MATCH (w:Worker {worker_id: $worker_id})
                        MERGE (c:Certification {name: $cert})
                        MERGE (w)-[:HAS_CERTIFICATION]->(c)
                    """, worker_id=row["worker_id"], cert=cert)

        print("Creating Capacity nodes...")
        for row in capacity:
            s.run("""
                MERGE (w:Week {week_id: $week})
                MERGE (cap:Capacity {week_id: $week})
                SET cap.own_hours = toInteger($own_hours),
                    cap.hired_hours = toInteger($hired_hours),
                    cap.overtime_hours = toInteger($overtime_hours),
                    cap.total_capacity = toInteger($total_capacity),
                    cap.total_planned = toInteger($total_planned),
                    cap.deficit = toInteger($deficit)
                MERGE (w)-[:HAS_CAPACITY]->(cap)
            """, **row)

    print("Graph seeded successfully.")

if __name__ == "__main__":
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    seed(driver)
    driver.close()