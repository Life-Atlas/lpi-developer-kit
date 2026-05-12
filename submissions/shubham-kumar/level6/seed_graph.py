"""
seed_graph.py — Run once to populate Neo4j from the 3 factory CSVs.
Idempotent: uses MERGE throughout, safe to re-run.

Usage:
    python seed_graph.py
"""

import os
import csv
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

DATA_DIR = Path(__file__).parent / "data"


def get_driver():
    return GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def create_constraints(session):
    stmts = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project)         REQUIRE n.project_id   IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Station)         REQUIRE n.station_code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product)         REQUIRE n.product_type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Week)            REQUIRE n.week_id      IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Worker)          REQUIRE n.worker_id    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Certification)   REQUIRE n.name         IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Etapp)           REQUIRE n.name         IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ProductionEntry) REQUIRE n.entry_id     IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:CapacitySnapshot) REQUIRE n.week_id     IS UNIQUE",
    ]
    for stmt in stmts:
        session.run(stmt)
    print("✓ Constraints created")


def load_production(session):
    with open(DATA_DIR / "factory_production.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # --- Unique entity collections ---
    projects, stations, products, weeks, etapps = {}, {}, {}, set(), set()
    uses_product = {}

    for row in rows:
        pid = row["project_id"]
        if pid not in projects:
            projects[pid] = {
                "project_id": pid,
                "project_number": row["project_number"],
                "project_name": row["project_name"],
                "etapp": row["etapp"],
                "bop": row["bop"],
            }
        stations[row["station_code"]] = row["station_name"]
        products[row["product_type"]] = {
            "unit": row["unit"],
            "unit_factor": float(row["unit_factor"]),
        }
        weeks.add(row["week"])
        etapps.add(row["etapp"])

        key = (pid, row["product_type"])
        if key not in uses_product:
            uses_product[key] = {
                "quantity": float(row["quantity"]),
                "unit_factor": float(row["unit_factor"]),
            }

    # --- Merge static nodes ---
    for p in projects.values():
        session.run(
            """
            MERGE (n:Project {project_id: $project_id})
            SET n.project_number = $project_number,
                n.project_name   = $project_name,
                n.etapp          = $etapp,
                n.bop            = $bop
            """,
            **p,
        )

    for name in etapps:
        session.run("MERGE (n:Etapp {name: $name})", name=name)

    for p in projects.values():
        session.run(
            """
            MATCH (proj:Project {project_id: $pid})
            MATCH (e:Etapp {name: $etapp})
            MERGE (proj)-[:IN_ETAPP]->(e)
            """,
            pid=p["project_id"],
            etapp=p["etapp"],
        )

    for code, name in stations.items():
        session.run(
            "MERGE (n:Station {station_code: $code}) SET n.station_name = $name",
            code=code,
            name=name,
        )

    for pt, props in products.items():
        session.run(
            """
            MERGE (n:Product {product_type: $product_type})
            SET n.unit = $unit, n.unit_factor = $unit_factor
            """,
            product_type=pt,
            **props,
        )

    for w in weeks:
        session.run("MERGE (n:Week {week_id: $week_id})", week_id=w)

    # --- ProductionEntry nodes (one per CSV row) ---
    for row in rows:
        entry_id = f"{row['project_id']}_{row['station_code']}_{row['product_type']}_{row['week']}"
        completed = int(row["completed_units"]) if row.get("completed_units") else 0
        session.run(
            """
            MERGE (pe:ProductionEntry {entry_id: $entry_id})
            SET pe.planned_hours    = $planned_hours,
                pe.actual_hours     = $actual_hours,
                pe.completed_units  = $completed_units
            WITH pe
            MATCH (p:Project  {project_id:   $project_id})
            MATCH (s:Station  {station_code: $station_code})
            MATCH (pr:Product {product_type: $product_type})
            MATCH (w:Week     {week_id:      $week_id})
            MERGE (p)-[:HAS_ENTRY]->(pe)
            MERGE (pe)-[:AT_STATION]->(s)
            MERGE (pe)-[:FOR_PRODUCT]->(pr)
            MERGE (pe)-[:IN_WEEK]->(w)
            """,
            entry_id=entry_id,
            planned_hours=float(row["planned_hours"]),
            actual_hours=float(row["actual_hours"]),
            completed_units=completed,
            project_id=row["project_id"],
            station_code=row["station_code"],
            product_type=row["product_type"],
            week_id=row["week"],
        )

    # --- Project-level USES_PRODUCT ---
    for (pid, pt), props in uses_product.items():
        session.run(
            """
            MATCH (p:Project {project_id: $pid})
            MATCH (pr:Product {product_type: $pt})
            MERGE (p)-[r:USES_PRODUCT]->(pr)
            SET r.quantity = $quantity, r.unit_factor = $unit_factor
            """,
            pid=pid,
            pt=pt,
            **props,
        )

    print(
        f"✓ Production: {len(rows)} entries | {len(projects)} projects | "
        f"{len(stations)} stations | {len(products)} products | {len(weeks)} weeks"
    )


def load_workers(session):
    with open(DATA_DIR / "factory_workers.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        # Worker node
        session.run(
            """
            MERGE (w:Worker {worker_id: $worker_id})
            SET w.name           = $name,
                w.role           = $role,
                w.hours_per_week = $hours_per_week,
                w.type           = $type
            """,
            worker_id=row["worker_id"],
            name=row["name"],
            role=row["role"],
            hours_per_week=float(row["hours_per_week"]),
            type=row["type"],
        )

        # PRIMARY_AT (Victor Elm has primary="all" — skip)
        primary = row["primary_station"].strip()
        if primary != "all":
            session.run(
                """
                MATCH (w:Worker  {worker_id:   $worker_id})
                MATCH (s:Station {station_code: $code})
                MERGE (w)-[:PRIMARY_AT]->(s)
                """,
                worker_id=row["worker_id"],
                code=primary,
            )

        # CAN_COVER
        for code in row["can_cover_stations"].split(","):
            code = code.strip()
            if code:
                session.run(
                    """
                    MATCH (w:Worker  {worker_id:   $worker_id})
                    MATCH (s:Station {station_code: $code})
                    MERGE (w)-[:CAN_COVER]->(s)
                    """,
                    worker_id=row["worker_id"],
                    code=code,
                )

        # Certifications + HAS_CERT + REQUIRES_CERT (for primary station)
        for cert in row["certifications"].split(","):
            cert = cert.strip()
            if not cert:
                continue
            session.run("MERGE (c:Certification {name: $name})", name=cert)
            session.run(
                """
                MATCH (w:Worker {worker_id: $worker_id})
                MATCH (c:Certification {name: $name})
                MERGE (w)-[:HAS_CERT]->(c)
                """,
                worker_id=row["worker_id"],
                name=cert,
            )
            # Station inherits cert requirements from its primary worker
            if primary != "all":
                session.run(
                    """
                    MATCH (s:Station {station_code: $code})
                    MATCH (c:Certification {name: $name})
                    MERGE (s)-[:REQUIRES_CERT]->(c)
                    """,
                    code=primary,
                    name=cert,
                )

    print(f"✓ Workers: {len(rows)} loaded")


def load_capacity(session):
    with open(DATA_DIR / "factory_capacity.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        session.run(
            """
            MERGE (c:CapacitySnapshot {week_id: $week_id})
            SET c.own_staff_count   = $own_staff_count,
                c.hired_staff_count = $hired_staff_count,
                c.own_hours         = $own_hours,
                c.hired_hours       = $hired_hours,
                c.overtime_hours    = $overtime_hours,
                c.total_capacity    = $total_capacity,
                c.total_planned     = $total_planned,
                c.deficit           = $deficit
            WITH c
            MATCH (w:Week {week_id: $week_id})
            MERGE (w)-[:HAS_CAPACITY]->(c)
            """,
            week_id=row["week"],
            own_staff_count=int(row["own_staff_count"]),
            hired_staff_count=int(row["hired_staff_count"]),
            own_hours=float(row["own_hours"]),
            hired_hours=float(row["hired_hours"]),
            overtime_hours=float(row["overtime_hours"]),
            total_capacity=float(row["total_capacity"]),
            total_planned=float(row["total_planned"]),
            deficit=float(row["deficit"]),
        )

    print(f"✓ Capacity: {len(rows)} weeks loaded")


def print_summary(driver):
    with driver.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        rel_types = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"
        ).single()["c"]
    print(
        f"\n✅ Graph ready — {nodes} nodes | {rels} relationships | "
        f"{labels} node labels | {rel_types} relationship types"
    )


def main():
    if not URI or not PASSWORD:
        raise SystemExit("❌ Set NEO4J_URI and NEO4J_PASSWORD in .env first.")

    print(f"Connecting to {URI} ...")
    driver = get_driver()

    with driver.session() as session:
        create_constraints(session)
        load_production(session)
        load_workers(session)
        load_capacity(session)

    print_summary(driver)
    driver.close()


if __name__ == "__main__":
    main()
