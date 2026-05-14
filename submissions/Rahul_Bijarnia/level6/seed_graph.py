"""
seed_graph.py — Populate Neo4j with factory data from 3 CSV files.
Run once (idempotent via MERGE). Safe to re-run.

Usage:
    python seed_graph.py

Requires .env with:
    NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your-password
"""

import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not PASSWORD:
    raise ValueError("Set NEO4J_URI and NEO4J_PASSWORD in your .env file.")


# ── helpers ────────────────────────────────────────────────────────────────────

def run(tx, query, **params):
    tx.run(query, **params)


# ── constraints ────────────────────────────────────────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product)  REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Station)  REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Worker)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Week)     REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Etapp)    REQUIRE n.id IS UNIQUE",
]


def create_constraints(session):
    for c in CONSTRAINTS:
        session.run(c)
    print("✅ Constraints created")


# ── node creation ──────────────────────────────────────────────────────────────

def seed_projects(session, prod_df):
    projects = prod_df[["project_id", "project_name", "project_number"]].drop_duplicates()
    for _, row in projects.iterrows():
        session.execute_write(run, """
            MERGE (p:Project {id: $id})
            SET p.name = $name, p.number = $number
        """, id=row["project_id"], name=row["project_name"], number=int(row["project_number"]))
    print(f"✅ {len(projects)} Project nodes")


def seed_products(session, prod_df):
    products = prod_df[["product_type", "unit", "unit_factor"]].drop_duplicates("product_type")
    for _, row in products.iterrows():
        session.execute_write(run, """
            MERGE (p:Product {code: $code})
            SET p.unit = $unit, p.unit_factor = $unit_factor
        """, code=row["product_type"], unit=row["unit"], unit_factor=float(row["unit_factor"]))
    print(f"✅ {len(products)} Product nodes")


def seed_stations(session, prod_df):
    stations = prod_df[["station_code", "station_name"]].drop_duplicates("station_code")
    for _, row in stations.iterrows():
        session.execute_write(run, """
            MERGE (s:Station {code: $code})
            SET s.name = $name
        """, code=str(row["station_code"]), name=row["station_name"])
    print(f"✅ {len(stations)} Station nodes")


def seed_weeks(session, prod_df, cap_df):
    all_weeks = sorted(set(prod_df["week"].unique()) | set(cap_df["week"].unique()))
    for w in all_weeks:
        session.execute_write(run, """
            MERGE (w:Week {id: $id})
        """, id=w)
    print(f"✅ {len(all_weeks)} Week nodes")


def seed_etapps(session, prod_df):
    etapps = prod_df["etapp"].unique()
    for e in etapps:
        session.execute_write(run, """
            MERGE (e:Etapp {id: $id})
        """, id=e)
    print(f"✅ {len(etapps)} Etapp nodes")


def seed_workers(session, workers_df):
    for _, row in workers_df.iterrows():
        session.execute_write(run, """
            MERGE (w:Worker {id: $id})
            SET w.name = $name,
                w.role = $role,
                w.primary_station = $primary_station,
                w.hours_per_week = $hours_per_week,
                w.type = $type,
                w.certifications = $certifications
        """,
            id=row["worker_id"],
            name=row["name"],
            role=row["role"],
            primary_station=str(row["primary_station"]),
            hours_per_week=int(row["hours_per_week"]),
            type=row["type"],
            certifications=row["certifications"]
        )
    print(f"✅ {len(workers_df)} Worker nodes")


# ── relationship creation ──────────────────────────────────────────────────────

