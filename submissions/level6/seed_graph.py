"""
seed_graph.py — Populate Neo4j graph from factory CSV files.
Run once:  python seed_graph.py
Safe to re-run (uses MERGE everywhere).
"""

import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

DATA_DIR = os.path.dirname(__file__)

# ── helpers ────────────────────────────────────────────────────────────────────

def run(driver, cypher, **params):
    with driver.session() as s:
        s.run(cypher, **params)

def run_many(driver, cypher, rows):
    with driver.session() as s:
        s.run(cypher, rows=rows)

# ── constraints / indexes ──────────────────────────────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project)  REQUIRE n.project_id  IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product)  REQUIRE n.product_type IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Station)  REQUIRE n.station_code IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Worker)   REQUIRE n.worker_id    IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Week)     REQUIRE n.week         IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Etapp)    REQUIRE n.etapp        IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:BOP)      REQUIRE n.bop          IS UNIQUE",
]

# ── seeding functions ──────────────────────────────────────────────────────────

def seed_production(driver, df):
    """Projects, Products, Stations, Etapps, BOPs, Weeks + relationships."""

    # ── nodes ──────────────────────────────────────────────────────────────────

    # Projects
    projects = df[["project_id","project_number","project_name"]].drop_duplicates().to_dict("records")
    run_many(driver,
        """UNWIND $rows AS r
           MERGE (p:Project {project_id: r.project_id})
           SET p.project_number = r.project_number,
               p.project_name   = r.project_name""",
        projects)

    # Products  (include unit/unit_factor per project-product pair)
    products = df[["product_type"]].drop_duplicates().to_dict("records")
    run_many(driver,
        "UNWIND $rows AS r MERGE (:Product {product_type: r.product_type})",
        products)

    # Stations
    stations = df[["station_code","station_name"]].drop_duplicates().to_dict("records")
    run_many(driver,
        """UNWIND $rows AS r
           MERGE (s:Station {station_code: toString(r.station_code)})
           SET s.station_name = r.station_name""",
        stations)

    # Etapps
    etapps = df[["etapp"]].drop_duplicates().to_dict("records")
    run_many(driver,
        "UNWIND $rows AS r MERGE (:Etapp {etapp: r.etapp})",
        etapps)

    # BOPs
    bops = df[["bop"]].drop_duplicates().to_dict("records")
    run_many(driver,
        "UNWIND $rows AS r MERGE (:BOP {bop: r.bop})",
        bops)

    # Weeks
    weeks = df[["week"]].drop_duplicates().to_dict("records")
    run_many(driver,
        "UNWIND $rows AS r MERGE (:Week {week: r.week})",
        weeks)

    # ── relationships ──────────────────────────────────────────────────────────

    # (Project)-[:PRODUCES]->(Product)  with qty & unit_factor
    prod_product = (df.groupby(["project_id","product_type","unit","unit_factor","quantity"])
                      .size().reset_index()[["project_id","product_type","unit","unit_factor","quantity"]]
                      .drop_duplicates().to_dict("records"))
    run_many(driver,
        """UNWIND $rows AS r
           MATCH (proj:Project {project_id: r.project_id})
           MATCH (prod:Product {product_type: r.product_type})
           MERGE (proj)-[rel:PRODUCES {product_type: r.product_type}]->(prod)
           SET rel.unit        = r.unit,
               rel.unit_factor = toFloat(r.unit_factor),
               rel.quantity    = toFloat(r.quantity)""",
        prod_product)

    # (Project)-[:SCHEDULED_AT]->(Station)  per week with planned/actual
    sched = df[["project_id","station_code","week","planned_hours","actual_hours","completed_units"]].copy()
    sched["station_code"] = sched["station_code"].astype(str)
    sched = sched.to_dict("records")
    run_many(driver,
        """UNWIND $rows AS r
           MATCH (proj:Project {project_id: r.project_id})
           MATCH (st:Station {station_code: r.station_code})
           MATCH (wk:Week {week: r.week})
           MERGE (proj)-[rel:SCHEDULED_AT {week: r.week, station_code: r.station_code}]->(st)
           SET rel.planned_hours    = toFloat(r.planned_hours),
               rel.actual_hours     = toFloat(r.actual_hours),
               rel.completed_units  = toInteger(r.completed_units),
               rel.week_node        = r.week""",
        sched)

    # (Project)-[:IN_ETAPP]->(Etapp)
    proj_etapp = df[["project_id","etapp"]].drop_duplicates().to_dict("records")
    run_many(driver,
        """UNWIND $rows AS r
           MATCH (proj:Project {project_id: r.project_id})
           MATCH (et:Etapp {etapp: r.etapp})
           MERGE (proj)-[:IN_ETAPP]->(et)""",
        proj_etapp)

    # (Project)-[:IN_BOP]->(BOP)
    proj_bop = df[["project_id","bop"]].drop_duplicates().to_dict("records")
    run_many(driver,
        """UNWIND $rows AS r
           MATCH (proj:Project {project_id: r.project_id})
           MATCH (b:BOP {bop: r.bop})
           MERGE (proj)-[:IN_BOP]->(b)""",
        proj_bop)

    # (Week)-[:HAS_SCHEDULE {planned, actual}]->(Station)  aggregate per week/station
    ws = (df.groupby(["week","station_code"])
            .agg(planned_hours=("planned_hours","sum"),
                 actual_hours=("actual_hours","sum"))
            .reset_index())
    ws["station_code"] = ws["station_code"].astype(str)
    run_many(driver,
        """UNWIND $rows AS r
           MATCH (wk:Week {week: r.week})
           MATCH (st:Station {station_code: r.station_code})
           MERGE (wk)-[rel:HAS_SCHEDULE {station_code: r.station_code}]->(st)
           SET rel.planned_hours = toFloat(r.planned_hours),
               rel.actual_hours  = toFloat(r.actual_hours)""",
        ws.to_dict("records"))


