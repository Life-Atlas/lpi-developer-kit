# Quick Copy-Paste Code Files

## seed_graph.py

```python
import csv
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class GraphSeeder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_constraints(self):
        """Create uniqueness constraints"""
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Worker) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.type IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (wk:Week) REQUIRE wk.week IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Etapp) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BOP) REQUIRE b.id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)
        print("✓ Constraints created")
    
    def load_projects_products_stations(self, csv_path):
        """Load from factory_production.csv"""
        projects = {}
        products = set()
        stations = {}
        etapps = set()
        bops = set()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                projects[row['project_id']] = {
                    'id': row['project_id'],
                    'number': row['project_number'],
                    'name': row['project_name']
                }
                products.add(row['product_type'])
                if row['station_code'] not in stations:
                    stations[row['station_code']] = {
                        'code': row['station_code'],
                        'name': row['station_name']
                    }
                etapps.add(row['etapp'])
                bops.add(row['bop'])
        
        with self.driver.session() as session:
            for proj in projects.values():
                session.execute_write(
                    lambda tx, p=proj: tx.run(
                        "MERGE (p:Project {id: $id}) SET p.number = $number, p.name = $name",
                        id=p['id'], number=p['number'], name=p['name']
                    )
                )
        print(f"✓ {len(projects)} projects created")
        
        with self.driver.session() as session:
            for prod_type in products:
                session.execute_write(
                    lambda tx, pt=prod_type: tx.run(
                        "MERGE (pr:Product {type: $type})", type=pt
                    )
                )
        print(f"✓ {len(products)} products created")
        
        with self.driver.session() as session:
            for station in stations.values():
                session.execute_write(
                    lambda tx, s=station: tx.run(
                        "MERGE (st:Station {code: $code}) SET st.name = $name",
                        code=s['code'], name=s['name']
                    )
                )
        print(f"✓ {len(stations)} stations created")
        
        with self.driver.session() as session:
            for etapp in etapps:
                session.execute_write(
                    lambda tx, e=etapp: tx.run(
                        "MERGE (et:Etapp {id: $id})", id=e
                    )
                )
            for bop in bops:
                session.execute_write(
                    lambda tx, b=bop: tx.run(
                        "MERGE (b:BOP {id: $id})", id=b
                    )
                )
        print(f"✓ {len(etapps)} etapps + {len(bops)} BOPs created")
    
    def load_relationships_production(self, csv_path):
        """Create relationships from production.csv"""
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session.execute_write(
                        lambda tx, r=row: tx.run(
                            "MATCH (p:Project {id: $proj_id}), (pr:Product {type: $prod_type}) "
                            "MERGE (p)-[:PRODUCES {quantity: $qty, unit_factor: $uf}]->(pr)",
                            proj_id=r['project_id'], prod_type=r['product_type'],
                            qty=int(r['quantity']), uf=float(r['unit_factor'])
                        )
                    )
                    
                    session.execute_write(
                        lambda tx, r=row: tx.run(
                            "MATCH (p:Project {id: $proj_id}), (s:Station {code: $st_code}), (w:Week {week: $week}) "
                            "MERGE (p)-[:SCHEDULED_AT {week: $week, planned_hours: $planned, actual_hours: $actual, completed_units: $completed}]->(s) "
                            "MERGE (p)-[:USES_WEEK]->(w)",
                            proj_id=r['project_id'], st_code=r['station_code'], week=r['week'],
                            planned=float(r['planned_hours']), actual=float(r['actual_hours']),
                            completed=int(r['completed_units'])
                        )
                    )
                    
                    session.execute_write(
                        lambda tx, r=row: tx.run(
                            "MATCH (p:Project {id: $proj_id}), (e:Etapp {id: $etapp}) MERGE (p)-[:PART_OF]->(e)",
                            proj_id=r['project_id'], etapp=r['etapp']
                        )
                    )
        print("✓ Production relationships created")
    
    def load_weeks(self, csv_path):
        """Load Week nodes from capacity.csv"""
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session.execute_write(
                        lambda tx, r=row: tx.run(
                            "MERGE (w:Week {week: $week}) SET w.week_num = $week_num",
                            week=r['week'], week_num=int(r['week'][1:])
                        )
                    )
        print("✓ Weeks created")
    
    def load_capacity(self, csv_path):
        """Load capacity data"""
        with self.driver.session() as session:
            session.execute_write(lambda tx: tx.run("MERGE (c:Capacity {id: 'GLOBAL'})"))
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session.execute_write(
                        lambda tx, r=row: tx.run(
                            "MATCH (w:Week {week: $week}), (c:Capacity {id: 'GLOBAL'}) "
                            "MERGE (w)-[:HAS_CAPACITY {own_staff: $own, hired_staff: $hired, overtime_hours: $overtime, "
                            "total_capacity: $total, total_planned: $planned, deficit: $deficit}]->(c)",
                            week=r['week'], own=int(r['own_staff_count']), hired=int(r['hired_staff_count']),
                            overtime=int(r['overtime_hours']), total=int(r['total_capacity']),
                            planned=int(r['total_planned']), deficit=int(r['deficit'])
                        )
                    )
        print("✓ Capacity relationships created")
    
    def load_workers(self, csv_path):
        """Load Worker nodes and relationships"""
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session.execute_write(
                        lambda tx, r=row: tx.run(
                            "MERGE (w:Worker {id: $id}) SET w.name = $name, w.role = $role, w.hours_per_week = $hours, w.type = $type",
                            id=r['worker_id'], name=r['name'], role=r['role'],
                            hours=int(r['hours_per_week']), type=r['type']
                        )
                    )
                    
                    if row['primary_station'] != 'all':
                        session.execute_write(
                            lambda tx, wid=row['worker_id'], ps=row['primary_station']: tx.run(
                                "MATCH (w:Worker {id: $worker_id}), (s:Station {code: $station_code}) "
                                "MERGE (w)-[:WORKS_AT]->(s)",
                                worker_id=wid, station_code=ps
                            )
                        )
                    
                    for station_code in row['can_cover_stations'].split(','):
                        station_code = station_code.strip()
                        if station_code != 'all':
                            session.execute_write(
                                lambda tx, wid=row['worker_id'], sc=station_code, certs=row['certifications']: tx.run(
                                    "MATCH (w:Worker {id: $worker_id}), (s:Station {code: $station_code}) "
                                    "MERGE (w)-[:CAN_COVER {certifications: $certs}]->(s)",
                                    worker_id=wid, station_code=sc, certs=certs
                                )
                            )
        print("✓ Workers and relationships created")
    
    def seed(self, production_csv, workers_csv, capacity_csv):
        """Run complete seeding"""
        print("\n🚀 Starting graph seeding...\n")
        try:
            self.create_constraints()
            self.load_projects_products_stations(production_csv)
            self.load_relationships_production(production_csv)
            self.load_weeks(capacity_csv)
            self.load_capacity(capacity_csv)
            self.load_workers(workers_csv)
            
            with self.driver.session() as session:
                node_count = session.run("MATCH (n) RETURN count(n) AS c").single()['c']
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()['c']
            
            print(f"\n✅ Seeding complete! Nodes: {node_count}, Relationships: {rel_count}\n")
        
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            raise
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    seeder = GraphSeeder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    seeder.seed("challenges/data/factory_production.csv", "challenges/data/factory_workers.csv", "challenges/data/factory_capacity.csv")
    seeder.close()
```

---

## requirements.txt

```
streamlit==1.37.0
neo4j==5.22.0
python-dotenv==1.0.0
pandas==2.2.0
plotly==5.18.0
```

---

## .env.example

```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

---

See LEVEL5_L6_COMPLETE_SOLUTION.md for full app.py and README.md content.
