import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load credentials
load_dotenv()
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PWD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PWD))

def run_query(query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters)

def clear_database():
    print("Wiping old database to prevent duplicates...")
    run_query("MATCH (n) DETACH DELETE n")

def create_constraints():
    print("Creating constraints...")
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week) REQUIRE wk.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Certification) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BOP) REQUIRE b.name IS UNIQUE"
    ]
    for q in queries:
        try:
            run_query(q)
        except Exception:
            pass

def clean_code(val):
    if pd.isna(val) or val == "":
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    try:
        # This converts '011' -> '11'
        return str(int(v))
    except ValueError:
        return v.upper()
    
def seed_database():
    print("Loading CSV Data with Sanitization...")
    
    # 1. Load Capacity
    df_cap = pd.read_csv('factory_capacity.csv')
    for _, row in df_cap.iterrows():
        query = """
        MERGE (wk:Week {id: $week})
        SET wk.total_capacity = toFloat($cap), 
            wk.total_planned = toFloat($plan), 
            wk.deficit = toFloat($def)
        """
        run_query(query, {"week": str(row['week']), "cap": row['total_capacity'], 
                          "plan": row['total_planned'], "def": row['deficit']})

    # 2. Load Workers
    df_workers = pd.read_csv('factory_workers.csv').fillna("")
    for _, row in df_workers.iterrows():
        wid = clean_code(row['worker_id'])
        if not wid: continue 
        
        run_query("MERGE (w:Worker {id: $wid}) SET w.name=$name, w.role=$role", 
                  {"wid": wid, "name": row['name'], "role": row['role']})
 
        p_station = clean_code(row['primary_station'])
        if p_station and p_station != "ALL":
            run_query("""
            MATCH (w:Worker {id: $wid})
            MERGE (s:Station {code: $scode})
            MERGE (w)-[:PRIMARY_STATION]->(s)
            """, {"wid": wid, "scode": p_station})

        if row['can_cover_stations']:
            for backup in str(row['can_cover_stations']).split(','):
                b_code = clean_code(backup)
                if b_code and b_code != "ALL":
                    run_query("""
                    MATCH (w:Worker {id: $wid})
                    MERGE (s:Station {code: $scode})
                    MERGE (w)-[:CAN_COVER]->(s)
                    """, {"wid": wid, "scode": b_code})

    # 3. Load Production
    df_prod = pd.read_csv('factory_production.csv').fillna("")
    for _, row in df_prod.iterrows():
        scode = clean_code(row['station_code'])
        if not scode:
            continue
            
        query_prod = """
        // Ensure Nodes Exist
        MERGE (p:Project {name: $proj_name})
        MERGE (s:Station {code: $scode}) SET s.name = $sname
        MERGE (pr:Product {type: $ptype})
        MERGE (wk:Week {id: $week})
        MERGE (e:Etapp {id: $etapp})
        MERGE (b:BOP {name: "Standard Flow"})
        MERGE (c_req:Certification {name: "General Safety"})
        
        // Create Relationships
        MERGE (p)-[:USES_PRODUCT]->(pr)
        MERGE (p)-[:PART_OF_ETAPP]->(e)
        MERGE (p)-[:BELONGS_TO_BOP]->(b)
        MERGE (s)-[:REQUIRES_CERT]->(c_req)
        
        MERGE (p)-[r1:PROCESSED_AT]->(s)
        ON CREATE SET r1.planned_hours = toFloat($plan), r1.actual_hours = toFloat($act)
        ON MATCH SET r1.planned_hours = r1.planned_hours + toFloat($plan), r1.actual_hours = r1.actual_hours + toFloat($act)
        
        MERGE (p)-[r2:LOGGED_IN_WEEK]->(wk)
        ON CREATE SET r2.planned_hours = toFloat($plan), r2.actual_hours = toFloat($act)
        ON MATCH SET r2.planned_hours = r2.planned_hours + toFloat($plan), r2.actual_hours = r2.actual_hours + toFloat($act)
        
        MERGE (s)-[r3:UTILIZED_IN_WEEK]->(wk)
        ON CREATE SET r3.planned_hours = toFloat($plan), r3.actual_hours = toFloat($act)
        ON MATCH SET r3.planned_hours = r3.planned_hours + toFloat($plan), r3.actual_hours = r3.actual_hours + toFloat($act)
        """
        run_query(query_prod, {
            "proj_name": row['project_name'], "scode": scode, 
            "sname": row['station_name'], "ptype": row['product_type'],
            "plan": row['planned_hours'], "act": row['actual_hours'],
            "week": str(row['week']), "etapp": str(row.get('etapp', 'Unknown'))
        })

    print("Graph Database Seeded Successfully!")

if __name__ == "__main__":
    clear_database()
    create_constraints()
    seed_database()
    driver.close()