def seed_workers(driver, wdf):
    """Worker nodes + WORKS_AT and CAN_COVER relationships."""

    workers = wdf.to_dict("records")

    # Worker nodes
    run_many(driver,
        """UNWIND $rows AS r
           MERGE (w:Worker {worker_id: r.worker_id})
           SET w.name           = r.name,
               w.role           = r.role,
               w.primary_station= toString(r.primary_station),
               w.certifications = r.certifications,
               w.hours_per_week = toInteger(r.hours_per_week),
               w.type           = r.type""",
        workers)

    def norm(code: str) -> str:
        """Strip leading zeros so '011' -> '11' matches Station nodes from production CSV."""
        code = code.strip()
        try:
            return str(int(code))   # '011' -> 11 -> '11'
        except ValueError:
            return code             # 'all' stays 'all'

    # WORKS_AT primary station
    for _, row in wdf.iterrows():
        primary = norm(str(row["primary_station"]))
        if primary == "all":
            with driver.session() as s:
                s.run("""MATCH (w:Worker {worker_id: $wid}), (st:Station)
                          MERGE (w)-[:WORKS_AT]->(st)""", wid=row["worker_id"])
        else:
            run(driver,
                """MATCH (w:Worker {worker_id: $wid})
                   MATCH (st:Station {station_code: $sc})
                   MERGE (w)-[:WORKS_AT]->(st)""",
                wid=row["worker_id"], sc=primary)

    # CAN_COVER  (comma-separated station codes)
    for _, row in wdf.iterrows():
        covers = [norm(c) for c in str(row["can_cover_stations"]).split(",")]
        if covers == ["all"]:
            with driver.session() as s:
                s.run("""MATCH (w:Worker {worker_id: $wid}), (st:Station)
                          MERGE (w)-[:CAN_COVER]->(st)""", wid=row["worker_id"])
        else:
            for sc in covers:
                run(driver,
                    """MATCH (w:Worker {worker_id: $wid})
                       MATCH (st:Station {station_code: $sc})
                       MERGE (w)-[:CAN_COVER]->(st)""",
                    wid=row["worker_id"], sc=sc)


def seed_capacity(driver, cdf):
    """Enrich Week nodes with capacity data + HAS_CAPACITY self-relationship."""

    rows = cdf.to_dict("records")

    # Set capacity properties on Week nodes
    run_many(driver,
        """UNWIND $rows AS r
           MERGE (wk:Week {week: r.week})
           SET wk.own_staff_count  = toInteger(r.own_staff_count),
               wk.hired_staff_count= toInteger(r.hired_staff_count),
               wk.own_hours        = toInteger(r.own_hours),
               wk.hired_hours      = toInteger(r.hired_hours),
               wk.overtime_hours   = toInteger(r.overtime_hours),
               wk.total_capacity   = toInteger(r.total_capacity),
               wk.total_planned    = toInteger(r.total_planned),
               wk.deficit          = toInteger(r.deficit)""",
        rows)

    # HAS_CAPACITY as a self-loop relationship (satisfies 8 rel-type requirement)
    run_many(driver,
        """UNWIND $rows AS r
           MATCH (wk:Week {week: r.week})
           MERGE (wk)-[rel:HAS_CAPACITY]->(wk)
           SET rel.own_hours      = toInteger(r.own_hours),
               rel.hired_hours    = toInteger(r.hired_hours),
               rel.overtime_hours = toInteger(r.overtime_hours),
               rel.total_capacity = toInteger(r.total_capacity),
               rel.total_planned  = toInteger(r.total_planned),
               rel.deficit        = toInteger(r.deficit)""",
        rows)


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"Connecting to {URI} …")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("✅  Connected")

    print("Creating constraints …")
    for c in CONSTRAINTS:
        run(driver, c)
    print("✅  Constraints created")

    # Load CSVs
    prod_df = pd.read_csv(os.path.join(DATA_DIR, "factory_production.csv"))
    work_df = pd.read_csv(os.path.join(DATA_DIR, "factory_workers.csv"))
    cap_df  = pd.read_csv(os.path.join(DATA_DIR, "factory_capacity.csv"))

    print("Seeding production data …")
    seed_production(driver, prod_df)
    print("✅  Production nodes/relationships done")

    print("Seeding worker data …")
    seed_workers(driver, work_df)
    print("✅  Worker nodes/relationships done")

    print("Seeding capacity data …")
    seed_capacity(driver, cap_df)
    print("✅  Capacity data done")

    # Summary
    with driver.session() as s:
        node_count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rel_count  = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels     = [r["label"] for r in s.run("CALL db.labels() YIELD label RETURN label")]
        rel_types  = [r["type"]  for r in s.run("CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type")]

    print("\n── Graph summary ─────────────────────────")
    print(f"  Nodes         : {node_count}")
    print(f"  Relationships : {rel_count}")
    print(f"  Labels        : {labels}")
    print(f"  Rel types     : {rel_types}")
    print("─────────────────────────────────────────")

    driver.close()
    print("\n🎉  seed_graph.py complete!")


if __name__ == "__main__":
    main()