def seed_scheduled_at(session, prod_df):
    """(Project)-[:SCHEDULED_AT {week, planned_hours, actual_hours}]->(Station)"""
    count = 0
    for _, row in prod_df.iterrows():
        variance_pct = 0.0
        if row["planned_hours"] and row["planned_hours"] > 0:
            variance_pct = round(
                (row["actual_hours"] - row["planned_hours"]) / row["planned_hours"] * 100, 2
            )
        session.execute_write(run, """
            MATCH (p:Project {id: $pid})
            MATCH (s:Station {code: $scode})
            MATCH (w:Week {id: $week})
            MERGE (p)-[r:SCHEDULED_AT {week: $week, station_code: $scode}]->(s)
            SET r.planned_hours   = $planned,
                r.actual_hours    = $actual,
                r.variance_pct    = $variance_pct,
                r.completed_units = $completed,
                r.etapp           = $etapp,
                r.bop             = $bop
        """,
            pid=row["project_id"],
            scode=str(row["station_code"]),
            week=row["week"],
            planned=float(row["planned_hours"]),
            actual=float(row["actual_hours"]),
            variance_pct=variance_pct,
            completed=int(row["completed_units"]),
            etapp=row["etapp"],
            bop=row["bop"],
        )
        count += 1
    print(f"✅ {count} SCHEDULED_AT relationships")


def seed_produces(session, prod_df):
    """(Project)-[:PRODUCES {qty, unit_factor}]->(Product)"""
    combos = prod_df[["project_id", "product_type", "quantity", "unit_factor"]].drop_duplicates(
        ["project_id", "product_type"]
    )
    for _, row in combos.iterrows():
        session.execute_write(run, """
            MATCH (p:Project {id: $pid})
            MATCH (pr:Product {code: $pcode})
            MERGE (p)-[r:PRODUCES]->(pr)
            SET r.quantity = $qty, r.unit_factor = $uf
        """, pid=row["project_id"], pcode=row["product_type"],
             qty=float(row["quantity"]), uf=float(row["unit_factor"]))
    print(f"✅ {len(combos)} PRODUCES relationships")


def seed_worker_station_rels(session, workers_df):
    """(Worker)-[:WORKS_AT]->(Station) and (Worker)-[:CAN_COVER]->(Station)"""
    works_count = 0
    cover_count = 0
    for _, row in workers_df.iterrows():
        primary = str(row["primary_station"])
        if primary == "all":
            # Foreman — works at all stations (create WORKS_AT for all)
            session.execute_write(run, """
                MATCH (w:Worker {id: $wid})
                MATCH (s:Station)
                MERGE (w)-[:WORKS_AT]->(s)
            """, wid=row["worker_id"])
            works_count += 9
        else:
            # Normalise: station_code in CSV may be '011' but Station nodes use str(int) e.g. '11'
            pcode = str(int(primary)) if primary.isdigit() else primary
            session.execute_write(run, """
                MATCH (w:Worker {id: $wid})
                MATCH (s:Station {code: $scode})
                MERGE (w)-[:WORKS_AT]->(s)
            """, wid=row["worker_id"], scode=pcode)
            works_count += 1

        # CAN_COVER
        can_cover_raw = str(row["can_cover_stations"])
        codes = [c.strip() for c in can_cover_raw.split(",") if c.strip()]
        for c in codes:
            ccode = str(int(c)) if c.isdigit() else c
            session.execute_write(run, """
                MATCH (w:Worker {id: $wid})
                MATCH (s:Station {code: $scode})
                MERGE (w)-[:CAN_COVER]->(s)
            """, wid=row["worker_id"], scode=ccode)
            cover_count += 1

    print(f"✅ {works_count} WORKS_AT + {cover_count} CAN_COVER relationships")


def seed_capacity(session, cap_df):
    """(Week)-[:HAS_CAPACITY {own, hired, overtime, total, demand, deficit}]->(:CapacityRecord)"""
    count = 0
    for _, row in cap_df.iterrows():
        session.execute_write(run, """
            MATCH (w:Week {id: $wid})
            MERGE (cr:CapacityRecord {week: $wid})
            SET cr.own_staff       = $own_staff,
                cr.hired_staff     = $hired_staff,
                cr.own_hours       = $own_hours,
                cr.hired_hours     = $hired_hours,
                cr.overtime_hours  = $overtime,
                cr.total_capacity  = $total,
                cr.total_planned   = $demand,
                cr.deficit         = $deficit
            MERGE (w)-[r:HAS_CAPACITY]->(cr)
            SET r.total_capacity = $total,
                r.deficit        = $deficit
        """,
            wid=row["week"],
            own_staff=int(row["own_staff_count"]),
            hired_staff=int(row["hired_staff_count"]),
            own_hours=int(row["own_hours"]),
            hired_hours=int(row["hired_hours"]),
            overtime=int(row["overtime_hours"]),
            total=int(row["total_capacity"]),
            demand=int(row["total_planned"]),
            deficit=int(row["deficit"]),
        )
        count += 1
    print(f"✅ {count} HAS_CAPACITY relationships + CapacityRecord nodes")


