"""
seed_graph.py — Factory Knowledge Graph Seeder
Level 6 Submission: Harshit Kumar (hrk0503)

Populates Neo4j Aura with factory data from 3 CSV files:
  - factory_production.csv  (68 rows)
  - factory_workers.csv     (13 workers)
  - factory_capacity.csv    (8 weeks)

Usage:
  python seed_graph.py

Idempotent: uses MERGE throughout, safe to run multiple times.
"""

import os
import csv
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ── Neo4j connection ──────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI",      "neo4j+s://your-aura-instance.databases.neo4j.io")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password-here")

# ── Data paths ────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent.parent.parent / "challenges" / "data"
PRODUCTION_CSV = DATA_DIR / "factory_production.csv"
WORKERS_CSV    = DATA_DIR / "factory_workers.csv"
CAPACITY_CSV   = DATA_DIR / "factory_capacity.csv"


def create_constraints(session):
    """Create uniqueness constraints before loading data."""
    constraints = [
        "CREATE CONSTRAINT project_id   IF NOT EXISTS FOR (p:Project)  REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT product_type  IF NOT EXISTS FOR (p:Product)  REQUIRE p.type IS UNIQUE",
        "CREATE CONSTRAINT station_code  IF NOT EXISTS FOR (s:Station)  REQUIRE s.code IS UNIQUE",
        "CREATE CONSTRAINT worker_id     IF NOT EXISTS FOR (w:Worker)   REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT week_id       IF NOT EXISTS FOR (w:Week)     REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT etapp_name    IF NOT EXISTS FOR (e:Etapp)    REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT bop_name      IF NOT EXISTS FOR (b:BOP)      REQUIRE b.name IS UNIQUE",
    ]
    for cypher in constraints:
        session.run(cypher)
    print("  Constraints created.")


def load_production(session, filepath):
    """Load factory_production.csv into the graph."""
    rows = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "project_id":    row["project_id"].strip(),
                "project_number": row["project_number"].strip(),
                "project_name":  row["project_name"].strip(),
                "product_type":  row["product_type"].strip(),
                "unit":          row["unit"].strip(),
                "quantity":      float(row["quantity"]),
                "unit_factor":   float(row["unit_factor"]),
                "station_code":  row["station_code"].strip(),
                "station_name":  row["station_name"].strip(),
                "etapp":         row["etapp"].strip(),
                "bop":           row["bop"].strip(),
                "week":          row["week"].strip(),
                "planned_hours": float(row["planned_hours"]),
                "actual_hours":  float(row["actual_hours"]),
                "completed_units": int(row["completed_units"]),
            })

    # Merge nodes and core relationships
    session.run("""
        UNWIND $rows AS row

        // ── Project ──
        MERGE (p:Project {id: row.project_id})
          ON CREATE SET
            p.number = row.project_number,
            p.name   = row.project_name

        // ── Product ──
        MERGE (pr:Product {type: row.product_type})
          ON CREATE SET
            pr.unit        = row.unit,
            pr.unit_factor = row.unit_factor

        // ── Station ──
        MERGE (st:Station {code: row.station_code})
          ON CREATE SET st.name = row.station_name

        // ── Week ──
        MERGE (wk:Week {id: row.week})

        // ── Etapp ──
        MERGE (et:Etapp {name: row.etapp})

        // ── BOP ──
        MERGE (b:BOP {name: row.bop})

        // ── PRODUCES relationship (project-level aggregate) ──
        MERGE (p)-[prod:PRODUCES {product_type: row.product_type}]->(pr)
          ON CREATE SET
            prod.quantity = row.quantity,
            prod.unit     = row.unit

        // ── SCHEDULED_AT (core fact: project × station × week) ──
        MERGE (p)-[sched:SCHEDULED_AT {week: row.week, station_code: row.station_code}]->(st)
          ON CREATE SET
            sched.planned_hours    = row.planned_hours,
            sched.actual_hours     = row.actual_hours,
            sched.completed_units  = row.completed_units

        // ── Context relationships ──
        MERGE (p)-[:IN_WEEK]->(wk)
        MERGE (p)-[:BELONGS_TO]->(et)
        MERGE (p)-[:PART_OF]->(b)
    """, rows=rows)

    print(f"  Loaded {len(rows)} production rows.")


