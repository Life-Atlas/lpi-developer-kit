"""
seed_graph.py — Populate Neo4j with factory production data.

Run once:  python seed_graph.py
Idempotent: safe to re-run (clears graph, then uses MERGE).
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_csv(filename):
    """Read a CSV file from the data/ directory and return a list of dicts."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run(session, query, **kwargs):
    """Run a Cypher query and return the result summary."""
    return session.run(query, **kwargs)


# ── Seeding phases ───────────────────────────────────────────────────────────

def create_constraints(session):
    """Phase 1: Uniqueness constraints for idempotent MERGE."""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project)       REQUIRE p.project_id   IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station)       REQUIRE s.station_code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker)        REQUIRE w.worker_id    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week)         REQUIRE wk.week_id     IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (prod:Product)    REQUIRE prod.product_type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Certification) REQUIRE c.cert_name    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp)         REQUIRE e.etapp_name   IS UNIQUE",
    ]
    for c in constraints:
        run(session, c)
    print("  Created 7 uniqueness constraints")


def seed_production(session, rows):
    """Phase 3: Nodes and relationships from factory_production.csv."""

    # ── Nodes ──
    run(session, """
        UNWIND $rows AS row
        MERGE (p:Project {project_id: row.project_id})
        SET p.project_number = row.project_number,
            p.project_name   = row.project_name
    """, rows=rows)

    run(session, """
        UNWIND $rows AS row
        MERGE (:Product {product_type: row.product_type, unit: row.unit})
    """, rows=rows)

    run(session, """
        UNWIND $rows AS row
        MERGE (s:Station {station_code: row.station_code})
        SET s.station_name = row.station_name
    """, rows=rows)

    run(session, """
        UNWIND $rows AS row
        MERGE (:Week {week_id: row.week})
    """, rows=rows)

    run(session, """
        UNWIND $rows AS row
        MERGE (:Etapp {etapp_name: row.etapp})
    """, rows=rows)

    # ── Relationships ──
    # PRODUCES — one per unique (project_id, product_type)
    run(session, """
        UNWIND $rows AS row
        MATCH (p:Project {project_id: row.project_id})
        MATCH (prod:Product {product_type: row.product_type})
        MERGE (p)-[r:PRODUCES]->(prod)
        SET r.quantity    = toInteger(row.quantity),
            r.unit_factor = toFloat(row.unit_factor),
            r.unit        = row.unit
    """, rows=rows)

    # SCHEDULED_AT — composite key includes product_type to avoid P05/018 collision
    run(session, """
        UNWIND $rows AS row
        MATCH (p:Project {project_id: row.project_id})
        MATCH (s:Station {station_code: row.station_code})
        MERGE (p)-[r:SCHEDULED_AT {
            week:         row.week,
            etapp:        row.etapp,
            bop:          row.bop,
            product_type: row.product_type
        }]->(s)
        SET r.planned_hours   = toFloat(row.planned_hours),
            r.actual_hours    = toFloat(row.actual_hours),
            r.completed_units = toInteger(row.completed_units),
            r.variance_pct    = CASE
                WHEN toFloat(row.planned_hours) > 0
                THEN round((toFloat(row.actual_hours) - toFloat(row.planned_hours))
                     / toFloat(row.planned_hours) * 100, 1)
                ELSE 0.0
            END
    """, rows=rows)

    # ACTIVE_IN — project ↔ week
    run(session, """
        UNWIND $rows AS row
        MATCH (p:Project {project_id: row.project_id})
        MATCH (wk:Week {week_id: row.week})
        MERGE (p)-[:ACTIVE_IN]->(wk)
    """, rows=rows)

    # IN_PHASE — project ↔ etapp
    run(session, """
        UNWIND $rows AS row
        MATCH (p:Project {project_id: row.project_id})
        MATCH (e:Etapp {etapp_name: row.etapp})
        MERGE (p)-[:IN_PHASE]->(e)
    """, rows=rows)

    print(f"  Loaded {len(rows)} production rows → nodes + relationships")


