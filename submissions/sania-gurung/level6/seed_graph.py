#!/usr/bin/env python3
"""
seed_graph.py — Populate Neo4j factory knowledge graph from CSV data.
Idempotent: uses MERGE throughout, safe to run multiple times.

Usage:
    python seed_graph.py
"""

import os
import csv
from collections import defaultdict

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Constraints ──────────────────────────────────────────────────────────────

def create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project)     REQUIRE n.project_id   IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product)     REQUIRE n.product_type  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Station)     REQUIRE n.station_code  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Worker)      REQUIRE n.worker_id     IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Week)        REQUIRE n.week_id       IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Etapp)       REQUIRE n.etapp_id      IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Certification) REQUIRE n.name        IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Bottleneck)  REQUIRE n.station_code  IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("  Constraints created.")


# ── Core production nodes + relationships ────────────────────────────────────

def seed_production_nodes(session, rows):
    """Project, Product, Station, Etapp nodes + HAS_PRODUCT, USES_STATION,
    IN_ETAPP, PROCESSED_AT relationships."""
    for row in rows:
        session.run("""
            MERGE (proj:Project {project_id: $project_id})
              SET proj.project_number = $project_number,
                  proj.project_name   = $project_name,
                  proj.bop            = $bop

            MERGE (prod:Product {product_type: $product_type})
              SET prod.unit        = $unit,
                  prod.unit_factor = toFloat($unit_factor),
                  prod.quantity    = toInteger($quantity)

            MERGE (st:Station {station_code: $station_code})
              SET st.station_name = $station_name

            MERGE (et:Etapp {etapp_id: $etapp})

            MERGE (proj)-[:HAS_PRODUCT]->(prod)
            MERGE (proj)-[:USES_STATION]->(st)
            MERGE (proj)-[:IN_ETAPP]->(et)
            MERGE (prod)-[:PROCESSED_AT]->(st)
        """, **row)
    print(f"  Production nodes seeded ({len(rows)} rows).")


# ── SCHEDULED_AT (Project → Station, aggregated per week) ────────────────────

def seed_scheduled_at(session, rows):
    """One SCHEDULED_AT relationship per (project, station, week), with
    aggregated planned/actual hours across all product types."""
    agg = defaultdict(lambda: {"planned": 0.0, "actual": 0.0})
    for row in rows:
        key = (row["project_id"], row["station_code"], row["week"])
        agg[key]["planned"] += float(row["planned_hours"])
        agg[key]["actual"]  += float(row["actual_hours"])

    for (pid, scode, week), data in agg.items():
        session.run("""
            MATCH (proj:Project {project_id: $pid})
            MATCH (st:Station   {station_code: $scode})
            MERGE (proj)-[r:SCHEDULED_AT {week: $week}]->(st)
              SET r.planned_hours = $planned,
                  r.actual_hours  = $actual
        """, pid=pid, scode=scode, week=week,
             planned=round(data["planned"], 2),
             actual=round(data["actual"], 2))
    print(f"  SCHEDULED_AT relationships seeded ({len(agg)} entries).")


# ── Week nodes ───────────────────────────────────────────────────────────────

def seed_weeks(session, rows):
    for row in rows:
        session.run("""
            MERGE (wk:Week {week_id: $week})
              SET wk.own_staff_count   = toInteger($own_staff_count),
                  wk.hired_staff_count = toInteger($hired_staff_count),
                  wk.own_hours         = toInteger($own_hours),
                  wk.hired_hours       = toInteger($hired_hours),
                  wk.overtime_hours    = toInteger($overtime_hours),
                  wk.total_capacity    = toInteger($total_capacity),
                  wk.total_planned     = toInteger($total_planned),
                  wk.deficit           = toInteger($deficit)
        """, **row)
    print(f"  Week nodes seeded ({len(rows)} weeks).")


# ── Workers, certifications, coverage ────────────────────────────────────────

