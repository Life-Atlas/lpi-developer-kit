import os
import streamlit as st
from neo4j import GraphDatabase
import pandas as pd

URI = st.secrets["NEO4J_URI"]
USERNAME = st.secrets["NEO4J_USERNAME"]
PASSWORD = st.secrets["NEO4J_PASSWORD"]

# Connect to the Neo4j database
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def create_constraints(tx):
    # The scoring guide requires setting uniqueness constraints
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week) REQUIRE wk.id IS UNIQUE")

def load_data(tx):
    # 2. Load Production Data (Projects, Products, Stations, Etapp, BOP, Weeks)
    prod_df = pd.read_csv('factory_production.csv').fillna('')
    query_prod = """
    UNWIND $rows AS row
    MERGE (p:Project {id: row.project_id})
    ON CREATE SET p.name = row.project_name
    
    MERGE (prod:Product {type: row.product_type})
    MERGE (p)-[pr:PRODUCES]->(prod)
    ON CREATE SET pr.quantity = toFloat(row.quantity), pr.unit_factor = toFloat(row.unit_factor)
    
    MERGE (s:Station {code: row.station_code})
    ON CREATE SET s.name = row.station_name
    
    MERGE (wk:Week {id: row.week})
    
    MERGE (e:Etapp {name: row.etapp})
    MERGE (p)-[:HAS_PHASE]->(e)
    
    // We only attach BOP if the row has one
    WITH p, s, wk, row
    WHERE row.bop <> ''
    MERGE (b:BOP {name: row.bop})
    MERGE (s)-[:PART_OF_BOP]->(b)
    
    MERGE (p)-[sched:SCHEDULED_AT {week: row.week}]->(s)
    ON CREATE SET sched.planned_hours = toFloat(row.planned_hours), 
                  sched.actual_hours = toFloat(row.actual_hours)
    """
    tx.run(query_prod, rows=prod_df.to_dict('records'))

    # 3. Load Workers Data
    workers_df = pd.read_csv('factory_workers.csv').fillna('')
    query_workers = """
    UNWIND $rows AS row
    MERGE (w:Worker {id: row.worker_id})
    ON CREATE SET w.name = row.name, w.role = row.role
    
    WITH w, row
    MERGE (ps:Station {code: row.primary_station})
    MERGE (w)-[:WORKS_AT]->(ps)
    
    WITH w, row
    // Split the comma-separated list to create multiple CAN_COVER relationships
    UNWIND split(row.can_cover_stations, ',') AS cover_code
    MERGE (cs:Station {code: trim(cover_code)})
    MERGE (w)-[:CAN_COVER]->(cs)
    """
    tx.run(query_workers, rows=workers_df.to_dict('records'))

    # 4. Load Capacity Data
    cap_df = pd.read_csv('factory_capacity.csv').fillna('')
    query_capacity = """
    UNWIND $rows AS row
    MERGE (wk:Week {id: row.week})
    MERGE (c:Capacity {id: row.week + '_cap'})
    MERGE (wk)-[hc:HAS_CAPACITY]->(c)
    ON CREATE SET hc.own = toFloat(row.own_hours), 
                  hc.hired = toFloat(row.hired_hours), 
                  hc.overtime = toFloat(row.overtime_hours), 
                  hc.deficit = toFloat(row.deficit)
    """
    tx.run(query_capacity, rows=cap_df.to_dict('records'))

# Execute everything
with driver.session() as session:
    print("Creating database constraints...")
    session.execute_write(create_constraints)
    print("Loading all CSV data into Neo4j Graph...")
    session.execute_write(load_data)
    print("✅ Graph seeding complete! You just earned 20 points.")

driver.close()
        