def seed_workers(session, rows):
    """Phase 4: Nodes and relationships from factory_workers.csv."""

    # Pre-process: split comma-separated fields in Python
    worker_data = []
    for w in rows:
        certs = [c.strip() for c in w["certifications"].split(",")]
        cover = [s.strip() for s in w["can_cover_stations"].split(",")]
        worker_data.append({
            "worker_id":       w["worker_id"],
            "name":            w["name"],
            "role":            w["role"],
            "primary_station": w["primary_station"],
            "hours_per_week":  int(w["hours_per_week"]),
            "type":            w["type"],
            "certifications":  certs,
            "can_cover":       cover,
        })

    # Worker nodes
    run(session, """
        UNWIND $rows AS row
        MERGE (w:Worker {worker_id: row.worker_id})
        SET w.name           = row.name,
            w.role           = row.role,
            w.hours_per_week = row.hours_per_week,
            w.type           = row.type
    """, rows=worker_data)

    # Certification nodes + HOLDS
    run(session, """
        UNWIND $rows AS row
        MATCH (w:Worker {worker_id: row.worker_id})
        UNWIND row.certifications AS cert
        MERGE (c:Certification {cert_name: cert})
        MERGE (w)-[:HOLDS]->(c)
    """, rows=worker_data)

    # WORKS_AT — skip W11 (primary_station = "all")
    run(session, """
        UNWIND $rows AS row
        WITH row WHERE row.primary_station <> 'all'
        MATCH (w:Worker {worker_id: row.worker_id})
        MATCH (s:Station {station_code: row.primary_station})
        MERGE (w)-[:WORKS_AT]->(s)
    """, rows=worker_data)

    # CAN_COVER
    run(session, """
        UNWIND $rows AS row
        MATCH (w:Worker {worker_id: row.worker_id})
        UNWIND row.can_cover AS sc
        MATCH (s:Station {station_code: sc})
        MERGE (w)-[:CAN_COVER]->(s)
    """, rows=worker_data)

    print(f"  Loaded {len(rows)} workers → Workers, Certifications + relationships")


def seed_capacity(session, rows):
    """Phase 5: HAS_CAPACITY relationships from factory_capacity.csv."""

    cap_data = []
    for c in rows:
        cap_data.append({
            "week":           c["week"],
            "own_hours":      int(c["own_hours"]),
            "hired_hours":    int(c["hired_hours"]),
            "overtime_hours": int(c["overtime_hours"]),
            "total_planned":  int(c["total_planned"]),
            "deficit":        int(c["deficit"]),
        })

    run(session, """
        UNWIND $rows AS row
        MERGE (wk:Week {week_id: row.week})
        MATCH (f:Factory)
        MERGE (wk)-[r:HAS_CAPACITY]->(f)
        SET r.own_hours      = row.own_hours,
            r.hired_hours    = row.hired_hours,
            r.overtime_hours = row.overtime_hours,
            r.total_planned  = row.total_planned,
            r.deficit        = row.deficit
    """, rows=cap_data)

    print(f"  Loaded {len(rows)} capacity rows → HAS_CAPACITY")


def compute_loaded_in(session):
    """Phase 6: Aggregate SCHEDULED_AT into LOADED_IN per (station, week)."""
    run(session, """
        MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
        WITH s, r.week AS week,
             sum(r.planned_hours) AS tp,
             sum(r.actual_hours)  AS ta
        MATCH (wk:Week {week_id: week})
        MERGE (s)-[l:LOADED_IN]->(wk)
        SET l.total_planned = tp,
            l.total_actual  = ta
    """)
    print("  Computed LOADED_IN aggregations")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Factory Knowledge Graph — Seeder")
    print("=" * 55)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("Connected to Neo4j\n")

    # Read CSVs
    production = read_csv("factory_production.csv")
    workers    = read_csv("factory_workers.csv")
    capacity   = read_csv("factory_capacity.csv")

    with driver.session() as session:
        # Phase 0: Clear
        run(session, "MATCH (n) DETACH DELETE n")
        print("Cleared existing graph\n")

        # Phase 1: Constraints
        create_constraints(session)

        # Phase 2: Factory singleton
        run(session, 'MERGE (:Factory {factory_name: "VSAB Stålbyggnad"})')
        print("  Created Factory node")

        # Phase 3–6
        seed_production(session, production)
        seed_workers(session, workers)
        seed_capacity(session, capacity)
        compute_loaded_in(session)

    # ── Summary ──
    with driver.session() as session:
        nodes     = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels      = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels    = session.run("CALL db.labels() YIELD label RETURN collect(label) AS l").single()["l"]
        rel_types = session.run(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS t"
        ).single()["t"]

    print(f"\n{'=' * 55}")
    print(f"  Seeding complete!")
    print(f"     Nodes:              {nodes}")
    print(f"     Relationships:      {rels}")
    print(f"     Labels ({len(labels)}):        {labels}")
    print(f"     Rel types ({len(rel_types)}):     {rel_types}")
    print(f"{'=' * 55}")

    driver.close()


if __name__ == "__main__":
    main()
