#!/usr/bin/env python3
"""
Neo4j Graph Seeding for Factory Production Data

Loads real factory CSV data into Neo4j with proper relationships.
Idempotent - can be run multiple times safely.
"""

import pandas as pd
from neo4j import GraphDatabase
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FactoryGraphSeeder:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.session = self.driver.session()
    
    def close(self):
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.close()
    
    def create_constraints(self):
        """Create database constraints"""
        constraints = [
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
            "CREATE CONSTRAINT worker_id_unique IF NOT EXISTS FOR (w:Worker) REQUIRE w.worker_id IS UNIQUE",
            "CREATE CONSTRAINT station_code_unique IF NOT EXISTS FOR (s:Station) REQUIRE s.station_code IS UNIQUE",
            "CREATE CONSTRAINT week_id_unique IF NOT EXISTS FOR (w:Week) REQUIRE w.week_id IS UNIQUE",
            "CREATE CONSTRAINT capacity_week_unique IF NOT EXISTS FOR (c:Capacity) REQUIRE c.week IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                self.session.run(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint exists: {e}")
    
    def clear_data(self):
        """Clear all existing data"""
        logger.warning("Clearing all data from database...")
        query = "MATCH (n) DETACH DELETE n"
        self.session.run(query)
        logger.info("Database cleared")
    
    def load_projects(self, csv_file):
        """Load projects from factory_production.csv"""
        logger.info(f"Loading projects from {csv_file}")
        df = pd.read_csv(csv_file)
        
        query = """
        MERGE (p:Project {project_id: $project_id, week: $week, station_code: $station_code})
        SET p.project_name = $project_name,
            p.product_type = $product_type,
            p.unit = $unit,
            p.quantity = $quantity,
            p.unit_factor = $unit_factor,
            p.station_name = $station_name,
            p.etapp = $etapp,
            p.bop = $bop,
            p.planned_hours = $planned_hours,
            p.actual_hours = $actual_hours,
            p.completed_units = $completed_units,
            p.variance_hours = $actual_hours - $planned_hours,
            p.variance_percent = (($actual_hours - $planned_hours) / $planned_hours) * 100,
            p.updated_at = datetime()
        RETURN p
        """
        
        loaded_count = 0
        for _, row in df.iterrows():
            try:
                self.session.run(query, {
                    'project_id': str(row['project_id']),
                    'project_name': str(row['project_name']),
                    'product_type': str(row['product_type']),
                    'unit': str(row['unit']),
                    'quantity': int(row['quantity']),
                    'unit_factor': float(row['unit_factor']),
                    'station_code': str(row['station_code']),
                    'station_name': str(row['station_name']),
                    'etapp': str(row['etapp']),
                    'bop': str(row['bop']),
                    'week': str(row['week']),
                    'planned_hours': float(row['planned_hours']),
                    'actual_hours': float(row['actual_hours']),
                    'completed_units': int(row['completed_units'])
                })
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading project {row.get('project_id')}: {e}")
        
        logger.info(f"Loaded {loaded_count} project records")
        return loaded_count
    
    def load_workers(self, csv_file):
        """Load workers from factory_workers.csv"""
        logger.info(f"Loading workers from {csv_file}")
        df = pd.read_csv(csv_file)
        
        query = """
        MERGE (w:Worker {worker_id: $worker_id})
        SET w.name = $name,
            w.role = $role,
            w.primary_station = $primary_station,
            w.can_cover_stations = $can_cover_stations,
            w.certifications = $certifications,
            w.hours_per_week = $hours_per_week,
            w.type = $type,
            w.updated_at = datetime()
        RETURN w
        """
        
        loaded_count = 0
        for _, row in df.iterrows():
            try:
                self.session.run(query, {
                    'worker_id': str(row['worker_id']),
                    'name': str(row['name']),
                    'role': str(row['role']),
                    'primary_station': str(row['primary_station']),
                    'can_cover_stations': str(row['can_cover_stations']),
                    'certifications': str(row['certifications']),
                    'hours_per_week': int(row['hours_per_week']),
                    'type': str(row['type'])
                })
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading worker {row.get('worker_id')}: {e}")
        
        logger.info(f"Loaded {loaded_count} workers")
        return loaded_count
    
    def load_capacity(self, csv_file):
        """Load capacity data from factory_capacity.csv"""
        logger.info(f"Loading capacity from {csv_file}")
        df = pd.read_csv(csv_file)
        
        query = """
        MERGE (c:Capacity {week: $week})
        SET c.own_staff_count = $own_staff_count,
            c.hired_staff_count = $hired_staff_count,
            c.own_hours = $own_hours,
            c.hired_hours = $hired_hours,
            c.overtime_hours = $overtime_hours,
            c.total_capacity = $total_capacity,
            c.total_planned = $total_planned,
            c.deficit = $deficit,
            c.utilization_percent = ($total_planned / $total_capacity) * 100,
            c.updated_at = datetime()
        RETURN c
        """
        
        loaded_count = 0
        for _, row in df.iterrows():
            try:
                self.session.run(query, {
                    'week': str(row['week']),
                    'own_staff_count': int(row['own_staff_count']),
                    'hired_staff_count': int(row['hired_staff_count']),
                    'own_hours': int(row['own_hours']),
                    'hired_hours': int(row['hired_hours']),
                    'overtime_hours': int(row['overtime_hours']),
                    'total_capacity': int(row['total_capacity']),
                    'total_planned': int(row['total_planned']),
                    'deficit': int(row['deficit'])
                })
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading capacity {row.get('week')}: {e}")
        
        logger.info(f"Loaded {loaded_count} capacity records")
        return loaded_count
    
    def create_supporting_entities(self):
        """Create stations, weeks, products, etapp, bop nodes"""
        logger.info("Creating supporting entities...")
        
        # Create unique stations
        station_query = """
        MATCH (p:Project)
        WITH DISTINCT p.station_code as station_code, p.station_name as station_name, p.etapp as etapp
        MERGE (s:Station {station_code: station_code})
        SET s.station_name = station_name, s.etapp = etapp
        """
        self.session.run(station_query)
        
        # Create unique weeks
        week_query = """
        MATCH (p:Project)
        WITH DISTINCT p.week as week_id
        MERGE (w:Week {week_id: week_id})
        """
        self.session.run(week_query)
        
        # Create unique products
        product_query = """
        MATCH (p:Project)
        WITH DISTINCT p.product_type as product_type
        MERGE (prod:Product {product_type: product_type})
        """
        self.session.run(product_query)
        
        # Create unique etapp
        etapp_query = """
        MATCH (p:Project)
        WITH DISTINCT p.etapp as etapp_id
        MERGE (e:Etapp {etapp_id: etapp_id})
        """
        self.session.run(etapp_query)
        
        # Create unique BOP
        bop_query = """
        MATCH (p:Project)
        WITH DISTINCT p.bop as bop_id
        MERGE (b:BOP {bop_id: bop_id})
        """
        self.session.run(bop_query)
        
        logger.info("Created supporting entities")
    
    def create_relationships(self):
        """Create relationships between entities"""
        logger.info("Creating relationships...")
        
        # Project to Station
        project_station_query = """
        MATCH (p:Project), (s:Station)
        WHERE p.station_code = s.station_code
        MERGE (p)-[:AT_STATION]->(s)
        """
        self.session.run(project_station_query)
        
        # Project to Week
        project_week_query = """
        MATCH (p:Project), (w:Week)
        WHERE p.week = w.week_id
        MERGE (p)-[:IN_WEEK]->(w)
        """
        self.session.run(project_week_query)
        
        # Project to Product
        project_product_query = """
        MATCH (p:Project), (prod:Product)
        WHERE p.product_type = prod.product_type
        MERGE (p)-[:PRODUCES]->(prod)
        """
        self.session.run(project_product_query)
        
        # Project to Etapp
        project_etapp_query = """
        MATCH (p:Project), (e:Etapp)
        WHERE p.etapp = e.etapp_id
        MERGE (p)-[:PART_OF_ETAPP]->(e)
        """
        self.session.run(project_etapp_query)
        
        # Project to BOP
        project_bop_query = """
        MATCH (p:Project), (b:BOP)
        WHERE p.bop = b.bop_id
        MERGE (p)-[:UNDER_BOP]->(b)
        """
        self.session.run(project_bop_query)
        
        # Worker to Primary Station
        worker_primary_query = """
        MATCH (w:Worker), (s:Station)
        WHERE w.primary_station = s.station_code
        MERGE (w)-[:PRIMARY_STATION]->(s)
        """
        self.session.run(worker_primary_query)
        
        # Worker to Coverable Stations
        worker_cover_query = """
        MATCH (w:Worker), (s:Station)
        WHERE w.can_cover_stations CONTAINS s.station_code
        MERGE (w)-[:CAN_COVER]->(s)
        """
        self.session.run(worker_cover_query)
        
        # Week to Capacity
        week_capacity_query = """
        MATCH (w:Week), (c:Capacity)
        WHERE w.week_id = c.week
        MERGE (w)-[:HAS_CAPACITY]->(c)
        """
        self.session.run(week_capacity_query)
        
        logger.info("Created relationships")
    
    def create_bottlenecks(self):
        """Create bottleneck nodes for capacity deficits"""
        logger.info("Creating bottlenecks...")
        
        bottleneck_query = """
        MATCH (c:Capacity)
        WHERE c.deficit < -50
        CREATE (b:Bottleneck {
            bottleneck_id: 'B_' + c.week,
            type: 'CAPACITY_DEFICIT',
            severity: CASE 
                WHEN c.deficit < -100 THEN 'CRITICAL'
                WHEN c.deficit < -75 THEN 'HIGH'
                ELSE 'MEDIUM'
            END,
            description: c.week + ' capacity deficit of ' + ABS(c.deficit) + ' hours',
            deficit_hours: c.deficit,
            utilization_percent: c.utilization_percent,
            created_at = datetime()
        })
        CREATE (c)-[:HAS_BOTTLENECK]->(b)
        """
        
        result = self.session.run(bottleneck_query)
        created_count = len(list(result))
        logger.info(f"Created {created_count} bottlenecks")
    
    def run_full_seed(self, production_csv="../challenges/data/factory_production.csv", 
                      workers_csv="../challenges/data/factory_workers.csv",
                      capacity_csv="../challenges/data/factory_capacity.csv"):
        """Run complete seeding process"""
        try:
            logger.info("Starting full graph seeding...")
            
            # Create constraints
            self.create_constraints()
            
            # Load CSV data
            self.load_projects(production_csv)
            self.load_workers(workers_csv)
            self.load_capacity(capacity_csv)
            
            # Create supporting entities
            self.create_supporting_entities()
            
            # Create relationships
            self.create_relationships()
            
            # Create bottlenecks
            self.create_bottlenecks()
            
            logger.info("Full graph seeding completed successfully!")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            raise
    
    def print_summary(self):
        """Print database summary"""
        summary_query = """
        MATCH (n) 
        WITH labels(n)[0] as label, count(n) as count
        RETURN label, count
        ORDER BY label
        """
        
        result = self.session.run(summary_query)
        logger.info("Database summary:")
        total_nodes = 0
        for record in result:
            logger.info(f"  {record['label']}: {record['count']}")
            total_nodes += record['count']
        
        # Count relationships
        rel_query = """
        MATCH ()-[r]->()
        RETURN count(r) as relationship_count
        """
        rel_result = self.session.run(rel_query).single()
        rel_count = rel_result['relationship_count']
        
        logger.info(f"Total nodes: {total_nodes}")
        logger.info(f"Total relationships: {rel_count}")

def main():
    """Main execution function"""
    seeder = FactoryGraphSeeder()
    
    try:
        # Check if CSV files exist
        csv_files = [
            "../challenges/data/factory_production.csv",
            "../challenges/data/factory_workers.csv", 
            "../challenges/data/factory_capacity.csv"
        ]
        
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                logger.error(f"CSV file not found: {csv_file}")
                return
        
        # Run full seeding
        seeder.run_full_seed()
        
    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        seeder.close()

if __name__ == "__main__":
    main()
