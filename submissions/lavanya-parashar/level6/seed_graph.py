import csv
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ── helpers ──────────────────────────────────────────────────────────────────

def read_csv(filename):
    with open(filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def run(session, query, **params):
    session.run(query, **params)

# ── constraints ───────────────────────────────────────────────────────────────

def create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project)  REQUIRE p.project_id   IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station)  REQUIRE s.station_code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker)   REQUIRE w.worker_id    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week)    REQUIRE wk.week        IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.product_type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp)    REQUIRE e.etapp        IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Capacity) REQUIRE c.week         IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("✅ Constraints created")

# ── nodes ─────────────────────────────────────────────────────────────────────

def load_projects(session, rows):
    seen = set()
    for r in rows:
        if r["project_id"] in seen:
            continue
        seen.add(r["project_id"])
        session.run("""
            MERGE (p:Project {project_id: $project_id})
            SET p.project_number = $project_number,
                p.project_name   = $project_name
        """, project_id=r["project_id"],
             project_number=r["project_number"],
             project_name=r["project_name"])
    print(f"✅ {len(seen)} Project nodes")

def load_products(session, rows):
    seen = set()
    for r in rows:
        if r["product_type"] in seen:
            continue
        seen.add(r["product_type"])
        session.run("""
            MERGE (pr:Product {product_type: $product_type})
            SET pr.unit        = $unit,
                pr.quantity    = toFloat($quantity),
                pr.unit_factor = toFloat($unit_factor)
        """, product_type=r["product_type"],
             unit=r["unit"],
             quantity=r["quantity"],
             unit_factor=r["unit_factor"])
    print(f"✅ {len(seen)} Product nodes")

def load_stations(session, rows):
    seen = set()
    for r in rows:
        if r["station_code"] in seen:
            continue
        seen.add(r["station_code"])
        session.run("""
            MERGE (s:Station {station_code: $station_code})
            SET s.station_name = $station_name
        """, station_code=r["station_code"],
             station_name=r["station_name"])
    print(f"✅ {len(seen)} Station nodes")

def load_weeks(session, prod_rows, cap_rows):
    weeks = set()
    for r in prod_rows:
        weeks.add(r["week"])
    for r in cap_rows:
        weeks.add(r["week"])
    for w in weeks:
        session.run("""
            MERGE (wk:Week {week: $week})
        """, week=w)
    print(f"✅ {len(weeks)} Week nodes")

def load_etapps(session, rows):
    seen = set()
    for r in rows:
        if r["etapp"] in seen:
            continue
        seen.add(r["etapp"])
        session.run("""
            MERGE (e:Etapp {etapp: $etapp})
        """, etapp=r["etapp"])
    print(f"✅ {len(seen)} Etapp nodes")

def load_capacity(session, rows):
    for r in rows:
        session.run("""
            MERGE (c:Capacity {week: $week})
            SET c.own_staff_count  = toInteger($own_staff_count),
                c.hired_staff_count= toInteger($hired_staff_count),
                c.own_hours        = toFloat($own_hours),
                c.hired_hours      = toFloat($hired_hours),
                c.overtime_hours   = toFloat($overtime_hours),
                c.total_capacity   = toFloat($total_capacity),
                c.total_planned    = toFloat($total_planned),
                c.deficit          = toFloat($deficit)
        """, **r)
    print(f"✅ {len(rows)} Capacity nodes")

def load_workers(session, rows):
    for r in rows:
        session.run("""
            MERGE (w:Worker {worker_id: $worker_id})
            SET w.name          = $name,
                w.role          = $role,
                w.certifications= $certifications,
                w.hours_per_week= toInteger($hours_per_week),
                w.type          = $type
        """, worker_id=r["worker_id"],
             name=r["name"],
             role=r["role"],
             certifications=r["certifications"],
             hours_per_week=r["hours_per_week"],
             type=r["type"])
    print(f"✅ {len(rows)} Worker nodes")

# ── relationships ─────────────────────────────────────────────────────────────

def load_produces(session, rows):
    seen = set()
    count = 0
    for r in rows:
        key = (r["project_id"], r["product_type"])
        if key in seen:
            continue
        seen.add(key)
        session.run("""
            MATCH (p:Project  {project_id:  $project_id})
            MATCH (pr:Product {product_type: $product_type})
            MERGE (p)-[:PRODUCES]->(pr)
        """, project_id=r["project_id"],
             product_type=r["product_type"])
        count += 1
    print(f"✅ {count} PRODUCES relationships")

def load_scheduled_at(session, rows):
    for r in rows:
        session.run("""
            MATCH (p:Project {project_id:   $project_id})
            MATCH (s:Station {station_code: $station_code})
            MERGE (p)-[rel:SCHEDULED_AT {week: $week}]->(s)
            SET rel.planned_hours   = toFloat($planned_hours),
                rel.actual_hours    = toFloat($actual_hours),
                rel.completed_units = toInteger($completed_units),
                rel.bop             = $bop
        """, project_id=r["project_id"],
             station_code=r["station_code"],
             week=r["week"],
             planned_hours=r["planned_hours"],
             actual_hours=r["actual_hours"],
             completed_units=r["completed_units"],
             bop=r["bop"])
    print(f"✅ {len(rows)} SCHEDULED_AT relationships")

