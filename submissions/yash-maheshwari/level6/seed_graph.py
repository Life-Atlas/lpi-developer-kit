import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ── helper ──────────────────────────────────────────────────────────────────
def run(session, query, **params):
    session.run(query, **params)

# ── 1. CONSTRAINTS ───────────────────────────────────────────────────────────
def create_constraints(session):
    print("Creating constraints...")
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project)      REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Station)      REQUIRE n.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product)      REQUIRE n.type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Worker)       REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Week)         REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Certification) REQUIRE n.name IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("  Done.")

# ── 2. NODES ─────────────────────────────────────────────────────────────────
def seed_projects(session, prod_df):
    print("Creating Project nodes...")
    projects = prod_df[["project_id","project_name","project_number"]].drop_duplicates()
    for _, row in projects.iterrows():
        session.run("""
            MERGE (p:Project {id: $id})
            SET p.name   = $name,
                p.number = $number
        """, id=row.project_id, name=row.project_name, number=int(row.project_number))
    print(f"  {len(projects)} projects.")

def seed_stations(session, prod_df):
    print("Creating Station nodes...")
    stations = prod_df[["station_code","station_name"]].drop_duplicates()
    for _, row in stations.iterrows():
        session.run("""
            MERGE (s:Station {code: $code})
            SET s.name = $name
        """, code=str(row.station_code), name=row.station_name)
    print(f"  {len(stations)} stations.")

def seed_products(session, prod_df):
    print("Creating Product nodes...")
    products = prod_df[["product_type","unit","unit_factor"]].drop_duplicates()
    for _, row in products.iterrows():
        session.run("""
            MERGE (p:Product {type: $type})
            SET p.unit        = $unit,
                p.unit_factor = $unit_factor
        """, type=row.product_type, unit=row.unit, unit_factor=float(row.unit_factor))
    print(f"  {len(products)} products.")

def seed_weeks(session, cap_df):
    print("Creating Week nodes...")
    for _, row in cap_df.iterrows():
        session.run("""
            MERGE (w:Week {id: $id})
            SET w.own_staff      = $own_staff,
                w.hired_staff    = $hired_staff,
                w.own_hours      = $own_hours,
                w.hired_hours    = $hired_hours,
                w.overtime_hours = $overtime_hours,
                w.total_capacity = $total_capacity,
                w.total_planned  = $total_planned,
                w.deficit        = $deficit
        """,
        id=row.week,
        own_staff=int(row.own_staff_count),
        hired_staff=int(row.hired_staff_count),
        own_hours=int(row.own_hours),
        hired_hours=int(row.hired_hours),
        overtime_hours=int(row.overtime_hours),
        total_capacity=int(row.total_capacity),
        total_planned=int(row.total_planned),
        deficit=int(row.deficit))
    print(f"  {len(cap_df)} weeks.")

def seed_workers(session, workers_df):
    print("Creating Worker nodes...")
    for _, row in workers_df.iterrows():
        session.run("""
            MERGE (w:Worker {id: $id})
            SET w.name           = $name,
                w.role           = $role,
                w.primary_station = $primary_station,
                w.hours_per_week = $hours_per_week,
                w.type           = $type
        """,
        id=row.worker_id,
        name=row["name"],
        role=row.role,
        primary_station=str(row.primary_station),
        hours_per_week=int(row.hours_per_week),
        type=row["type"])
    print(f"  {len(workers_df)} workers.")

def seed_certifications(session, workers_df):
    print("Creating Certification nodes...")
    certs = set()
    for _, row in workers_df.iterrows():
        for cert in str(row.certifications).split(","):
            certs.add(cert.strip())
    for cert in certs:
        session.run("MERGE (:Certification {name: $name})", name=cert)
    print(f"  {len(certs)} certifications.")

# ── 3. RELATIONSHIPS ──────────────────────────────────────────────────────────
def seed_scheduled_at(session, prod_df):
    """Project -[:SCHEDULED_AT {week, planned_hours, actual_hours, ...}]-> Station"""
    print("Creating SCHEDULED_AT relationships...")
    count = 0
    for _, row in prod_df.iterrows():
        session.run("""
            MATCH (p:Project {id: $proj_id})
            MATCH (s:Station {code: $station_code})
            MERGE (p)-[r:SCHEDULED_AT {week: $week, product_type: $product_type}]->(s)
            SET r.planned_hours    = $planned_hours,
                r.actual_hours     = $actual_hours,
                r.completed_units  = $completed_units,
                r.etapp            = $etapp,
                r.bop              = $bop
        """,
        proj_id=row.project_id,
        station_code=str(row.station_code),
        week=row.week,
        product_type=row.product_type,
        planned_hours=float(row.planned_hours),
        actual_hours=float(row.actual_hours),
        completed_units=int(row.completed_units),
        etapp=row.etapp,
        bop=row.bop)
        count += 1
    print(f"  {count} SCHEDULED_AT relationships.")

def seed_produces(session, prod_df):
    """Project -[:PRODUCES {quantity, unit}]-> Product"""
    print("Creating PRODUCES relationships...")
    pairs = prod_df[["project_id","product_type","quantity","unit"]].drop_duplicates(
        subset=["project_id","product_type"])
    for _, row in pairs.iterrows():
        session.run("""
            MATCH (p:Project {id: $proj_id})
            MATCH (pr:Product {type: $product_type})
            MERGE (p)-[r:PRODUCES]->(pr)
            SET r.quantity = $quantity,
                r.unit     = $unit
        """,
        proj_id=row.project_id,
        product_type=row.product_type,
        quantity=int(row.quantity),
        unit=row.unit)
    print(f"  {len(pairs)} PRODUCES relationships.")

