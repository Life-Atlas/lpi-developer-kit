#!/usr/bin/env python3
"""
Neo4j Data Loader for Factory Intelligence System

Loads CSV data into Neo4j graph database with duplicate prevention
and relationship creation for factory operations.
"""

import pandas as pd
from neo4j import GraphDatabase
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FactoryGraphLoader:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.session = self.driver.session()
        
    def close(self):
        """Close database connection"""
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear all existing data (for testing)"""
        logger.warning("Clearing all data from database...")
        query = "MATCH (n) DETACH DELETE n"
        self.session.run(query)
        logger.info("Database cleared")
    
    def create_constraints(self):
        """Create database constraints for performance"""
        constraints = [
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.projectId IS UNIQUE",
            "CREATE CONSTRAINT station_id_unique IF NOT EXISTS FOR (s:Station) REQUIRE s.stationId IS UNIQUE",
            "CREATE CONSTRAINT worker_id_unique IF NOT EXISTS FOR (w:Worker) REQUIRE w.workerId IS UNIQUE",
            "CREATE CONSTRAINT machine_id_unique IF NOT EXISTS FOR (m:Machine) REQUIRE m.machineId IS UNIQUE",
            "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.taskId IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                self.session.run(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint already exists: {e}")
    
    def load_projects(self, csv_file):
        """Load projects from CSV"""
        logger.info(f"Loading projects from {csv_file}")
        df = pd.read_csv(csv_file)
        
        query = """
        MERGE (p:Project {projectId: $projectId})
        SET p.name = $name,
            p.description = $description,
            p.priority = $priority,
            p.startDate = datetime($startDate),
            p.deadline = datetime($deadline),
            p.status = $status,
            p.budget = $budget,
            p.progress = $progress,
            p.complexity = $complexity,
            p.daysToDeadline = $daysToDeadline,
            p.riskScore = $riskScore,
            p.updatedAt = datetime()
        RETURN p
        """
        
        loaded_count = 0
        for _, row in df.iterrows():
            try:
                self.session.run(query, {
                    'projectId': str(row['projectId']),
                    'name': str(row['name']),
                    'description': str(row.get('description', '')),
                    'priority': int(row['priority']),
                    'startDate': str(row['startDate']),
                    'deadline': str(row['deadline']),
                    'status': str(row['status']),
                    'budget': float(row.get('budget', 0)),
                    'progress': float(row['progress']),
                    'complexity': int(row.get('complexity', 1)),
                    'daysToDeadline': int(row.get('daysToDeadline', 0)),
                    'riskScore': float(row.get('riskScore', 0))
                })
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading project {row.get('projectId')}: {e}")
        
        logger.info(f"Loaded {loaded_count} projects")
        return loaded_count
    
    def load_stations(self, csv_file):
        """Load stations from CSV"""
        logger.info(f"Loading stations from {csv_file}")
        df = pd.read_csv(csv_file)
        
        query = """
        MERGE (s:Station {stationId: $stationId})
        SET s.name = $name,
            s.type = $type,
            s.capacity = $capacity,
            s.currentLoad = $currentLoad,
            s.status = $status,
            s.efficiency = $efficiency,
            s.location = $location,
            s.downtime = $downtime,
            s.updatedAt = datetime()
        RETURN s
        """
        
        loaded_count = 0
        for _, row in df.iterrows():
            try:
                self.session.run(query, {
                    'stationId': str(row['stationId']),
                    'name': str(row['name']),
                    'type': str(row['type']),
                    'capacity': int(row['capacity']),
                    'currentLoad': float(row['currentLoad']),
                    'status': str(row['status']),
                    'efficiency': float(row['efficiency']),
                    'location': str(row.get('location', '')),
                    'downtime': float(row.get('downtime', 0))
                })
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading station {row.get('stationId')}: {e}")
        
        logger.info(f"Loaded {loaded_count} stations")
        return loaded_count
    
    def load_workers(self, csv_file):
        """Load workers from CSV"""
        logger.info(f"Loading workers from {csv_file}")
        df = pd.read_csv(csv_file)
        
        query = """
        MERGE (w:Worker {workerId: $workerId})
        SET w.name = $name,
            w.skillLevel = $skillLevel,
            w.specialization = $specialization,
            w.experience = $experience,
            w.currentLoad = $currentLoad,
            w.efficiency = $efficiency,
            w.availability = $availability,
            w.hourlyCost = $hourlyCost,
            w.certifications = $certifications,
            w.updatedAt = datetime()
        RETURN w
        """
        
        loaded_count = 0
        for _, row in df.iterrows():
            try:
                # Parse certifications as list
                certifications = str(row.get('certifications', '')).split(',') if pd.notna(row.get('certifications')) else []
                certifications = [cert.strip() for cert in certifications if cert.strip()]
                
                self.session.run(query, {
                    'workerId': str(row['workerId']),
                    'name': str(row['name']),
                    'skillLevel': int(row['skillLevel']),
                    'specialization': str(row['specialization']),
                    'experience': float(row['experience']),
                    'currentLoad': float(row['currentLoad']),
                    'efficiency': float(row['efficiency']),
                    'availability': bool(row['availability']),
                    'hourlyCost': float(row.get('hourlyCost', 0)),
                    'certifications': certifications
                })
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading worker {row.get('workerId')}: {e}")
        
        logger.info(f"Loaded {loaded_count} workers")
        return loaded_count
    
    def create_sample_machines(self):
        """Create sample machines for stations"""
        logger.info("Creating sample machines...")
        
        machines_data = [
            ("M001", "CNC Machine Alpha", "CNC", "DMG MORI", 100, 75.0, "RUNNING", 168, 2.5, 45.0),
            ("M002", "Assembly Robot Beta", "ROBOT", "KUKA", 50, 85.0, "RUNNING", 336, 1.2, 35.0),
            ("M003", "Testing Station Gamma", "TESTING", "NI", 80, 60.0, "RUNNING", 720, 0.8, 25.0),
            ("M004", "Packaging Line Delta", "PACKAGING", "Siemens", 200, 90.0, "RUNNING", 504, 3.2, 55.0),
            ("M005", "Quality Control Epsilon", "QUALITY", "Mitutoyo", 30, 45.0, "IDLE", 168, 0.5, 20.0),
        ]
        
        query = """
        MERGE (m:Machine {machineId: $machineId})
        SET m.name = $name,
            m.type = $type,
            m.model = $model,
            m.capacity = $capacity,
            m.currentUtilization = $currentUtilization,
            m.status = $status,
            m.maintenanceInterval = $maintenanceInterval,
            m.errorRate = $errorRate,
            m.operatingCost = $operatingCost,
            m.lastMaintenance = datetime() - duration({hours: $maintenanceInterval * 0.7}),
            m.updatedAt = datetime()
        """
        
        for machine in machines_data:
            try:
                self.session.run(query, {
                    'machineId': machine[0],
                    'name': machine[1],
                    'type': machine[2],
                    'model': machine[3],
                    'capacity': machine[4],
                    'currentUtilization': machine[5],
                    'status': machine[6],
                    'maintenanceInterval': machine[7],
                    'errorRate': machine[8],
                    'operatingCost': machine[9]
                })
            except Exception as e:
                logger.error(f"Error creating machine {machine[0]}: {e}")
        
        logger.info("Created 5 sample machines")
    
    def create_sample_tasks(self):
        """Create sample tasks"""
        logger.info("Creating sample tasks...")
        
        tasks_data = [
            ("T001", "Assembly Task 1", "ASSEMBLY", 120, 115, "COMPLETED", 3, 2, ["assembly", "quality"], 4),
            ("T002", "Testing Task 1", "TESTING", 60, 65, "IN_PROGRESS", 4, 3, ["testing", "calibration"], 3),
            ("T003", "Quality Inspection", "INSPECTION", 45, 40, "COMPLETED", 5, 2, ["quality", "inspection"], 4),
            ("T004", "Packaging Task 1", "PACKAGING", 30, 30, "PENDING", 2, 1, ["packaging"], 2),
            ("T005", "Final Assembly", "ASSEMBLY", 180, 0, "PENDING", 5, 4, ["assembly", "testing"], 5),
        ]
        
        query = """
        MERGE (t:Task {taskId: $taskId})
        SET t.name = $name,
            t.type = $type,
            t.estimatedTime = $estimatedTime,
            t.actualTime = $actualTime,
            t.status = $status,
            t.priority = $priority,
            t.complexity = $complexity,
            t.requiredSkills = $requiredSkills,
            t.riskLevel = $riskLevel * 0.2,
            t.createdAt = datetime(),
            t.updatedAt = datetime()
        """
        
        for task in tasks_data:
            try:
                self.session.run(query, {
                    'taskId': task[0],
                    'name': task[1],
                    'type': task[2],
                    'estimatedTime': task[3],
                    'actualTime': task[4],
                    'status': task[5],
                    'priority': task[6],
                    'complexity': task[7],
                    'requiredSkills': task[8],
                    'riskLevel': task[9]
                })
            except Exception as e:
                logger.error(f"Error creating task {task[0]}: {e}")
        
        logger.info("Created 5 sample tasks")
    
    def create_relationships(self):
        """Create relationships between entities"""
        logger.info("Creating relationships...")
        
        # Station-Machine relationships
        station_machine_query = """
        MATCH (s:Station), (m:Machine)
        WHERE s.stationId IN ['ST001', 'ST002', 'ST003', 'ST004', 'ST005']
        AND m.machineId IN ['M001', 'M002', 'M003', 'M004', 'M005']
        WITH s, m, 
             CASE s.stationId 
                 WHEN 'ST001' THEN 'M001'
                 WHEN 'ST002' THEN 'M002'
                 WHEN 'ST003' THEN 'M003'
                 WHEN 'ST004' THEN 'M004'
                 WHEN 'ST005' THEN 'M005'
             END as assigned_machine
        WHERE m.machineId = assigned_machine
        MERGE (s)-[:CONTAINS_MACHINE]->(m)
        """
        
        # Worker-Station relationships
        worker_station_query = """
        MATCH (w:Worker), (s:Station)
        WHERE w.workerId IN ['W001', 'W002', 'W003', 'W004', 'W005']
        AND s.stationId IN ['ST001', 'ST002', 'ST003', 'ST004', 'ST005']
        WITH w, s, 
             (toInt(w.workerId.replace('W', '')) - 1) % 5 as station_index
        WITH w, s, ['ST001', 'ST002', 'ST003', 'ST004', 'ST005'][station_index] as assigned_station
        WHERE s.stationId = assigned_station
        MERGE (w)-[:WORKS_AT]->(s)
        """
        
        # Project-Station relationships
        project_station_query = """
        MATCH (p:Project), (s:Station)
        WHERE p.status = 'ACTIVE'
        WITH p, s
        ORDER BY p.priority DESC
        WITH p, collect(s)[0..2] as assigned_stations
        UNWIND assigned_stations as station
        MERGE (p)-[:USES_STATION]->(station)
        """
        
        # Task-Worker relationships
        task_worker_query = """
        MATCH (t:Task), (w:Worker)
        WHERE t.status IN ['IN_PROGRESS', 'PENDING']
        AND w.availability = true
        WITH t, w
        ORDER BY t.priority DESC, w.skillLevel DESC
        WITH t, collect(w)[0] as assigned_worker
        MERGE (t)-[:REQUIRES_WORKER]->(assigned_worker)
        """
        
        try:
            self.session.run(station_machine_query)
            self.session.run(worker_station_query)
            self.session.run(project_station_query)
            self.session.run(task_worker_query)
            logger.info("Created relationships between entities")
        except Exception as e:
            logger.error(f"Error creating relationships: {e}")
    
    def create_bottlenecks(self):
        """Create sample bottlenecks based on current load"""
        logger.info("Creating bottlenecks...")
        
        # Find overloaded stations and create bottlenecks
        bottleneck_query = """
        MATCH (s:Station)
        WHERE s.currentLoad > 85
        CREATE (b:Bottleneck {
            bottleneckId: 'B_' + s.stationId,
            type: 'STATION',
            severity: CASE 
                WHEN s.currentLoad > 95 THEN 'CRITICAL'
                WHEN s.currentLoad > 90 THEN 'HIGH'
                ELSE 'MEDIUM'
            END,
            description: s.name + ' station overload',
            impactRate: s.currentLoad,
            cost: s.capacity * 0.1,
            createdAt = datetime()
        })
        CREATE (s)-[:HAS_BOTTLENECK]->(b)
        """
        
        try:
            result = self.session.run(bottleneck_query)
            created_count = len(list(result))
            logger.info(f"Created {created_count} bottlenecks")
        except Exception as e:
            logger.error(f"Error creating bottlenecks: {e}")
    
    def run_full_load(self, projects_csv="projects.csv", stations_csv="stations.csv", workers_csv="workers.csv"):
        """Run complete data loading process"""
        try:
            logger.info("Starting full data load...")
            
            # Create constraints
            self.create_constraints()
            
            # Load CSV data
            self.load_projects(projects_csv)
            self.load_stations(stations_csv)
            self.load_workers(workers_csv)
            
            # Create sample data
            self.create_sample_machines()
            self.create_sample_tasks()
            
            # Create relationships
            self.create_relationships()
            
            # Create bottlenecks
            self.create_bottlenecks()
            
            logger.info("Full data load completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during data load: {e}")
            raise

def main():
    """Main execution function"""
    loader = FactoryGraphLoader()
    
    try:
        # Check if CSV files exist
        csv_files = ["projects.csv", "stations.csv", "workers.csv"]
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                logger.error(f"CSV file not found: {csv_file}")
                return
        
        # Run full load
        loader.run_full_load()
        
        # Print summary
        summary_query = """
        MATCH (n) 
        WITH labels(n)[0] as label, count(n) as count
        RETURN label, count
        ORDER BY label
        """
        
        result = loader.session.run(summary_query)
        logger.info("Database summary:")
        for record in result:
            logger.info(f"  {record['label']}: {record['count']}")
            
    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        loader.close()

if __name__ == "__main__":
    main()