def load_runs_in(session, rows):
    seen = set()
    count = 0
    for r in rows:
        key = (r["project_id"], r["week"])
        if key in seen:
            continue
        seen.add(key)
        session.run("""
            MATCH (p:Project {project_id: $project_id})
            MATCH (wk:Week   {week:       $week})
            MERGE (p)-[:RUNS_IN]->(wk)
        """, project_id=r["project_id"], week=r["week"])
        count += 1
    print(f"✅ {count} RUNS_IN relationships")

def load_in_etapp(session, rows):
    seen = set()
    count = 0
    for r in rows:
        key = (r["project_id"], r["etapp"])
        if key in seen:
            continue
        seen.add(key)
        session.run("""
            MATCH (p:Project {project_id: $project_id})
            MATCH (e:Etapp   {etapp:      $etapp})
            MERGE (p)-[:IN_ETAPP]->(e)
        """, project_id=r["project_id"], etapp=r["etapp"])
        count += 1
    print(f"✅ {count} IN_ETAPP relationships")

def load_processed_at(session, rows):
    seen = set()
    count = 0
    for r in rows:
        key = (r["product_type"], r["station_code"])
        if key in seen:
            continue
        seen.add(key)
        session.run("""
            MATCH (pr:Product {product_type: $product_type})
            MATCH (s:Station  {station_code: $station_code})
            MERGE (pr)-[:PROCESSED_AT]->(s)
        """, product_type=r["product_type"],
             station_code=r["station_code"])
        count += 1
    print(f"✅ {count} PROCESSED_AT relationships")

def load_works_at(session, workers):
    count = 0
    for w in workers:
        primary = w["primary_station"].strip()
        if not primary or primary == "all":
            continue
        session.run("""
            MATCH (wk:Worker  {worker_id:   $worker_id})
            MATCH (s:Station  {station_code: $station_code})
            MERGE (wk)-[:WORKS_AT]->(s)
        """, worker_id=w["worker_id"], station_code=primary)
        count += 1
    print(f"✅ {count} WORKS_AT relationships")

def load_can_cover(session, workers):
    count = 0
    for w in workers:
        stations = [s.strip() for s in w["can_cover_stations"].split(",") if s.strip()]
        for station_code in stations:
            session.run("""
                MATCH (wk:Worker {worker_id:   $worker_id})
                MATCH (s:Station {station_code: $station_code})
                MERGE (wk)-[:CAN_COVER]->(s)
            """, worker_id=w["worker_id"], station_code=station_code)
            count += 1
    print(f"✅ {count} CAN_COVER relationships")

def load_available_in(session, workers, weeks):
    count = 0
    for w in workers:
        for week in weeks:
            session.run("""
                MATCH (wk:Worker {worker_id: $worker_id})
                MATCH (wknd:Week {week:      $week})
                MERGE (wk)-[:AVAILABLE_IN {hours_per_week: toInteger($hours_per_week)}]->(wknd)
            """, worker_id=w["worker_id"],
                 week=week,
                 hours_per_week=w["hours_per_week"])
            count += 1
    print(f"✅ {count} AVAILABLE_IN relationships")

def load_has_capacity(session, cap_rows):
    for r in cap_rows:
        session.run("""
            MATCH (wk:Week    {week: $week})
            MATCH (c:Capacity {week: $week})
            MERGE (wk)-[:HAS_CAPACITY]->(c)
        """, week=r["week"])
    print(f"✅ {len(cap_rows)} HAS_CAPACITY relationships")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n🚀 Starting graph seed...\n")

    prod    = read_csv("factory_production.csv")
    workers = read_csv("factory_workers.csv")
    cap     = read_csv("factory_capacity.csv")
    weeks   = sorted(set(r["week"] for r in prod) | set(r["week"] for r in cap))

    with driver.session() as session:
        print("── Creating constraints ──")
        create_constraints(session)

        print("\n── Loading nodes ──")
        load_projects(session, prod)
        load_products(session, prod)
        load_stations(session, prod)
        load_weeks(session, prod, cap)
        load_etapps(session, prod)
        load_capacity(session, cap)
        load_workers(session, workers)

        print("\n── Loading relationships ──")
        load_produces(session, prod)
        load_scheduled_at(session, prod)
        load_runs_in(session, prod)
        load_in_etapp(session, prod)
        load_processed_at(session, prod)
        load_works_at(session, workers)
        load_can_cover(session, workers)
        load_available_in(session, workers, weeks)
        load_has_capacity(session, cap)

    driver.close()
    print("\n✅ Graph seeded successfully!")
    print("Run this in Neo4j Browser to verify:")
    print("  MATCH (n) RETURN count(n) AS total_nodes")
    print("  MATCH ()-[r]->() RETURN count(r) AS total_relationships")

if __name__ == "__main__":
    main()