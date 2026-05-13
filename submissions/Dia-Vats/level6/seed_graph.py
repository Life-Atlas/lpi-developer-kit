"""
seed_graph.py — Swedish Steel Factory Graph Seeder
Author: Dia Vats
Description:
    Reads factory_production.csv, factory_workers.csv, factory_capacity.csv
    and seeds a Neo4j graph database that exactly follows the schema defined
    in schema.md / schema.png.

    Safe to re-run: uses MERGE everywhere, never CREATE.
    WorkOrder IDs: {project_id}_{station_code}_{week}_{product_type}
    e.g. P01_011_w1_IQB
"""

import os
import csv
from itertools import groupby
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PRODUCTION_CSV = os.path.join(BASE_DIR, "data", "factory_production.csv")
WORKERS_CSV    = os.path.join(BASE_DIR, "data", "factory_workers.csv")
CAPACITY_CSV   = os.path.join(BASE_DIR, "data", "factory_capacity.csv")

# Production flow order (exactly as specified)
STATION_FLOW = [
    "011", "012", "013", "014", "015",
    "016", "017", "018", "019", "021"
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def workorder_id(project_id: str, station_code: str, week: str, product_type: str) -> str:
    return f"{project_id}_{station_code}_{week}_{product_type}"


def variance_pct(planned: float, actual: float) -> float:
    if planned == 0:
        return 0.0
    return round((actual - planned) / planned * 100, 2)


def is_bottleneck(planned: float, actual: float) -> bool:
    return actual > planned * 1.1


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------

def create_constraints(session):
    print("Creating constraints …")
    constraints = [
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (n:Project)          REQUIRE n.project_id      IS UNIQUE",
        "CREATE CONSTRAINT workorder_id IF NOT EXISTS FOR (n:WorkOrder)       REQUIRE n.workorder_id    IS UNIQUE",
        "CREATE CONSTRAINT station_code IF NOT EXISTS FOR (n:Station)         REQUIRE n.station_code    IS UNIQUE",
        "CREATE CONSTRAINT product_type IF NOT EXISTS FOR (n:Product)         REQUIRE n.product_type    IS UNIQUE",
        "CREATE CONSTRAINT week_id IF NOT EXISTS FOR (n:Week)                 REQUIRE n.week_id         IS UNIQUE",
        "CREATE CONSTRAINT worker_id IF NOT EXISTS FOR (n:Worker)             REQUIRE n.worker_id       IS UNIQUE",
        "CREATE CONSTRAINT certification_name IF NOT EXISTS FOR (n:Certification) REQUIRE n.name        IS UNIQUE",
        "CREATE CONSTRAINT capacity_week IF NOT EXISTS FOR (n:CapacitySnapshot)   REQUIRE n.week_id     IS UNIQUE",
        "CREATE CONSTRAINT etapp_name IF NOT EXISTS FOR (n:Etapp)                 REQUIRE n.name        IS UNIQUE",
    ]
    for cypher in constraints:
        session.run(cypher)
    print("  ✓ Constraints ready.")


# ---------------------------------------------------------------------------
# Seed: Project, WorkOrder, Station, Product, Week nodes + core relationships
# ---------------------------------------------------------------------------

def seed_production(session, rows: list[dict]):
    print("Seeding production data …")

    # Build sorted week list for FOLLOWS logic
    week_sort = {"w1": 1, "w2": 2, "w3": 3, "w4": 4, "w5": 5, "w6": 6, "w7": 7, "w8": 8}

    for row in rows:
        project_id    = row["project_id"].strip()
        project_number = row["project_number"].strip()
        project_name  = row["project_name"].strip()
        product_type  = row["product_type"].strip()
        unit          = row["unit"].strip()
        unit_factor   = float(row["unit_factor"])
        quantity      = int(row["quantity"])
        station_code  = row["station_code"].strip()
        station_name  = row["station_name"].strip()
        etapp         = row["etapp"].strip()
        bop           = row["bop"].strip()
        week          = row["week"].strip()
        planned_hrs   = float(row["planned_hours"])
        actual_hrs    = float(row["actual_hours"])
        completed     = int(row["completed_units"])

        wo_id = workorder_id(project_id, station_code, week, product_type)
        var   = variance_pct(planned_hrs, actual_hrs)
        bottleneck = is_bottleneck(planned_hrs, actual_hrs)

        session.run("""
            MERGE (p:Project {project_id: $project_id})
            SET p.project_number = $project_number,
                p.project_name   = $project_name,
                p.etapp          = $etapp,
                p.bop            = $bop

            MERGE (st:Station {station_code: $station_code})
            SET st.station_name = $station_name

            MERGE (pr:Product {product_type: $product_type})
            SET pr.unit        = $unit,
                pr.unit_factor = $unit_factor

            MERGE (wk:Week {week_id: $week})

            MERGE (wo:WorkOrder {workorder_id: $wo_id})
            SET wo.planned_hours    = $planned_hrs,
                wo.actual_hours     = $actual_hrs,
                wo.completed_units  = $completed,
                wo.variance_pct     = $var,
                wo.is_bottleneck    = $bottleneck,
                wo.week             = $week,
                wo.station_code     = $station_code,
                wo.project_id       = $project_id,
                wo.product_type     = $product_type

            MERGE (p)-[:HAS_WORKORDER]->(wo)
            MERGE (wo)-[:AT_STATION]->(st)
            MERGE (wo)-[:PRODUCES]->(pr)

            MERGE (wo)-[r:SCHEDULED_IN]->(wk)
            SET r.planned_hours   = $planned_hrs,
                r.actual_hours    = $actual_hrs,
                r.completed_units = $completed
        """,
            project_id=project_id,
            project_number=project_number,
            project_name=project_name,
            etapp=etapp,
            bop=bop,
            station_code=station_code,
            station_name=station_name,
            product_type=product_type,
            unit=unit,
            unit_factor=unit_factor,
            week=week,
            wo_id=wo_id,
            planned_hrs=planned_hrs,
            actual_hrs=actual_hrs,
            completed=completed,
            var=var,
            bottleneck=bottleneck,
        )

        # (Project)-[:IN_ETAPP]->(Etapp)  — ET1 and ET2 only
        if etapp in ("ET1", "ET2"):
            session.run("""
                MERGE (e:Etapp {name: $etapp})
                MERGE (p:Project {project_id: $project_id})
                MERGE (p)-[:IN_ETAPP]->(e)
            """, etapp=etapp, project_id=project_id)

    print(f"  ✓ Seeded {len(rows)} WorkOrder rows.")


# ---------------------------------------------------------------------------
# Seed: FEEDS_INTO between stations (production flow order)
# ---------------------------------------------------------------------------

def seed_feeds_into(session):
    print("Creating FEEDS_INTO relationships …")
    for i in range(len(STATION_FLOW) - 1):
        src = STATION_FLOW[i]
        dst = STATION_FLOW[i + 1]
        session.run("""
            MATCH (a:Station {station_code: $src})
            MATCH (b:Station {station_code: $dst})
            MERGE (a)-[:FEEDS_INTO]->(b)
        """, src=src, dst=dst)
    print(f"  ✓ Created {len(STATION_FLOW)-1} FEEDS_INTO relationships.")


# ---------------------------------------------------------------------------
# Seed: FOLLOWS between WorkOrders (same project, same station, consecutive weeks)
# ---------------------------------------------------------------------------

def seed_follows(session, rows: list[dict]):
    print("Creating FOLLOWS relationships …")
    week_order = {"w1": 1, "w2": 2, "w3": 3, "w4": 4, "w5": 5, "w6": 6, "w7": 7, "w8": 8}

    # Group by (project_id, station_code, product_type)
    key = lambda r: (r["project_id"].strip(), r["station_code"].strip(), r["product_type"].strip())
    sorted_rows = sorted(rows, key=key)

    count = 0
    for grp_key, group in groupby(sorted_rows, key=key):
        project_id, station_code, product_type = grp_key
        group_list = sorted(list(group), key=lambda r: week_order.get(r["week"].strip(), 99))

        for idx in range(len(group_list) - 1):
            cur  = group_list[idx]
            nxt  = group_list[idx + 1]
            cur_week  = cur["week"].strip()
            nxt_week  = nxt["week"].strip()
            # Only link consecutive weeks
            if week_order.get(nxt_week, 99) - week_order.get(cur_week, 0) == 1:
                wo1 = workorder_id(project_id, station_code, cur_week, product_type)
                wo2 = workorder_id(project_id, station_code, nxt_week, product_type)
                session.run("""
                    MATCH (a:WorkOrder {workorder_id: $wo1})
                    MATCH (b:WorkOrder {workorder_id: $wo2})
                    MERGE (a)-[:FOLLOWS]->(b)
                """, wo1=wo1, wo2=wo2)
                count += 1

    print(f"  ✓ Created {count} FOLLOWS relationships.")


# ---------------------------------------------------------------------------
# Seed: Workers, Certifications, ASSIGNED_TO, CAN_COVER, CERTIFIED_IN, REQUIRES
# ---------------------------------------------------------------------------

def seed_workers(session, rows: list[dict]):
    print("Seeding workers …")
    for row in rows:
        worker_id    = row["worker_id"].strip()
        name         = row["name"].strip()
        role         = row["role"].strip()
        primary_sta  = row["primary_station"].strip()
        can_cover    = [s.strip() for s in row["can_cover_stations"].split(",")]
        certs        = [c.strip() for c in row["certifications"].split(",")]
        hours_pw     = int(row["hours_per_week"])
        wtype        = row["type"].strip()

        session.run("""
            MERGE (w:Worker {worker_id: $worker_id})
            SET w.name           = $name,
                w.role           = $role,
                w.hours_per_week = $hours_pw,
                w.type           = $wtype
        """, worker_id=worker_id, name=name, role=role, hours_pw=hours_pw, wtype=wtype)

        # ASSIGNED_TO primary station (skip "all" sentinel for Victor Elm)
        if primary_sta != "all":
            session.run("""
                MATCH (w:Worker {worker_id: $worker_id})
                MATCH (s:Station {station_code: $station_code})
                MERGE (w)-[:ASSIGNED_TO]->(s)
            """, worker_id=worker_id, station_code=primary_sta)

        # CAN_COVER stations
        for sc in can_cover:
            if sc:
                session.run("""
                    MATCH (w:Worker {worker_id: $worker_id})
                    MATCH (s:Station {station_code: $station_code})
                    MERGE (w)-[:CAN_COVER]->(s)
                """, worker_id=worker_id, station_code=sc)

        # CERTIFIED_IN certifications
        for cert in certs:
            if cert:
                session.run("""
                    MERGE (c:Certification {name: $cert})
                    WITH c
                    MATCH (w:Worker {worker_id: $worker_id})
                    MERGE (w)-[:CERTIFIED_IN]->(c)
                """, cert=cert, worker_id=worker_id)

        # REQUIRES: link each station this worker covers to their certifications
        for sc in can_cover:
            if sc:
                for cert in certs:
                    if cert:
                        session.run("""
                            MATCH (s:Station {station_code: $station_code})
                            MATCH (c:Certification {name: $cert})
                            MERGE (s)-[:REQUIRES]->(c)
                        """, station_code=sc, cert=cert)

    print(f"  ✓ Seeded {len(rows)} workers.")


# ---------------------------------------------------------------------------
# Seed: CapacitySnapshot + HAS_CAPACITY
# ---------------------------------------------------------------------------

def seed_capacity(session, rows: list[dict]):
    print("Seeding capacity snapshots …")
    for row in rows:
        week = row["week"].strip()
        session.run("""
            MERGE (wk:Week {week_id: $week})

            MERGE (cs:CapacitySnapshot {week_id: $week})
            SET cs.own_staff_count  = $own_staff,
                cs.hired_staff_count = $hired_staff,
                cs.own_hours        = $own_hours,
                cs.hired_hours      = $hired_hours,
                cs.overtime_hours   = $overtime,
                cs.total_capacity   = $total_cap,
                cs.total_planned    = $total_planned,
                cs.deficit          = $deficit

            MERGE (wk)-[:HAS_CAPACITY]->(cs)
        """,
            week=week,
            own_staff=int(row["own_staff_count"]),
            hired_staff=int(row["hired_staff_count"]),
            own_hours=int(row["own_hours"]),
            hired_hours=int(row["hired_hours"]),
            overtime=int(row["overtime_hours"]),
            total_cap=int(row["total_capacity"]),
            total_planned=int(row["total_planned"]),
            deficit=int(row["deficit"]),
        )
    print(f"  ✓ Seeded {len(rows)} CapacitySnapshot nodes.")


# ---------------------------------------------------------------------------
# Verification summary
# ---------------------------------------------------------------------------

def print_summary(session):
    print("\n--- Graph Summary ---")
    for label in ["Project", "WorkOrder", "Station", "Product", "Week",
                  "Worker", "Certification", "CapacitySnapshot", "Etapp"]:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
        cnt = result.single()["cnt"]
        print(f"  {label}: {cnt}")

    result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
    print(f"  Relationships: {result.single()['cnt']}")

    result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType)")
    rels = result.single()[0]
    print(f"  Relationship types: {rels}")
    print("---")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Connecting to Neo4j at {NEO4J_URI} …")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("  ✓ Connected.")

    production_rows = read_csv(PRODUCTION_CSV)
    workers_rows    = read_csv(WORKERS_CSV)
    capacity_rows   = read_csv(CAPACITY_CSV)

    with driver.session() as session:
        create_constraints(session)
        seed_production(session, production_rows)
        seed_feeds_into(session)
        seed_follows(session, production_rows)
        seed_workers(session, workers_rows)
        seed_capacity(session, capacity_rows)
        print_summary(session)

    driver.close()
    print("\n✅ Graph seeding complete. Safe to re-run.")


if __name__ == "__main__":
    main()
