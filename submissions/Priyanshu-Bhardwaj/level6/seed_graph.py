import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

def run_query(driver, query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters)

def setup_constraints(driver):
    print("Setting up constraints...")
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week) REQUIRE wk.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pd:Product) REQUIRE pd.type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Certification) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Factory) REQUIRE f.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp) REQUIRE e.name IS UNIQUE"
    ]
    for q in constraints:
        run_query(driver, q)

def load_data(driver):
    print("Loading CSVs...")
    production_df = pd.read_csv("data/factory_production.csv", dtype=str)
    workers_df = pd.read_csv("data/factory_workers.csv", dtype=str)
    capacity_df = pd.read_csv("data/factory_capacity.csv", dtype=str)

    # 1. Load Capacity & Weeks (Relationships: 1. HAS_CAPACITY)
    print("Seeding Capacity & Weeks...")
    capacity_data = capacity_df.fillna(0).to_dict('records')
    run_query(driver, """
        UNWIND $rows AS row
        MERGE (w:Week {id: row.week})
        MERGE (f:Factory {name: "Main Factory"})
        MERGE (w)-[r:HAS_CAPACITY {own: toInteger(row.own_hours), hired: toInteger(row.hired_hours), 
                                   overtime: toInteger(row.overtime_hours), deficit: toInteger(row.deficit)}]->(f)
        SET r.total_capacity = toInteger(row.total_capacity), r.total_planned = toInteger(row.total_planned)
    """, {"rows": capacity_data})

    # 2. Load Workers (Relationships: 2. PRIMARY_AT, 3. CAN_COVER, 4. HAS_CERT)
    print("Seeding Workers...")
    workers_data = workers_df.fillna("").to_dict('records')
    run_query(driver, """
        UNWIND $rows AS row
        MERGE (w:Worker {id: row.worker_id})
        SET w.name = row.name, w.role = row.role, w.type = row.type
        
        // Primary Station
        WITH w, row
        WHERE row.primary_station <> ""
        MERGE (s:Station {code: toString(row.primary_station)})
        MERGE (w)-[:PRIMARY_AT]->(s)
        
        // Cover Stations
        WITH w, row
        WHERE row.can_cover_stations <> ""
        UNWIND split(row.can_cover_stations, ",") AS cover_code
        MERGE (cs:Station {code: trim(cover_code)})
        MERGE (w)-[:CAN_COVER]->(cs)
        
        // Certifications
        WITH w, row
        WHERE row.certifications <> ""
        UNWIND split(row.certifications, ",") AS cert_name
        MERGE (c:Certification {name: trim(cert_name)})
        MERGE (w)-[:HAS_CERT]->(c)
    """, {"rows": workers_data})

    # 3. Load Production (Relationships: 5. EXECUTED_AT, 6. INCLUDES, 7. ACTIVE_DURING, 8. ASSIGNED_TO)
    print("Seeding Production...")
    prod_data = production_df.fillna(0).to_dict('records')
    run_query(driver, """
        UNWIND $rows AS row
        MERGE (p:Project {id: row.project_id})
        SET p.name = row.project_name, p.number = toString(row.project_number)
        
        MERGE (s:Station {code: toString(row.station_code)})
        SET s.name = row.station_name
        
        MERGE (pd:Product {type: row.product_type})
        SET pd.unit = row.unit
        
        MERGE (wk:Week {id: row.week})
        MERGE (et:Etapp {name: row.etapp})
        
        // Ensure idempotency for identical week/station overlaps by adding product to rel
        MERGE (p)-[r:EXECUTED_AT {week: row.week, product: row.product_type}]->(s)
        SET r.planned_hours = toFloat(row.planned_hours),
            r.actual_hours = toFloat(row.actual_hours),
            r.completed_units = toInteger(row.completed_units)
            
        MERGE (p)-[inc:INCLUDES {product: row.product_type}]->(pd)
        SET inc.qty = toFloat(row.quantity), inc.unit_factor = toFloat(row.unit_factor)
        
        MERGE (p)-[:ACTIVE_DURING]->(wk)
        MERGE (p)-[:ASSIGNED_TO]->(et)
    """, {"rows": prod_data})

    print("Graph seeding complete! ✅")

if __name__ == "__main__":
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        setup_constraints(driver)
        load_data(driver)
