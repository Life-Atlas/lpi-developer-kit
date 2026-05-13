"""
seed_graph.py — Populate Neo4j with factory data from 3 CSVs.
Run once: python seed_graph.py
Safe to re-run (uses MERGE everywhere — idempotent).
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# ── helpers ──────────────────────────────────────────────────────────────────

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

# ── constraints ──────────────────────────────────────────────────────────────

def create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project)  REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station)  REQUIRE s.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker)   REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week)    REQUIRE wk.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp)    REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BOP)      REQUIRE b.name IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("✅ Constraints created")

# ── production.csv ────────────────────────────────────────────────────────────

def load_production(session, filepath):
    with open(filepath, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        project_id   = row["project_id"].strip()
        project_num  = row["project_number"].strip()
        project_name = row["project_name"].strip()
        product_type = row["product_type"].strip()
        unit         = row["unit"].strip()
        quantity     = safe_int(row["quantity"])
        unit_factor  = safe_float(row["unit_factor"])
        station_code = row["station_code"].strip()
        station_name = row["station_name"].strip()
        etapp        = row["etapp"].strip()
        bop          = row["bop"].strip()
        week         = row["week"].strip()
        planned      = safe_float(row["planned_hours"])
        actual       = safe_float(row["actual_hours"])
        completed    = safe_int(row["completed_units"])

        session.run("""
            MERGE (p:Project {id: $pid})
              ON CREATE SET p.number = $pnum, p.name = $pname

            MERGE (pr:Product {type: $ptype})
              ON CREATE SET pr.unit = $unit

            MERGE (s:Station {code: $scode})
              ON CREATE SET s.name = $sname

            MERGE (e:Etapp {name: $etapp})
            MERGE (b:BOP   {name: $bop})
            MERGE (wk:Week {name: $week})

            MERGE (p)-[:BELONGS_TO]->(e)
            MERGE (e)-[:CONTAINS_BOP]->(b)
            MERGE (b)-[:SPANS_WEEK]->(wk)

            MERGE (p)-[prod:PRODUCES]->(pr)
              ON CREATE SET prod.quantity = $qty, prod.unit_factor = $uf

            MERGE (p)-[sched:SCHEDULED_AT {week: $week}]->(s)
              ON CREATE SET
                sched.planned_hours   = $planned,
                sched.actual_hours    = $actual,
                sched.completed_units = $completed,
                sched.variance_pct    = CASE WHEN $planned > 0
                                         THEN round(($actual - $planned) / $planned * 100 * 10) / 10
                                         ELSE 0 END

            MERGE (s)-[:ACTIVE_IN]->(wk)
        """, pid=project_id, pnum=project_num, pname=project_name,
             ptype=product_type, unit=unit,
             scode=station_code, sname=station_name,
             etapp=etapp, bop=bop, week=week,
             qty=quantity, uf=unit_factor,
             planned=planned, actual=actual, completed=completed)

    print(f"✅ Production loaded ({len(rows)} rows → Projects, Products, Stations, Weeks, Etapps, BOPs)")

# ── factory_workers.csv ───────────────────────────────────────────────────────

def load_workers(session, filepath):
    with open(filepath, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        worker_id      = row["worker_id"].strip()
        name           = row["name"].strip()
        role           = row["role"].strip()
        primary        = row["primary_station"].strip()
        can_cover_raw  = row["can_cover_stations"].strip()
        certs          = row["certifications"].strip()
        hours_per_week = safe_int(row["hours_per_week"])
        wtype          = row["type"].strip()

        session.run("""
            MERGE (w:Worker {id: $wid})
              ON CREATE SET
                w.name           = $name,
                w.role           = $role,
                w.certifications = $certs,
                w.hours_per_week = $hpw,
                w.type           = $wtype
        """, wid=worker_id, name=name, role=role,
             certs=certs, hpw=hours_per_week, wtype=wtype)

        # primary station
        if primary and primary != "all":
            session.run("""
                MATCH (w:Worker {id: $wid})
                MERGE (s:Station {code: $scode})
                MERGE (w)-[:WORKS_AT]->(s)
            """, wid=worker_id, scode=primary)

        # coverage stations
        cover_codes = [c.strip() for c in can_cover_raw.split(",") if c.strip()]
        if primary == "all":
            # Victor Elm can cover all — fetch all stations
            session.run("""
                MATCH (w:Worker {id: $wid})
                MATCH (s:Station)
                MERGE (w)-[:CAN_COVER]->(s)
            """, wid=worker_id)
        else:
            for code in cover_codes:
                session.run("""
                    MATCH (w:Worker {id: $wid})
                    MERGE (s:Station {code: $scode})
                    MERGE (w)-[:CAN_COVER]->(s)
                """, wid=worker_id, scode=code)

    print(f"✅ Workers loaded ({len(rows)} workers)")

# ── factory_capacity.csv ──────────────────────────────────────────────────────

def load_capacity(session, filepath):
    with open(filepath, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        week         = row["week"].strip()
        own_staff    = safe_int(row["own_staff_count"])
        hired_staff  = safe_int(row["hired_staff_count"])
        own_hours    = safe_float(row["own_hours"])
        hired_hours  = safe_float(row["hired_hours"])
        overtime     = safe_float(row["overtime_hours"])
        total_cap    = safe_float(row["total_capacity"])
        total_plan   = safe_float(row["total_planned"])
        deficit      = safe_float(row["deficit"])

        session.run("""
            MERGE (wk:Week {name: $week})
              ON MATCH SET
                wk.own_staff_count = $own_staff,
                wk.hired_staff_count = $hired_staff,
                wk.own_hours       = $own_hours,
                wk.hired_hours     = $hired_hours,
                wk.overtime_hours  = $overtime,
                wk.total_capacity  = $total_cap,
                wk.total_planned   = $total_plan,
                wk.deficit         = $deficit
        """, week=week, own_staff=own_staff, hired_staff=hired_staff,
             own_hours=own_hours, hired_hours=hired_hours, overtime=overtime,
             total_cap=total_cap, total_plan=total_plan, deficit=deficit)

    print(f"✅ Capacity loaded ({len(rows)} weeks)")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print(f"✅ Connected to {URI}\n")

    with driver.session() as session:
        create_constraints(session)
        load_production(session, "factory_production.csv")
        load_workers(session, "factory_workers.csv")
        load_capacity(session, "factory_capacity.csv")

    # Summary
    with driver.session() as session:
        nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels  = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels = session.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        rel_types = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c").single()["c"]

    print(f"\n📊 Graph summary:")
    print(f"   Nodes:              {nodes}")
    print(f"   Relationships:      {rels}")
    print(f"   Node labels:        {labels}")
    print(f"   Relationship types: {rel_types}")
    driver.close()

if __name__ == "__main__":
    main()
