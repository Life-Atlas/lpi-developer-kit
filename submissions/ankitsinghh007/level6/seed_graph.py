#!/usr/bin/env python3
"""
seed_graph.py — Factory Knowledge Graph Seeder
Author: Ankit Kumar Singh (ankitsinghh007)
Level 6 — LifeAtlas Contributor Program

Reads all 3 CSV files and populates a Neo4j knowledge graph.
Idempotent: uses MERGE everywhere — safe to run multiple times.

Usage:
    python seed_graph.py
    python seed_graph.py --verify   # run after seeding to check counts
"""

import csv
import os
import sys
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ── Connection ────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ── Data paths ────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PRODUCTION_CSV = os.path.join(DATA_DIR, "factory_production.csv")
WORKERS_CSV    = os.path.join(DATA_DIR, "factory_workers.csv")
CAPACITY_CSV   = os.path.join(DATA_DIR, "factory_capacity.csv")


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ─────────────────────────────────────────────────────────────
# STEP 0 — Constraints (uniqueness + index)
# ─────────────────────────────────────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (n:Project) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT product_type IF NOT EXISTS FOR (n:Product) REQUIRE n.type IS UNIQUE",
    "CREATE CONSTRAINT station_code IF NOT EXISTS FOR (n:Station) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT worker_id IF NOT EXISTS FOR (n:Worker) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT week_id IF NOT EXISTS FOR (n:Week) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT etapp_id IF NOT EXISTS FOR (n:Etapp) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT cert_name IF NOT EXISTS FOR (n:Certification) REQUIRE n.name IS UNIQUE",
]

def create_constraints(session):
    print("Creating constraints...")
    for c in CONSTRAINTS:
        try:
            session.run(c)
        except Exception as e:
            # Constraint may already exist — safe to ignore
            if "already exists" not in str(e).lower():
                print(f"  Warning: {e}")
    print("  Constraints ready.")


# ─────────────────────────────────────────────────────────────
# STEP 1 — Seed from factory_production.csv
# ─────────────────────────────────────────────────────────────

