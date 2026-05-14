import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PWD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PWD))


def seed_data():
    # Load CSVs
    prod_df = pd.read_csv('factory_production.csv')
    workers_df = pd.read_csv('factory_workers.csv')
    cap_df = pd.read_csv('factory_capacity.csv')

    with driver.session() as session:
        # ── 1. Constraints ──────────────────────────────────────────────
        session.run("CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE")
        session.run("CREATE CONSTRAINT station_code IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE")
        session.run("CREATE CONSTRAINT worker_id IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE")
        session.run("CREATE CONSTRAINT week_id IF NOT EXISTS FOR (wk:Week) REQUIRE wk.id IS UNIQUE")
        session.run("CREATE CONSTRAINT cert_name IF NOT EXISTS FOR (c:Certification) REQUIRE c.name IS UNIQUE")
        session.run("CREATE CONSTRAINT etapp_id IF NOT EXISTS FOR (e:Etapp) REQUIRE e.id IS UNIQUE")

        # ── 2. Seed Workers, Certifications, and Station assignments ───
        for _, row in workers_df.iterrows():
            # Worker + certifications
            session.run("""
                MERGE (w:Worker {id: $id})
                SET w.name = $name, w.role = $role, w.hours_per_week = $hours, w.type = $type
                WITH w
                UNWIND split($certs, ',') AS cert_name
                MERGE (c:Certification {name: trim(cert_name)})
                MERGE (w)-[:HAS_CERT]->(c)
            """, id=row['worker_id'], name=row['name'], role=row['role'],
               hours=row['hours_per_week'], type=row['type'], certs=row['certifications'])

            # Primary station
            session.run("""
                MATCH (w:Worker {id: $id})
                MERGE (s:Station {code: $s_code})
                MERGE (w)-[:WORKS_AT {primary: true}]->(s)
            """, id=row['worker_id'], s_code=str(row['primary_station']).zfill(3))

            # Coverage stations
            for s_code in str(row['can_cover_stations']).split(','):
                s_code = s_code.strip().zfill(3)
                session.run("""
                    MATCH (w:Worker {id: $id})
                    MERGE (s:Station {code: $s_code})
                    MERGE (w)-[:CAN_COVER]->(s)
                """, id=row['worker_id'], s_code=s_code)

        # ── 3. Seed Capacity & Weeks ───────────────────────────────────
        for _, row in cap_df.iterrows():
            session.run("""
                MERGE (wk:Week {id: $week})
                MERGE (c:Capacity {id: $cap_id})
                SET c.own_hours = $own_hrs, c.hired_hours = $hired_hrs,
                    c.overtime_hours = $ot_hrs, c.total_capacity = $cap,
                    c.total_planned = $plan, c.deficit = $deficit
                MERGE (c)-[:COVERS]->(wk)
            """, week=row['week'], cap_id=row['week'] + "_cap",
               own_hrs=row['own_hours'], hired_hrs=row['hired_hours'],
               ot_hrs=row['overtime_hours'], cap=row['total_capacity'],
               plan=row['total_planned'], deficit=row['deficit'])

        # ── 4. Seed Projects, Products, Etapps, Stations, Production ──
        for _, row in prod_df.iterrows():
            session.run("""
                MERGE (p:Project {id: $p_id})
                SET p.name = $p_name, p.number = $p_num

                MERGE (prod:Product {type: $prod_type})
                SET prod.unit = $unit, prod.unit_factor = $u_fact

                MERGE (p)-[:PRODUCES {quantity: $qty}]->(prod)

                MERGE (s:Station {code: $s_code})
                SET s.name = $s_name

                MERGE (e:Etapp {id: $etapp})

                MERGE (wk:Week {id: $week})

                MERGE (p)-[:IN_ETAPP]->(e)
            """, p_id=row['project_id'], p_name=row['project_name'],
               p_num=row['project_number'], prod_type=row['product_type'],
               unit=row['unit'], u_fact=row['unit_factor'], qty=row['quantity'],
               s_code=str(row['station_code']).zfill(3), s_name=row['station_name'],
               etapp=row['etapp'], week=row['week'])

            # Per-row SCHEDULED_AT relationship: Project -> Station (with weekly metrics)
            # Use CREATE here because each CSV row is a unique production record
            session.run("""
                MATCH (p:Project {id: $p_id})
                MATCH (s:Station {code: $s_code})
                MATCH (wk:Week {id: $week})
                CREATE (p)-[:SCHEDULED_AT {
                    week: $week,
                    planned_hours: $p_hrs,
                    actual_hours: $a_hrs,
                    completed_units: $c_units,
                    product_type: $prod_type,
                    etapp: $etapp,
                    bop: $bop
                }]->(s)
            """, p_id=row['project_id'], s_code=str(row['station_code']).zfill(3),
               week=row['week'], p_hrs=row['planned_hours'], a_hrs=row['actual_hours'],
               c_units=row['completed_units'], prod_type=row['product_type'],
               etapp=row['etapp'], bop=row['bop'])

        # ── 5. Station -> Certification requirements (inferred from workers) ──
        station_certs = {}
        for _, row in workers_df.iterrows():
            s_code = str(row['primary_station']).zfill(3)
            certs = [c.strip() for c in row['certifications'].split(',')]
            if s_code not in station_certs:
                station_certs[s_code] = set()
            station_certs[s_code].update(certs)

        for s_code, certs in station_certs.items():
            for cert in certs:
                session.run("""
                    MERGE (s:Station {code: $s_code})
                    MERGE (c:Certification {name: $cert})
                    MERGE (s)-[:REQUIRES_CERT]->(c)
                """, s_code=s_code, cert=cert)

        # ── 6. Create Bottleneck nodes for stations with >10% overrun ──
        session.run("""
            MATCH (p:Project)-[r:SCHEDULED_AT]->(s:Station)
            WHERE r.actual_hours > r.planned_hours * 1.1
            WITH s, r.week AS week, 
                 sum(r.actual_hours - r.planned_hours) AS deficit_hours
            MERGE (b:Bottleneck {station: s.code, week: week})
            SET b.deficit_hours = deficit_hours
            MERGE (s)-[:FLAGGED_AS]->(b)
        """)

    print("Graph seeding complete.")
    driver.close()


if __name__ == "__main__":
    seed_data()