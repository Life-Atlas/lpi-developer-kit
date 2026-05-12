import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(override=True)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def wipe_database(tx):
    print("🧹 Wiping database to fix the 'Leading Zero' Pandas bug...")
    tx.run("MATCH (n) DETACH DELETE n")

def create_constraints(tx):
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week) REQUIRE wk.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.type IS UNIQUE")

def seed_production_data(tx, df):
    print("Seeding Production Data...")
    for _, row in df.iterrows():
        query = """
        MERGE (p:Project {id: $project_id}) ON CREATE SET p.name = $project_name
        MERGE (pr:Product {type: $product_type})
        MERGE (s:Station {code: $station_code}) ON CREATE SET s.name = $station_name
        MERGE (wk:Week {name: $week})
        MERGE (e:Etapp {name: $etapp})
        MERGE (p)-[prod:PRODUCES]->(pr) ON CREATE SET prod.quantity = $quantity, prod.unit_factor = $unit_factor
        MERGE (p)-[sched:SCHEDULED_AT {week: $week}]->(s) ON CREATE SET sched.planned_hours = $planned_hours, sched.actual_hours = $actual_hours
        MERGE (p)-[:BELONGS_TO]->(e)
        MERGE (p)-[:PLANNED_IN]->(wk)
        """
        # Because dtype=str, we must explicitly float() the math columns
        tx.run(query, 
               project_id=str(row['project_id']), project_name=str(row['project_name']),
               product_type=str(row['product_type']),
               station_code=str(row['station_code']), station_name=str(row['station_name']),
               week=str(row['week']), etapp=str(row['etapp']),
               quantity=float(row['quantity']), unit_factor=float(row['unit_factor']),
               planned_hours=float(row['planned_hours']), actual_hours=float(row['actual_hours']))

def seed_worker_data(tx, df):
    print("Seeding Worker Data...")
    for _, row in df.iterrows():
        certs = [c.strip() for c in str(row.get('certifications', '')).split(',') if c.strip() and str(row.get('certifications', '')) != 'nan']
        covers = [c.strip() for c in str(row.get('can_cover_stations', '')).split(',') if c.strip() and str(row.get('can_cover_stations', '')) != 'nan']
        
        # Merge the worker first
        tx.run("MERGE (w:Worker {id: $worker_id}) ON CREATE SET w.name = $name", worker_id=str(row['worker_id']), name=str(row['name']))
        
        # Only attach WORKS_AT if the primary station is an actual station code (not 'all')
        if str(row['primary_station']).lower() != 'all':
            tx.run("MATCH (w:Worker {id: $worker_id}) MERGE (s:Station {code: $primary_station}) MERGE (w)-[:WORKS_AT]->(s)", 
                   worker_id=str(row['worker_id']), primary_station=str(row['primary_station']))
        
        # Map certifications to skills
        for cert in certs:
            tx.run("MATCH (w:Worker {id: $w_id}) MERGE (sk:Skill {name: $skill}) MERGE (w)-[:CERTIFIED_FOR]->(sk)", w_id=str(row['worker_id']), skill=cert)
            
        # Map covers to stations
        for cover in covers:
            if cover.lower() != 'all':
                tx.run("MATCH (w:Worker {id: $w_id}) MERGE (s:Station {code: $s_code}) MERGE (w)-[:CAN_COVER]->(s)", w_id=str(row['worker_id']), s_code=cover)

def seed_capacity_data(tx, df):
    print("Seeding Capacity Data...")
    for _, row in df.iterrows():
        query = """
        MERGE (wk:Week {name: $week})
        MERGE (f:Factory {name: "Main Factory"})
        MERGE (wk)-[cap:HAS_CAPACITY]->(f)
          ON CREATE SET cap.own = $own, cap.hired = $hired, 
                        cap.overtime = $overtime, cap.deficit = $deficit
        """
        tx.run(query, week=str(row['week']), 
               own=float(row['own_hours']), hired=float(row['hired_hours']),
               overtime=float(row['overtime_hours']), deficit=float(row['deficit']))

if __name__ == "__main__":
    DATA_DIR = "./" 
    
    # THE FIX: dtype=str forces Pandas to preserve the leading zeros!
    prod_df = pd.read_csv(f"{DATA_DIR}factory_production.csv", dtype=str)
    work_df = pd.read_csv(f"{DATA_DIR}factory_workers.csv", dtype=str)
    cap_df = pd.read_csv(f"{DATA_DIR}factory_capacity.csv", dtype=str)

    with driver.session() as session:
        session.execute_write(wipe_database)
        session.execute_write(create_constraints)
        session.execute_write(seed_production_data, prod_df)
        session.execute_write(seed_worker_data, work_df)
        session.execute_write(seed_capacity_data, cap_df)
    
    print("✅ Graph successfully seeded!")
    driver.close()