def seed_production(session):
    print("\nSeeding from factory_production.csv...")

    projects_seen  = {}
    products_seen  = {}
    stations_seen  = {}
    etapps_seen    = {}
    schedules      = []

    with open(PRODUCTION_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid   = row["project_id"]
            ptype = row["product_type"]
            scode = row["station_code"]
            etapp = row["etapp"]
            week  = row["week"]

            planned  = float(row["planned_hours"])
            actual   = float(row["actual_hours"])
            variance = round((actual - planned) / planned * 100, 2) if planned else 0

            # Collect unique nodes
            if pid not in projects_seen:
                projects_seen[pid] = {
                    "id": pid,
                    "number": row["project_number"],
                    "name": row["project_name"],
                    "etapp": etapp,
                    "bop": row["bop"],
                }

            if ptype not in products_seen:
                products_seen[ptype] = {
                    "type": ptype,
                    "unit": row["unit"],
                    "unit_factor": float(row["unit_factor"]),
                }

            if scode not in stations_seen:
                stations_seen[scode] = {
                    "code": scode,
                    "name": row["station_name"],
                }

            if etapp not in etapps_seen:
                etapps_seen[etapp] = {"id": etapp}

            schedules.append({
                "project_id": pid,
                "station_code": scode,
                "product_type": ptype,
                "week": week,
                "planned_hours": planned,
                "actual_hours": actual,
                "completed_units": int(row["completed_units"]),
                "variance_pct": variance,
                "quantity": float(row["quantity"]),
                "unit_factor": float(row["unit_factor"]),
            })

    # ── Write Project nodes ──
    for p in projects_seen.values():
        session.run("""
            MERGE (n:Project {id: $id})
            SET n.number = $number,
                n.name   = $name,
                n.etapp  = $etapp,
                n.bop    = $bop
        """, **p)

    # ── Write Product nodes ──
    for p in products_seen.values():
        session.run("""
            MERGE (n:Product {type: $type})
            SET n.unit        = $unit,
                n.unit_factor = $unit_factor
        """, **p)

    # ── Write Station nodes ──
    for s in stations_seen.values():
        session.run("""
            MERGE (n:Station {code: $code})
            SET n.name = $name
        """, **s)

    # ── Write Etapp nodes ──
    for e in etapps_seen.values():
        session.run("MERGE (n:Etapp {id: $id})", **e)

    # ── Write Week nodes (from production weeks seen) ──
    weeks_in_prod = sorted(set(s["week"] for s in schedules))
    for w in weeks_in_prod:
        session.run("MERGE (n:Week {id: $id})", id=w)

    # ── Write relationships from schedules ──
    for s in schedules:
        # Project -[:IN_ETAPP]-> Etapp
        session.run("""
            MATCH (p:Project {id: $project_id})
            MATCH (e:Etapp   {id: $etapp})
            MERGE (p)-[:IN_ETAPP]->(e)
        """, project_id=s["project_id"], etapp=projects_seen[s["project_id"]]["etapp"])

        # Project -[:PRODUCES {quantity, unit_factor}]-> Product
        session.run("""
            MATCH (p:Project {id: $project_id})
            MATCH (pr:Product {type: $product_type})
            MERGE (p)-[r:PRODUCES]->(pr)
            SET r.quantity    = $quantity,
                r.unit_factor = $unit_factor
        """, **{k: s[k] for k in ["project_id","product_type","quantity","unit_factor"]})

        # Product -[:PROCESSED_AT]-> Station
        session.run("""
            MATCH (pr:Product {type: $product_type})
            MATCH (st:Station {code: $station_code})
            MERGE (pr)-[:PROCESSED_AT]->(st)
        """, product_type=s["product_type"], station_code=s["station_code"])

        # Project -[:SCHEDULED_AT {week, hours, variance}]-> Station
        session.run("""
            MATCH (p:Project {id: $project_id})
            MATCH (st:Station {code: $station_code})
            MERGE (p)-[r:SCHEDULED_AT {week: $week}]->(st)
            SET r.planned_hours    = $planned_hours,
                r.actual_hours     = $actual_hours,
                r.completed_units  = $completed_units,
                r.variance_pct     = $variance_pct
        """, **{k: s[k] for k in [
            "project_id","station_code","week",
            "planned_hours","actual_hours","completed_units","variance_pct"
        ]})

    print(f"  Projects:  {len(projects_seen)}")
    print(f"  Products:  {len(products_seen)}")
    print(f"  Stations:  {len(stations_seen)}")
    print(f"  Etapps:    {len(etapps_seen)}")
    print(f"  Schedules: {len(schedules)}")


# ─────────────────────────────────────────────────────────────
# STEP 2 — Seed from factory_workers.csv
# ─────────────────────────────────────────────────────────────

def seed_workers(session):
    print("\nSeeding from factory_workers.csv...")

    with open(WORKERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        wid   = row["worker_id"]
        name  = row["name"]
        role  = row["role"]
        prim  = row["primary_station"].strip()
        cover = [s.strip() for s in row["can_cover_stations"].split(",") if s.strip()]
        certs = [c.strip() for c in row["certifications"].split(",") if c.strip()]
        hpw   = int(row["hours_per_week"])
        wtype = row["type"]

        # Worker node
        session.run("""
            MERGE (w:Worker {id: $id})
            SET w.name           = $name,
                w.role           = $role,
                w.hours_per_week = $hpw,
                w.type           = $wtype,
                w.primary_station = $prim
        """, id=wid, name=name, role=role, hpw=hpw, wtype=wtype, prim=prim)

        # Primary station — WORKS_AT
        if prim != "all":
            session.run("""
                MATCH (w:Worker {id: $wid})
                MATCH (s:Station {code: $scode})
                MERGE (w)-[r:WORKS_AT]->(s)
                SET r.primary = true
            """, wid=wid, scode=prim)
        else:
            # Victor Elm (Foreman) works at all stations
            all_stations = ["011","012","013","014","015","016","017","018","019","021"]
            for sc in all_stations:
                session.run("""
                    MATCH (w:Worker {id: $wid})
                    MATCH (s:Station {code: $scode})
                    MERGE (w)-[r:WORKS_AT]->(s)
                    SET r.primary = true
                """, wid=wid, scode=sc)

        # CAN_COVER stations
        for sc in cover:
            session.run("""
                MATCH (w:Worker {id: $wid})
                MATCH (s:Station {code: $scode})
                MERGE (w)-[:CAN_COVER]->(s)
            """, wid=wid, scode=sc)

        # Certifications
        for cert in certs:
            session.run("""
                MERGE (c:Certification {name: $cert})
            """, cert=cert)
            session.run("""
                MATCH (w:Worker {id: $wid})
                MATCH (c:Certification {name: $cert})
                MERGE (w)-[:HAS_CERTIFICATION]->(c)
            """, wid=wid, cert=cert)

    print(f"  Workers seeded: {len(rows)}")


# ─────────────────────────────────────────────────────────────
# STEP 3 — Seed from factory_capacity.csv
# ─────────────────────────────────────────────────────────────

def seed_capacity(session):
    print("\nSeeding from factory_capacity.csv...")

    with open(CAPACITY_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        week_id  = row["week"]
        own_h    = float(row["own_hours"])
        hired_h  = float(row["hired_hours"])
        ot_h     = float(row["overtime_hours"])
        total_c  = float(row["total_capacity"])
        total_p  = float(row["total_planned"])
        deficit  = float(row["deficit"])
        own_cnt  = int(row["own_staff_count"])
        hired_cnt= int(row["hired_staff_count"])

        # Ensure Week node exists
        session.run("MERGE (w:Week {id: $id})", id=week_id)

        # Capacity node (one per week)
        session.run("""
            MERGE (c:Capacity {week: $week_id})
            SET c.own_hours      = $own_h,
                c.hired_hours    = $hired_h,
                c.overtime_hours = $ot_h,
                c.total_capacity = $total_c,
                c.total_planned  = $total_p,
                c.deficit        = $deficit,
                c.own_staff      = $own_cnt,
                c.hired_staff    = $hired_cnt,
                c.is_deficit     = ($deficit < 0)
        """, week_id=week_id, own_h=own_h, hired_h=hired_h, ot_h=ot_h,
             total_c=total_c, total_p=total_p, deficit=deficit,
             own_cnt=own_cnt, hired_cnt=hired_cnt)

        # Week -[:HAS_CAPACITY]-> Capacity
        session.run("""
            MATCH (w:Week {id: $week_id})
            MATCH (c:Capacity {week: $week_id})
            MERGE (w)-[r:HAS_CAPACITY]->(c)
            SET r.deficit        = $deficit,
                r.total_capacity = $total_c,
                r.total_planned  = $total_p
        """, week_id=week_id, deficit=deficit, total_c=total_c, total_p=total_p)

    print(f"  Weeks seeded: {len(rows)}")


# ─────────────────────────────────────────────────────────────
# STEP 4 — Compute Bottleneck nodes (derived)
# ─────────────────────────────────────────────────────────────

def seed_bottlenecks(session):
    print("\nComputing Bottleneck nodes...")

    session.run("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WHERE r.actual_hours > r.planned_hours * 1.1
        WITH s, r.week AS week,
             count(p) AS overrun_count,
             sum(r.actual_hours - r.planned_hours) AS excess_hours,
             collect(p.id) AS projects
        MERGE (b:Bottleneck {station_code: s.code, week: week})
        SET b.excess_hours  = excess_hours,
            b.overrun_count = overrun_count,
            b.projects      = projects,
            b.severity      = CASE
                WHEN excess_hours > 15 THEN "HIGH"
                WHEN excess_hours > 7  THEN "MEDIUM"
                ELSE "LOW"
            END
        WITH b, s
        MERGE (b)-[:TRIGGERED_AT]->(s)
    """)

    result = session.run("MATCH (b:Bottleneck) RETURN count(b) AS c")
    count = result.single()["c"]
    print(f"  Bottleneck nodes created: {count}")


# ─────────────────────────────────────────────────────────────
# VERIFY — counts and relationship types
# ─────────────────────────────────────────────────────────────

def verify(session):
    print("\n── Verification ─────────────────────────────────────────")

    node_counts = session.run("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
    """)
    print("\nNode counts:")
    total_nodes = 0
    for r in node_counts:
        print(f"  {r['label']:<16} {r['count']}")
        total_nodes += r['count']
    print(f"  {'TOTAL':<16} {total_nodes}")

    rel_counts = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(r) AS count
        ORDER BY count DESC
    """)
    print("\nRelationship counts:")
    total_rels = 0
    for r in rel_counts:
        print(f"  {r['rel_type']:<24} {r['count']}")
        total_rels += r['count']
    print(f"  {'TOTAL':<24} {total_rels}")

    print(f"\n{'✅' if total_nodes >= 50 else '❌'} Nodes >= 50: {total_nodes}")
    print(f"{'✅' if total_rels >= 100 else '❌'} Relationships >= 100: {total_rels}")

    # Check variance query works
    result = session.run("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WHERE r.actual_hours > r.planned_hours * 1.1
        RETURN count(*) AS c
    """)
    var_count = result.single()["c"]
    print(f"{'✅' if var_count > 0 else '❌'} Variance >10% rows: {var_count}")
    print("─────────────────────────────────────────────────────────")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed factory knowledge graph into Neo4j")
    parser.add_argument("--verify", action="store_true", help="Only run verification")
    args = parser.parse_args()

    # Check CSV files exist
    for path, name in [
        (PRODUCTION_CSV, "factory_production.csv"),
        (WORKERS_CSV,    "factory_workers.csv"),
        (CAPACITY_CSV,   "factory_capacity.csv"),
    ]:
        if not os.path.isfile(path):
            print(f"[ERROR] Cannot find {name} at {path}")
            print(f"        Place CSV files in a 'data/' folder next to seed_graph.py")
            sys.exit(1)

    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = get_driver()

    try:
        with driver.session() as session:
            session.run("RETURN 1")  # connection test
        print("Connected.\n")
    except Exception as e:
        print(f"[ERROR] Cannot connect to Neo4j: {e}")
        print("        Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
        sys.exit(1)

    with driver.session() as session:
        if args.verify:
            verify(session)
        else:
            create_constraints(session)
            seed_production(session)
            seed_workers(session)
            seed_capacity(session)
            seed_bottlenecks(session)
            print("\nSeeding complete.")
            verify(session)

    driver.close()


if __name__ == "__main__":
    main()
