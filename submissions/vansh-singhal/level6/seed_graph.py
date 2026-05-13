import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")


def normalize_station(code) -> str:
    """Normalize station code to 3-digit zero-padded string. e.g. 11 → '011'"""
    try:
        return f"{int(str(code).strip()):03d}"
    except (ValueError, TypeError):
        return str(code).strip()


def create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project)       REQUIRE p.project_id    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station)       REQUIRE s.station_code  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product)       REQUIRE p.product_type  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker)        REQUIRE w.worker_id     IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Week)          REQUIRE w.week_id       IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Certification) REQUIRE c.name          IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp)         REQUIRE e.etapp_id      IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("✓ Constraints created")


def seed_projects(session, prod: pd.DataFrame):
    rows = prod[["project_id", "project_number", "project_name"]].drop_duplicates()
    for _, row in rows.iterrows():
        session.run(
            """
            MERGE (p:Project {project_id: $project_id})
            SET p.project_number = $project_number,
                p.project_name   = $project_name,
                p.name           = $project_name
            """,
            project_id=row["project_id"],
            project_number=int(row["project_number"]),
            project_name=row["project_name"],
        )
    print(f"✓ {len(rows)} Project nodes")


def seed_stations(session, prod: pd.DataFrame):
    rows = prod[["station_code", "station_name"]].drop_duplicates()
    for _, row in rows.iterrows():
        session.run(
            """
            MERGE (s:Station {station_code: $station_code})
            SET s.station_name = $station_name,
                s.name         = $station_name
            """,
            station_code=row["station_code"],
            station_name=row["station_name"],
        )
    print(f"✓ {len(rows)} Station nodes")


def seed_products(session, prod: pd.DataFrame):
    rows = prod[["product_type", "unit"]].drop_duplicates()
    for _, row in rows.iterrows():
        session.run(
            """
            MERGE (p:Product {product_type: $product_type})
            SET p.unit = $unit,
                p.name = $product_type
            """,
            product_type=row["product_type"],
            unit=row["unit"],
        )
    print(f"✓ {len(rows)} Product nodes")


def seed_etapps(session, prod: pd.DataFrame):
    for etapp in prod["etapp"].unique():
        session.run(
            "MERGE (e:Etapp {etapp_id: $etapp_id})",
            etapp_id=etapp,
        )
    print(f"✓ {prod['etapp'].nunique()} Etapp nodes")


def seed_weeks(session, capacity: pd.DataFrame):
    for _, row in capacity.iterrows():
        session.run(
            """
            MERGE (w:Week {week_id: $week_id})
            SET w.own_staff_count   = $own_staff_count,
                w.hired_staff_count = $hired_staff_count,
                w.own_hours         = $own_hours,
                w.hired_hours       = $hired_hours,
                w.overtime_hours    = $overtime_hours,
                w.total_capacity    = $total_capacity,
                w.total_planned     = $total_planned,
                w.deficit           = $deficit
            """,
            week_id=row["week"],
            own_staff_count=int(row["own_staff_count"]),
            hired_staff_count=int(row["hired_staff_count"]),
            own_hours=int(row["own_hours"]),
            hired_hours=int(row["hired_hours"]),
            overtime_hours=int(row["overtime_hours"]),
            total_capacity=int(row["total_capacity"]),
            total_planned=int(row["total_planned"]),
            deficit=int(row["deficit"]),
        )
    print(f"✓ {len(capacity)} Week nodes")


def seed_workers_and_certs(session, workers: pd.DataFrame):
    for _, row in workers.iterrows():
        # Worker node
        session.run(
            """
            MERGE (w:Worker {worker_id: $worker_id})
            SET w.name          = $name,
                w.role          = $role,
                w.hours_per_week = $hours_per_week,
                w.type          = $type
            """,
            worker_id=row["worker_id"],
            name=row["name"],
            role=row["role"],
            hours_per_week=int(row["hours_per_week"]),
            type=row["type"],
        )

        # Certifications + HAS_CERTIFICATION
        for cert in str(row["certifications"]).split(","):
            cert = cert.strip()
            if not cert:
                continue
            session.run(
                """
                MERGE (c:Certification {name: $cert})
                WITH c
                MATCH (w:Worker {worker_id: $worker_id})
                MERGE (w)-[:HAS_CERTIFICATION]->(c)
                """,
                cert=cert,
                worker_id=row["worker_id"],
            )

        # WORKS_AT (primary station — skip "all")
        primary = str(row["primary_station"]).strip()
        if primary != "all":
            sc = normalize_station(primary)
            session.run(
                """
                MATCH (w:Worker  {worker_id:   $wid})
                MATCH (s:Station {station_code: $sc})
                MERGE (w)-[:WORKS_AT]->(s)
                """,
                wid=row["worker_id"],
                sc=sc,
            )

        # CAN_COVER
        for station in str(row["can_cover_stations"]).split(","):
            sc = normalize_station(station.strip())
            session.run(
                """
                MATCH (w:Worker  {worker_id:   $wid})
                MATCH (s:Station {station_code: $sc})
                MERGE (w)-[:CAN_COVER]->(s)
                """,
                wid=row["worker_id"],
                sc=sc,
            )

    print(f"✓ {len(workers)} Worker nodes + certifications + WORKS_AT + CAN_COVER")