def seed_active_in(session, prod_df):
    """Project -[:ACTIVE_IN]-> Week"""
    print("Creating ACTIVE_IN relationships...")
    pairs = prod_df[["project_id","week"]].drop_duplicates()
    for _, row in pairs.iterrows():
        session.run("""
            MATCH (p:Project {id: $proj_id})
            MATCH (w:Week {id: $week})
            MERGE (p)-[:ACTIVE_IN]->(w)
        """, proj_id=row.project_id, week=row.week)
    print(f"  {len(pairs)} ACTIVE_IN relationships.")

def seed_worker_station(session, workers_df):
    """Worker -[:WORKS_AT]-> Station  and  Worker -[:CAN_COVER]-> Station"""
    print("Creating WORKS_AT and CAN_COVER relationships...")
    works_count = 0
    cover_count = 0
    for _, row in workers_df.iterrows():
        primary = str(row.primary_station).strip()
        # WORKS_AT primary station (skip 'all')
        if primary != "all":
            session.run("""
                MATCH (w:Worker {id: $worker_id})
                MATCH (s:Station {code: $code})
                MERGE (w)-[:WORKS_AT]->(s)
            """, worker_id=row.worker_id, code=primary)
            works_count += 1

        # CAN_COVER all listed stations
        for code in str(row.can_cover_stations).split(","):
            code = code.strip()
            if code and code != "all":
                session.run("""
                    MATCH (w:Worker {id: $worker_id})
                    MATCH (s:Station {code: $code})
                    MERGE (w)-[:CAN_COVER]->(s)
                """, worker_id=row.worker_id, code=code)
                cover_count += 1

    print(f"  {works_count} WORKS_AT, {cover_count} CAN_COVER relationships.")

def seed_has_certification(session, workers_df):
    """Worker -[:HAS_CERTIFICATION]-> Certification"""
    print("Creating HAS_CERTIFICATION relationships...")
    count = 0
    for _, row in workers_df.iterrows():
        for cert in str(row.certifications).split(","):
            cert = cert.strip()
            session.run("""
                MATCH (w:Worker {id: $worker_id})
                MATCH (c:Certification {name: $cert})
                MERGE (w)-[:HAS_CERTIFICATION]->(c)
            """, worker_id=row.worker_id, cert=cert)
            count += 1
    print(f"  {count} HAS_CERTIFICATION relationships.")

def seed_station_in_week(session, prod_df):
    """Station -[:LOADED_IN {planned_hours, actual_hours}]-> Week"""
    print("Creating LOADED_IN relationships...")
    grouped = prod_df.groupby(["station_code","week"]).agg(
        planned_hours=("planned_hours","sum"),
        actual_hours=("actual_hours","sum")
    ).reset_index()
    for _, row in grouped.iterrows():
        session.run("""
            MATCH (s:Station {code: $code})
            MATCH (w:Week {id: $week})
            MERGE (s)-[r:LOADED_IN]->(w)
            SET r.planned_hours = $planned,
                r.actual_hours  = $actual
        """,
        code=str(row.station_code),
        week=row.week,
        planned=float(row.planned_hours),
        actual=float(row.actual_hours))
    print(f"  {len(grouped)} LOADED_IN relationships.")

def seed_reports_to(session, workers_df):
    """Non-foreman Workers -[:REPORTS_TO]-> Foreman (W11 Victor Elm)"""
    print("Creating REPORTS_TO relationships...")
    foreman = workers_df[workers_df["role"] == "Foreman"]["worker_id"].values
    if len(foreman) == 0:
        print("  No foreman found, skipping.")
        return
    foreman_id = foreman[0]
    operators = workers_df[workers_df["worker_id"] != foreman_id]["worker_id"]
    for wid in operators:
        session.run("""
            MATCH (w:Worker {id: $wid})
            MATCH (f:Worker {id: $fid})
            MERGE (w)-[:REPORTS_TO]->(f)
        """, wid=wid, fid=foreman_id)
    print(f"  {len(operators)} REPORTS_TO relationships.")

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("\n=== Loading CSVs ===")
    prod_df    = pd.read_csv("factory_production.csv")
    workers_df = pd.read_csv("factory_workers.csv")
    cap_df     = pd.read_csv("factory_capacity.csv")

    # normalize station_code to string
    prod_df["station_code"] = prod_df["station_code"].astype(str).str.zfill(3)

    print("\n=== Seeding Neo4j ===")
    with driver.session() as s:
        create_constraints(s)

        # Nodes
        seed_projects(s, prod_df)
        seed_stations(s, prod_df)
        seed_products(s, prod_df)
        seed_weeks(s, cap_df)
        seed_workers(s, workers_df)
        seed_certifications(s, workers_df)

        # Relationships
        seed_scheduled_at(s, prod_df)
        seed_produces(s, prod_df)
        seed_active_in(s, prod_df)
        seed_worker_station(s, workers_df)
        seed_has_certification(s, workers_df)
        seed_station_in_week(s, prod_df)
        seed_reports_to(s, workers_df)

    driver.close()
    print("\n✅ Graph seeded successfully!")

if __name__ == "__main__":
    main()