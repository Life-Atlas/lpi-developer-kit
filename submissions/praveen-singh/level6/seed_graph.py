import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# =========================
# LOAD ENV
# =========================

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

production_df = pd.read_csv("data/factory_production.csv")
workers_df = pd.read_csv("data/factory_workers.csv")
capacity_df = pd.read_csv("data/factory_capacity.csv")

# =========================
# SEED GRAPH
# =========================

def seed_graph():

    with driver.session() as session:

        # =====================================
        # PRODUCTION DATA
        # =====================================

        for _, row in production_df.iterrows():

            query = """
            MERGE (p:Project {
                project_id: $project_id
            })

            SET
                p.project_name = $project_name,
                p.project_number = $project_number

            MERGE (prod:Product {
                product_type: $product_type
            })

            SET
                prod.unit = $unit,
                prod.quantity = $quantity,
                prod.unit_factor = $unit_factor

            MERGE (s:Station {
                station_code: $station_code
            })

            SET
                s.station_name = $station_name

            MERGE (w:Week {
                week: $week
            })

            MERGE (p)-[:PRODUCES]->(prod)

            MERGE (p)-[:RUNS_IN]->(w)

            MERGE (p)-[r:PROCESSED_AT {
                week: $week,
                station_code: $station_code
            }]->(s)

            SET
                r.planned_hours = $planned_hours,
                r.actual_hours = $actual_hours,
                r.completed_units = $completed_units,
                r.etapp = $etapp,
                r.bop = $bop
            """

            session.run(
                query,
                {
                    "project_id": row["project_id"],
                    "project_name": row["project_name"],
                    "project_number": row["project_number"],
                    "product_type": row["product_type"],
                    "unit": row["unit"],
                    "quantity": float(row["quantity"]),
                    "unit_factor": float(row["unit_factor"]),
                    "station_code": row["station_code"],
                    "station_name": row["station_name"],
                    "week": row["week"],
                    "planned_hours": float(row["planned_hours"]),
                    "actual_hours": float(row["actual_hours"]),
                    "completed_units": float(row["completed_units"]),
                    "etapp": row["etapp"],
                    "bop": row["bop"],
                }
            )

        # =====================================
        # WORKER DATA
        # =====================================

        for _, row in workers_df.iterrows():

            query = """
            MERGE (w:Worker {
                worker_id: $worker_id
            })

            SET
                w.worker_name = $worker_name,
                w.worker_type = $worker_type,
                w.hours_per_week = $hours_per_week

            MERGE (s:Station {
                station_code: $primary_station
            })

            MERGE (w)-[:PRIMARY_AT]->(s)

            MERGE (r:Role {
                role_name: $role
            })

            MERGE (w)-[:HAS_ROLE]->(r)
            """

            session.run(
                query,
                {
                    "worker_id": row["worker_id"],
                    "worker_name": row["name"],
                    "worker_type": row["type"],
                    "hours_per_week": float(row["hours_per_week"]),
                    "primary_station": row["primary_station"],
                    "role": row["role"],
                }
            )

        # =====================================
        # CAPACITY DATA
        # =====================================

        for _, row in capacity_df.iterrows():

            query = """
            MERGE (c:CapacityWeek {
                week: $week
            })

            SET
                c.own_staff_count = $own_staff_count,
                c.hired_staff_count = $hired_staff_count,
                c.own_hours = $own_hours,
                c.hired_hours = $hired_hours,
                c.overtime_hours = $overtime_hours,
                c.total_capacity = $total_capacity,
                c.total_planned = $total_planned,
                c.deficit = $deficit
            """

            session.run(
                query,
                {
                    "week": row["week"],
                    "own_staff_count": float(row["own_staff_count"]),
                    "hired_staff_count": float(row["hired_staff_count"]),
                    "own_hours": float(row["own_hours"]),
                    "hired_hours": float(row["hired_hours"]),
                    "overtime_hours": float(row["overtime_hours"]),
                    "total_capacity": float(row["total_capacity"]),
                    "total_planned": float(row["total_planned"]),
                    "deficit": float(row["deficit"]),
                }
            )

    print("Graph seeded successfully!")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    seed_graph()
    driver.close()