def seed_relationships(session, prod: pd.DataFrame):
    rel_counts = {"BELONGS_TO": 0, "PRODUCES": 0, "PROCESSED_AT": 0,
                  "SCHEDULED_AT": 0, "SCHEDULED_IN": 0}

    # BELONGS_TO (Project → Etapp)
    for _, row in prod[["project_id", "etapp"]].drop_duplicates().iterrows():
        session.run(
            """
            MATCH (p:Project {project_id: $pid})
            MATCH (e:Etapp   {etapp_id:   $eid})
            MERGE (p)-[:BELONGS_TO]->(e)
            """,
            pid=row["project_id"],
            eid=row["etapp"],
        )
        rel_counts["BELONGS_TO"] += 1

    # PRODUCES (Project → Product)
    for _, row in prod[["project_id", "product_type", "quantity",
                         "unit_factor", "unit"]].drop_duplicates(
                             subset=["project_id", "product_type"]).iterrows():
        session.run(
            """
            MATCH (p:Project {project_id:  $pid})
            MATCH (d:Product {product_type: $ptype})
            MERGE (p)-[r:PRODUCES]->(d)
            SET r.quantity    = $qty,
                r.unit_factor = $uf,
                r.unit        = $unit
            """,
            pid=row["project_id"],
            ptype=row["product_type"],
            qty=float(row["quantity"]),
            uf=float(row["unit_factor"]),
            unit=row["unit"],
        )
        rel_counts["PRODUCES"] += 1

    # PROCESSED_AT (Product → Station)
    for _, row in prod[["product_type", "station_code"]].drop_duplicates().iterrows():
        session.run(
            """
            MATCH (d:Product {product_type:  $ptype})
            MATCH (s:Station {station_code:  $sc})
            MERGE (d)-[:PROCESSED_AT]->(s)
            """,
            ptype=row["product_type"],
            sc=row["station_code"],
        )
        rel_counts["PROCESSED_AT"] += 1

    # SCHEDULED_AT (Project → Station, one per production row)
    for _, row in prod.iterrows():
        session.run(
            """
            MATCH (p:Project {project_id:  $pid})
            MATCH (s:Station {station_code: $sc})
            MERGE (p)-[r:SCHEDULED_AT {week: $week, product_type: $ptype}]->(s)
            SET r.planned_hours    = $planned,
                r.actual_hours     = $actual,
                r.completed_units  = $completed,
                r.etapp            = $etapp,
                r.bop              = $bop
            """,
            pid=row["project_id"],
            sc=row["station_code"],
            week=row["week"],
            ptype=row["product_type"],
            planned=float(row["planned_hours"]),
            actual=float(row["actual_hours"]),
            completed=int(row["completed_units"]),
            etapp=row["etapp"],
            bop=row["bop"],
        )
        rel_counts["SCHEDULED_AT"] += 1

    # SCHEDULED_IN (Project → Week)
    for _, row in prod[["project_id", "week"]].drop_duplicates().iterrows():
        session.run(
            """
            MATCH (p:Project {project_id: $pid})
            MATCH (w:Week    {week_id:    $wid})
            MERGE (p)-[:SCHEDULED_IN]->(w)
            """,
            pid=row["project_id"],
            wid=row["week"],
        )
        rel_counts["SCHEDULED_IN"] += 1

    for rel, n in rel_counts.items():
        print(f"  {rel}: {n}")
    print(f"✓ Relationships seeded")


def print_summary(session):
    nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    rels  = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    labels = [r["label"] for r in session.run("CALL db.labels() YIELD label")]
    rel_types = [r["relationshipType"] for r in
                 session.run("CALL db.relationshipTypes() YIELD relationshipType")]
    print(f"\n── Graph Summary ──────────────────────")
    print(f"  Nodes:              {nodes}")
    print(f"  Relationships:      {rels}")
    print(f"  Node labels ({len(labels)}):   {labels}")
    print(f"  Rel types   ({len(rel_types)}):   {rel_types}")
    print(f"───────────────────────────────────────")


def seed():
    # Load CSVs
    prod     = pd.read_csv("factory_production.csv")
    workers  = pd.read_csv("factory_workers.csv")
    capacity = pd.read_csv("factory_capacity.csv")

    # Normalize station codes to "011" format
    prod["station_code"] = prod["station_code"].apply(normalize_station)

    print("\n🔌 Connecting to Neo4j…")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as s:
        print("\n📐 Creating constraints…")
        create_constraints(s)

        print("\n🌱 Seeding nodes…")
        seed_projects(s, prod)
        seed_stations(s, prod)
        seed_products(s, prod)
        seed_etapps(s, prod)
        seed_weeks(s, capacity)
        seed_workers_and_certs(s, workers)

        print("\n🔗 Seeding relationships…")
        seed_relationships(s, prod)

        print("\n📊 Final graph state…")
        print_summary(s)

    driver.close()
    print("\n✅ Done — graph is ready!\n")


if __name__ == "__main__":
    seed()