def seed_workers(session, rows):
    station_certs = defaultdict(set)

    for row in rows:
        session.run("""
            MERGE (w:Worker {worker_id: $worker_id})
              SET w.name            = $name,
                  w.role            = $role,
                  w.type            = $type,
                  w.hours_per_week  = toInteger($hours_per_week),
                  w.primary_station = $primary_station
        """, **row)

        primary = row["primary_station"].strip()

        # ASSIGNED_TO primary station (skip "all" — Victor Elm, Foreman)
        if primary != "all":
            session.run("""
                MATCH (w:Worker  {worker_id:   $wid})
                MERGE (st:Station {station_code: $scode})
                MERGE (w)-[:ASSIGNED_TO]->(st)
            """, wid=row["worker_id"], scode=primary)

        # CAN_COVER
        for scode in row["can_cover_stations"].split(","):
            scode = scode.strip()
            if scode:
                session.run("""
                    MATCH (w:Worker  {worker_id:   $wid})
                    MERGE (st:Station {station_code: $scode})
                    MERGE (w)-[:CAN_COVER]->(st)
                """, wid=row["worker_id"], scode=scode)

        # HAS_CERTIFICATION
        for cert in row["certifications"].split(","):
            cert = cert.strip()
            if cert:
                session.run("""
                    MATCH (w:Worker {worker_id: $wid})
                    MERGE (c:Certification {name: $cert})
                    MERGE (w)-[:HAS_CERTIFICATION]->(c)
                """, wid=row["worker_id"], cert=cert)

                # Track which certs belong to which primary station
                if primary != "all":
                    station_certs[primary].add(cert)

    # REQUIRES_CERT: station requires certifications held by its primary worker(s)
    for scode, certs in station_certs.items():
        for cert in certs:
            session.run("""
                MERGE (st:Station {station_code: $scode})
                MERGE (c:Certification {name: $cert})
                MERGE (st)-[:REQUIRES_CERT]->(c)
            """, scode=scode, cert=cert)

    print(f"  Workers seeded ({len(rows)} workers, REQUIRES_CERT from {len(station_certs)} stations).")


# ── Bottleneck nodes ─────────────────────────────────────────────────────────

def seed_bottlenecks(session, rows):
    """Create Bottleneck nodes for stations with 2+ overrun production events."""
    overruns = defaultdict(list)
    for row in rows:
        planned = float(row["planned_hours"])
        actual  = float(row["actual_hours"])
        if planned > 0 and actual > planned * 1.10:
            pct = round((actual - planned) / planned * 100, 1)
            overruns[row["station_code"]].append({"week": row["week"], "pct": pct})

    count = 0
    for scode, events in overruns.items():
        if len(events) >= 2:
            avg_pct  = round(sum(e["pct"] for e in events) / len(events), 1)
            severity = "CRITICAL" if avg_pct > 20 else ("HIGH" if avg_pct > 10 else "MEDIUM")
            n_weeks  = len(set(e["week"] for e in events))
            session.run("""
                MERGE (b:Bottleneck {station_code: $scode})
                  SET b.avg_overrun_pct = $avg_pct,
                      b.severity        = $severity,
                      b.overrun_count   = $count,
                      b.overrun_weeks   = $n_weeks
                WITH b
                MATCH (st:Station {station_code: $scode})
                MERGE (st)-[:HAS_BOTTLENECK]->(b)
            """, scode=scode, avg_pct=avg_pct, severity=severity,
                 count=len(events), n_weeks=n_weeks)
            count += 1

    print(f"  Bottleneck nodes seeded ({count} stations flagged).")


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(driver):
    with driver.session() as s:
        nodes    = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels     = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels   = s.run("CALL db.labels() YIELD label RETURN count(label) AS c").single()["c"]
        reltypes = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN count(relationshipType) AS c"
        ).single()["c"]

    print(f"\n{'─'*50}")
    print(f"  Graph summary")
    print(f"  Nodes         : {nodes}")
    print(f"  Relationships : {rels}")
    print(f"  Node labels   : {labels}")
    print(f"  Rel types     : {reltypes}")
    print(f"{'─'*50}")

    ok = nodes >= 50 and rels >= 100 and labels >= 6 and reltypes >= 8
    if ok:
        print("  All self-test thresholds met.")
    else:
        print("  WARNING: some thresholds not met — check data above.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not URI or not PASSWORD:
        raise ValueError(
            "NEO4J_URI and NEO4J_PASSWORD must be set in .env or environment."
        )

    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    print("Loading CSV files...")
    production = load_csv("factory_production.csv")
    workers    = load_csv("factory_workers.csv")
    capacity   = load_csv("factory_capacity.csv")

    print("Seeding graph...")
    with driver.session() as session:
        create_constraints(session)
        seed_production_nodes(session, production)
        seed_scheduled_at(session, production)
        seed_weeks(session, capacity)
        seed_workers(session, workers)
        seed_bottlenecks(session, production)

    print_summary(driver)
    driver.close()
    print("\nDone. Graph is ready.")


if __name__ == "__main__":
    main()
