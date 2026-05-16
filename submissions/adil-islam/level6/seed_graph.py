import pandas as pd
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def load_data(file):
    if not os.path.exists(file):
        print(f"❌ Error: File '{file}' not found.")
        return None

    df = pd.read_csv(file)

    # Remove hidden spaces from column names
    df.columns = df.columns.str.strip()

    print(f"✅ Loaded {file}: {len(df)} rows.")

    return df


# Load DataFrames
production_df = load_data("factory_production.csv")
workers_df = load_data("factory_workers.csv")
capacity_df = load_data("factory_capacity.csv")


def create_constraints(tx):

    queries = [
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",

        "CREATE CONSTRAINT station_code IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE",

        "CREATE CONSTRAINT worker_name IF NOT EXISTS FOR (w:Worker) REQUIRE w.name IS UNIQUE",

        "CREATE CONSTRAINT week_name IF NOT EXISTS FOR (w:Week) REQUIRE w.name IS UNIQUE",
    ]

    for q in queries:
        tx.run(q)


def seed_production(tx):

    for _, row in tqdm(
        production_df.iterrows(),
        total=len(production_df),
        desc="Seeding Production"
    ):

        tx.run(
            """
            MERGE (p:Project {id:$project_id})
            SET p.name = $project_name

            MERGE (prod:Product {name:$product_type})

            MERGE (s:Station {code:$station_code})
            SET s.name = $station_name

            MERGE (w:Week {name:$week})

            MERGE (e:Etapp {name:$etapp})

            MERGE (p)-[:PRODUCES {
                qty:$quantity,
                unit_factor:$unit_factor
            }]->(prod)

            MERGE (p)-[r:SCHEDULED_AT {
                week:$week
            }]->(s)

            SET r.planned_hours = $planned_hours,
                r.actual_hours = $actual_hours

            MERGE (p)-[:PART_OF]->(e)

            MERGE (p)-[:RUNS_IN]->(w)
            """,

            project_id=str(row["project_id"]),
            project_name=row["project_name"],
            product_type=row["product_type"],
            station_code=str(row["station_code"]),
            station_name=row["station_name"],
            week=row["week"],
            etapp=row["etapp"],
            quantity=float(row["quantity"]),
            unit_factor=float(row["unit_factor"]),
            planned_hours=float(row["planned_hours"]),
            actual_hours=float(row["actual_hours"])
        )

        # Create overload relationship
        if float(row["actual_hours"]) > float(row["planned_hours"]) * 1.1:

            tx.run(
                """
                MATCH (s:Station {code:$station_code})
                MATCH (w:Week {name:$week})

                MERGE (s)-[:OVERLOADED_IN]->(w)
                """,

                station_code=str(row["station_code"]),
                week=row["week"]
            )


def seed_workers(tx):

    for _, row in tqdm(
        workers_df.iterrows(),
        total=len(workers_df),
        desc="Seeding Workers"
    ):

        tx.run(
            """
            MERGE (w:Worker {name:$name})
            SET w.role = $role

            MERGE (s:Station {code:$station})

            MERGE (w)-[:WORKS_AT]->(s)

            MERGE (w)-[:CAN_COVER]->(s)
            """,

            name=row["name"],
            role=row["role"],
            station=str(row["primary_station"])
        )


def seed_capacity(tx):

    for _, row in tqdm(
        capacity_df.iterrows(),
        total=len(capacity_df),
        desc="Seeding Capacity"
    ):

        tx.run(
            """
            MERGE (w:Week {name:$week})

            MERGE (c:Capacity {week:$week})

            SET c.own = $own,
                c.hired = $hired,
                c.overtime = $overtime,
                c.demand = $demand,
                c.deficit = $deficit

            MERGE (w)-[:HAS_CAPACITY]->(c)
            """,

            week=row["week"],
            own=float(row["own_hours"]),
            hired=float(row["hired_hours"]),
            overtime=float(row["overtime_hours"]),
            demand=float(row["total_planned"]),
            deficit=float(row["deficit"])
        )


# Main Execution
try:

    with driver.session() as session:

        print("\n--- Starting Database Operations ---")

        session.execute_write(create_constraints)

        if production_df is not None:
            session.execute_write(seed_production)

        if workers_df is not None:
            session.execute_write(seed_workers)

        if capacity_df is not None:
            session.execute_write(seed_capacity)

    print("\n✅ Graph seeded successfully!")

except Exception as e:

    print(f"\n🛑 Error: {e}")

finally:

    driver.close()