def seed_etapp_rels(session, prod_df):
    """(Project)-[:IN_ETAPP]->(Etapp)"""
    combos = prod_df[["project_id", "etapp"]].drop_duplicates()
    for _, row in combos.iterrows():
        session.execute_write(run, """
            MATCH (p:Project {id: $pid})
            MATCH (e:Etapp {id: $eid})
            MERGE (p)-[:IN_ETAPP]->(e)
        """, pid=row["project_id"], eid=row["etapp"])
    print(f"✅ {len(combos)} IN_ETAPP relationships")


def seed_week_sequence(session, cap_df):
    """(Week)-[:NEXT_WEEK]->(Week) for temporal ordering"""
    weeks = sorted(cap_df["week"].unique())
    for i in range(len(weeks) - 1):
        session.execute_write(run, """
            MATCH (a:Week {id: $a}), (b:Week {id: $b})
            MERGE (a)-[:NEXT_WEEK]->(b)
        """, a=weeks[i], b=weeks[i + 1])
    print(f"✅ {len(weeks) - 1} NEXT_WEEK relationships")


def seed_project_week_rels(session, prod_df):
    """(Project)-[:ACTIVE_IN]->(Week) — 8th relationship type for Self-Test check 5"""
    combos = prod_df[["project_id", "week"]].drop_duplicates()
    for _, row in combos.iterrows():
        session.execute_write(run, """
            MATCH (p:Project {id: $pid})
            MATCH (w:Week {id: $wid})
            MERGE (p)-[:ACTIVE_IN]->(w)
        """, pid=row["project_id"], wid=row["week"])
    print(f"✅ {len(combos)} ACTIVE_IN relationships")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("Seeding Neo4j factory knowledge graph…")
    print("=" * 50)

    prod_df    = pd.read_csv("data/factory_production.csv")
    workers_df = pd.read_csv("data/factory_workers.csv")
    cap_df     = pd.read_csv("data/factory_capacity.csv")

    # Normalise station_code to string (drop leading zeros)
    prod_df["station_code"] = prod_df["station_code"].astype(str)

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("✅ Connected to Neo4j")

    with driver.session() as session:
        # 1. Constraints
        create_constraints(session)

        # 2. Nodes
        print("\n── Nodes ──")
        seed_projects(session, prod_df)
        seed_products(session, prod_df)
        seed_stations(session, prod_df)
        seed_weeks(session, prod_df, cap_df)
        seed_etapps(session, prod_df)
        seed_workers(session, workers_df)

        # 3. Relationships
        print("\n── Relationships ──")
        seed_scheduled_at(session, prod_df)
        seed_produces(session, prod_df)
        seed_worker_station_rels(session, workers_df)
        seed_capacity(session, cap_df)
        seed_etapp_rels(session, prod_df)
        seed_week_sequence(session, cap_df)
        seed_project_week_rels(session, prod_df)   # ← NEW: 8th relationship type

        # 4. Summary
        node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rel_count  = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels     = [r["label"] for r in session.run("CALL db.labels() YIELD label")]
        rel_types  = [r["relationshipType"] for r in session.run("CALL db.relationshipTypes() YIELD relationshipType")]

    driver.close()

    print("\n" + "=" * 50)
    print(f"✅ DONE — {node_count} nodes, {rel_count} relationships")
    print(f"   Labels:  {labels}")
    print(f"   Rel types: {rel_types}")
    print("=" * 50)


if __name__ == "__main__":
    main()
