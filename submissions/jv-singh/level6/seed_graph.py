"""Seed the Level 6 factory knowledge graph into Neo4j.

Run this once after setting NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in
.env or in your shell. The script is idempotent: it uses Cypher MERGE and can
be run repeatedly without duplicating nodes/relationships.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PRODUCTION_CSV = DATA_DIR / "factory_production.csv"
WORKERS_CSV = DATA_DIR / "factory_workers.csv"
CAPACITY_CSV = DATA_DIR / "factory_capacity.csv"


def get_driver():
    load_dotenv(BASE_DIR / ".env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError(
            "Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USER, and "
            "NEO4J_PASSWORD in submissions/jv-singh/level6/.env."
        )
    return GraphDatabase.driver(uri, auth=(user, password))


def rows_from_csv(path: Path) -> list[dict]:
    frame = pd.read_csv(path).fillna("")
    return frame.to_dict("records")


def create_constraints(session) -> None:
    constraints = [
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
        "CREATE CONSTRAINT product_type IF NOT EXISTS FOR (p:Product) REQUIRE p.product_type IS UNIQUE",
        "CREATE CONSTRAINT station_code IF NOT EXISTS FOR (s:Station) REQUIRE s.station_code IS UNIQUE",
        "CREATE CONSTRAINT worker_id IF NOT EXISTS FOR (w:Worker) REQUIRE w.worker_id IS UNIQUE",
        "CREATE CONSTRAINT week_id IF NOT EXISTS FOR (w:Week) REQUIRE w.week IS UNIQUE",
        "CREATE CONSTRAINT etapp_name IF NOT EXISTS FOR (e:Etapp) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT bop_name IF NOT EXISTS FOR (b:BOP) REQUIRE b.name IS UNIQUE",
        "CREATE CONSTRAINT certification_name IF NOT EXISTS FOR (c:Certification) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT capacity_plan_id IF NOT EXISTS FOR (c:CapacityPlan) REQUIRE c.plan_id IS UNIQUE",
        "CREATE CONSTRAINT alert_id IF NOT EXISTS FOR (a:BottleneckAlert) REQUIRE a.alert_id IS UNIQUE",
    ]
    for statement in constraints:
        session.run(statement)


def load_production(session, rows: list[dict]) -> None:
    query = """
    UNWIND $rows AS row
    MERGE (project:Project {project_id: row.project_id})
      SET project.project_number = toString(row.project_number),
          project.name = row.project_name
    MERGE (product:Product {product_type: row.product_type})
      SET product.unit = row.unit
    MERGE (station:Station {station_code: toString(row.station_code)})
      SET station.name = row.station_name
    MERGE (week:Week {week: row.week})
      SET week.sort_order = toInteger(replace(row.week, 'w', ''))
    MERGE (etapp:Etapp {name: row.etapp})
    MERGE (bop:BOP {name: row.bop})

    MERGE (project)-[produces:PRODUCES]->(product)
      SET produces.quantity = toFloat(row.quantity),
          produces.unit = row.unit,
          produces.unit_factor = toFloat(row.unit_factor)
    MERGE (project)-[scheduled:SCHEDULED_AT {
        station_code: toString(row.station_code),
        week: row.week,
        product_type: row.product_type,
        etapp: row.etapp,
        bop: row.bop
    }]->(station)
      SET scheduled.planned_hours = toFloat(row.planned_hours),
          scheduled.actual_hours = toFloat(row.actual_hours),
          scheduled.completed_units = toInteger(row.completed_units),
          scheduled.quantity = toFloat(row.quantity),
          scheduled.variance_hours = toFloat(row.actual_hours) - toFloat(row.planned_hours),
          scheduled.variance_pct = CASE
              WHEN toFloat(row.planned_hours) = 0 THEN 0
              ELSE round(10000.0 * (toFloat(row.actual_hours) - toFloat(row.planned_hours)) / toFloat(row.planned_hours)) / 100.0
          END
    MERGE (project)-[work_week:HAS_WORK_IN {week: row.week}]->(week)
      ON CREATE SET work_week.planned_hours = 0, work_week.actual_hours = 0
      SET work_week.planned_hours = work_week.planned_hours + toFloat(row.planned_hours),
          work_week.actual_hours = work_week.actual_hours + toFloat(row.actual_hours)
    MERGE (project)-[:HAS_ETAPP]->(etapp)
    MERGE (project)-[:USES_BOP]->(bop)
    MERGE (product)-[requires:REQUIRES_STATION]->(station)
      ON CREATE SET requires.times_seen = 0
      SET requires.times_seen = requires.times_seen + 1
    MERGE (station)-[:ACTIVE_IN]->(week)
    """
    # Recompute aggregate relationships from scratch while preserving idempotency.
    session.run("MATCH (:Project)-[r:HAS_WORK_IN]->(:Week) DELETE r")
    session.run("MATCH (:Product)-[r:REQUIRES_STATION]->(:Station) DELETE r")
    session.run(query, rows=rows)

    alert_query = """
    UNWIND $rows AS row
    WITH row
    WHERE toFloat(row.actual_hours) > toFloat(row.planned_hours) * 1.10
    MERGE (alert:BottleneckAlert {alert_id: row.project_id + '-' + toString(row.station_code) + '-' + row.week})
      SET alert.kind = 'station_overrun',
          alert.message = row.project_name + ' exceeded plan at ' + row.station_name + ' in ' + row.week,
          alert.planned_hours = toFloat(row.planned_hours),
          alert.actual_hours = toFloat(row.actual_hours),
          alert.variance_pct = round(10000.0 * (toFloat(row.actual_hours) - toFloat(row.planned_hours)) / toFloat(row.planned_hours)) / 100.0
    MATCH (project:Project {project_id: row.project_id})
    MATCH (station:Station {station_code: toString(row.station_code)})
    MATCH (week:Week {week: row.week})
    MERGE (alert)-[:FLAGS_PROJECT]->(project)
    MERGE (alert)-[:FLAGS_STATION]->(station)
    MERGE (alert)-[:FLAGS_WEEK]->(week)
    """
    session.run(alert_query, rows=rows)


def load_workers(session, rows: list[dict]) -> None:
    query = """
    UNWIND $rows AS row
    MERGE (worker:Worker {worker_id: row.worker_id})
      SET worker.name = row.name,
          worker.role = row.role,
          worker.primary_station = row.primary_station,
          worker.hours_per_week = toInteger(row.hours_per_week),
          worker.type = row.type
    WITH worker, row,
         [station IN split(row.can_cover_stations, ',') WHERE trim(station) <> ''] AS cover_stations,
         [cert IN split(row.certifications, ',') WHERE trim(cert) <> ''] AS certifications
    FOREACH (station_code IN CASE WHEN row.primary_station <> 'all' THEN [row.primary_station] ELSE [] END |
      MERGE (primary:Station {station_code: toString(station_code)})
      ON CREATE SET primary.name = 'Station ' + toString(station_code)
      MERGE (worker)-[:PRIMARY_AT]->(primary)
    )
    FOREACH (station_code IN cover_stations |
      MERGE (covered:Station {station_code: toString(trim(station_code))})
      ON CREATE SET covered.name = 'Station ' + toString(trim(station_code))
      MERGE (worker)-[:CAN_COVER]->(covered)
    )
    FOREACH (cert_name IN certifications |
      MERGE (cert:Certification {name: trim(cert_name)})
      MERGE (worker)-[:HAS_CERTIFICATION]->(cert)
    )
    """
    session.run(query, rows=rows)


def load_capacity(session, rows: list[dict]) -> None:
    query = """
    UNWIND $rows AS row
    MERGE (week:Week {week: row.week})
      SET week.sort_order = toInteger(replace(row.week, 'w', ''))
    MERGE (plan:CapacityPlan {plan_id: 'capacity-' + row.week})
      SET plan.week = row.week,
          plan.own_staff_count = toInteger(row.own_staff_count),
          plan.hired_staff_count = toInteger(row.hired_staff_count),
          plan.own_hours = toFloat(row.own_hours),
          plan.hired_hours = toFloat(row.hired_hours),
          plan.overtime_hours = toFloat(row.overtime_hours),
          plan.total_capacity = toFloat(row.total_capacity),
          plan.total_planned = toFloat(row.total_planned),
          plan.deficit = toFloat(row.deficit),
          plan.is_deficit = toFloat(row.deficit) < 0
    MERGE (week)-[has_capacity:HAS_CAPACITY]->(plan)
      SET has_capacity.own_hours = toFloat(row.own_hours),
          has_capacity.hired_hours = toFloat(row.hired_hours),
          has_capacity.overtime_hours = toFloat(row.overtime_hours),
          has_capacity.total_capacity = toFloat(row.total_capacity),
          has_capacity.total_planned = toFloat(row.total_planned),
          has_capacity.deficit = toFloat(row.deficit)
    WITH row, week, plan
    OPTIONAL MATCH (project:Project)-[scheduled:SCHEDULED_AT {week: row.week}]->(station:Station)
    WITH row, week, plan, station, sum(scheduled.planned_hours) AS station_planned
    WHERE station IS NOT NULL
    MERGE (plan)-[pressure:CAPACITY_PRESSURE_ON {week: row.week}]->(station)
      SET pressure.station_planned_hours = station_planned,
          pressure.week_deficit = toFloat(row.deficit)
    """
    session.run("MATCH (:CapacityPlan)-[r:CAPACITY_PRESSURE_ON]->(:Station) DELETE r")
    session.run(query, rows=rows)

    deficit_alert_query = """
    UNWIND $rows AS row
    WITH row
    WHERE toFloat(row.deficit) < 0
    MERGE (alert:BottleneckAlert {alert_id: 'capacity-' + row.week})
      SET alert.kind = 'capacity_deficit',
          alert.message = 'Capacity deficit in ' + row.week,
          alert.total_capacity = toFloat(row.total_capacity),
          alert.total_planned = toFloat(row.total_planned),
          alert.deficit = toFloat(row.deficit)
    MATCH (week:Week {week: row.week})
    MERGE (alert)-[:FLAGS_WEEK]->(week)
    """
    session.run(deficit_alert_query, rows=rows)


def print_summary(session) -> None:
    summary = session.run(
        """
        MATCH (n)
        WITH count(n) AS nodes
        MATCH ()-[r]->()
        RETURN nodes, count(r) AS relationships
        """
    ).single()
    labels = session.run("CALL db.labels() YIELD label RETURN collect(label) AS labels").single()["labels"]
    rel_types = session.run(
        "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS rels"
    ).single()["rels"]
    print(f"Seed complete: {summary['nodes']} nodes, {summary['relationships']} relationships")
    print(f"Labels: {', '.join(sorted(labels))}")
    print(f"Relationship types: {', '.join(sorted(rel_types))}")


def main() -> None:
    production_rows = rows_from_csv(PRODUCTION_CSV)
    worker_rows = rows_from_csv(WORKERS_CSV)
    capacity_rows = rows_from_csv(CAPACITY_CSV)
    driver = get_driver()
    try:
        with driver.session() as session:
            create_constraints(session)
            load_production(session, production_rows)
            load_workers(session, worker_rows)
            load_capacity(session, capacity_rows)
            print_summary(session)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