def load_workers(session, filepath):
    """Load factory_workers.csv into the graph."""
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            worker = {
                "id":             row["worker_id"].strip(),
                "name":           row["name"].strip(),
                "role":           row["role"].strip(),
                "primary_station": row["primary_station"].strip(),
                "certifications": row["certifications"].strip(),
                "hours_per_week": int(row["hours_per_week"]),
                "worker_type":    row["type"].strip(),
                "can_cover":      [s.strip() for s in row["can_cover_stations"].split(",") if s.strip()],
            }

            # Create/merge Worker node
            session.run("""
                MERGE (w:Worker {id: $id})
                  ON CREATE SET
                    w.name           = $name,
                    w.role           = $role,
                    w.certifications = $certifications,
                    w.hours_per_week = $hours_per_week,
                    w.type           = $worker_type
            """, **worker)

            # WORKS_AT primary station
            session.run("""
                MATCH (w:Worker {id: $worker_id})
                MATCH (s:Station {code: $station_code})
                MERGE (w)-[:WORKS_AT]->(s)
            """, worker_id=worker["id"], station_code=worker["primary_station"])

            # CAN_COVER all listed stations
            for station_code in worker["can_cover"]:
                session.run("""
                    MATCH (w:Worker {id: $worker_id})
                    MATCH (s:Station {code: $station_code})
                    MERGE (w)-[:CAN_COVER]->(s)
                """, worker_id=worker["id"], station_code=station_code)

    print("  Loaded workers and coverage relationships.")


def load_capacity(session, filepath):
    """Load factory_capacity.csv into the graph."""
    rows = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "week":             row["week"].strip(),
                "own_staff_count":  int(row["own_staff_count"]),
                "hired_staff_count": int(row["hired_staff_count"]),
                "own_hours":        int(row["own_hours"]),
                "hired_hours":      int(row["hired_hours"]),
                "overtime_hours":   int(row["overtime_hours"]),
                "total_capacity":   int(row["total_capacity"]),
                "total_planned":    int(row["total_planned"]),
                "deficit":          int(row["deficit"]),
            })

    session.run("""
        UNWIND $rows AS row
        MERGE (wk:Week {id: row.week})
        MERGE (cap:Capacity {week: row.week})
          ON CREATE SET
            cap.own_staff_count   = row.own_staff_count,
            cap.hired_staff_count  = row.hired_staff_count,
            cap.own_hours         = row.own_hours,
            cap.hired_hours       = row.hired_hours,
            cap.overtime_hours    = row.overtime_hours,
            cap.total_capacity    = row.total_capacity,
            cap.total_planned     = row.total_planned,
            cap.deficit           = row.deficit
        MERGE (wk)-[:HAS_CAPACITY]->(cap)
    """, rows=rows)

    print(f"  Loaded {len(rows)} capacity weeks.")


def add_bottleneck_relationships(session):
    """
    Derived relationship: mark project-station pairs where actual > planned by >10%.
    This is computed post-load, not from raw CSV.
    """
    session.run("""
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WHERE r.actual_hours > r.planned_hours * 1.1
        MERGE (p)-[b:BOTTLENECK {week: r.week}]->(s)
          ON CREATE SET
            b.variance_pct = round(
              (r.actual_hours - r.planned_hours) / r.planned_hours * 100, 1
            ),
            b.severity = CASE
              WHEN r.actual_hours > r.planned_hours * 1.25 THEN "CRITICAL"
              WHEN r.actual_hours > r.planned_hours * 1.15 THEN "HIGH"
              ELSE "MEDIUM"
            END
    """)
    print("  Bottleneck relationships computed.")


def verify_graph(session):
    """Print a summary of what was loaded."""
    result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC")
    print("\n  Node counts:")
    for record in result:
        print(f"    {record['label']}: {record['count']}")

    result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY count DESC")
    print("\n  Relationship counts:")
    for record in result:
        print(f"    {record['rel_type']}: {record['count']}")

    total_nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    total_rels  = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    print(f"\n  Total: {total_nodes} nodes, {total_rels} relationships")


def main():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        driver.verify_connectivity()
        print("  Connected successfully.")
    except Exception as e:
        print(f"  Connection failed: {e}")
        return

    with driver.session() as session:
        print("\nCreating constraints...")
        create_constraints(session)

        print("\nLoading production data...")
        load_production(session, PRODUCTION_CSV)

        print("\nLoading worker data...")
        load_workers(session, WORKERS_CSV)

        print("\nLoading capacity data...")
        load_capacity(session, CAPACITY_CSV)

        print("\nComputing bottleneck relationships...")
        add_bottleneck_relationships(session)

        print("\nVerifying graph...")
        verify_graph(session)

    driver.close()
    print("\nDone. Graph is ready.")


if __name__ == "__main__":
    main()
