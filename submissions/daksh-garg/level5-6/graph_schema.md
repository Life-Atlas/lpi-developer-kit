# Factory Production Knowledge Graph Schema

## Overview
Neo4j graph database schema for factory production intelligence system that enables real-time operational optimization and predictive analytics.

## Core Entities

### 1. Project
```cypher
(:Project {
    projectId: String,           // Unique identifier
    name: String,               // Project name
    description: String,          // Project description
    priority: Integer,           // 1-5 priority level
    startDate: DateTime,          // Project start date
    deadline: DateTime,           // Hard deadline
    status: String,              // PLANNING, ACTIVE, DELAYED, COMPLETED
    budget: Float,              // Project budget
    progress: Float,             // 0-100 completion percentage
    riskScore: Float,            // Calculated risk score
    complexity: Integer           // 1-5 complexity rating
})
```

### 2. Station
```cypher
(:Station {
    stationId: String,           // Unique identifier
    name: String,               // Station name
    type: String,               // ASSEMBLY, TESTING, PACKAGING, QUALITY
    capacity: Integer,           // Max units per hour
    currentLoad: Float,          // Current utilization (0-100%)
    status: String,              // ACTIVE, MAINTENANCE, OFFLINE
    efficiency: Float,           // Historical efficiency rate
    location: String,            // Physical location
    setupTime: Integer,          // Minutes between jobs
    downtime: Float,             // Monthly downtime percentage
    lastMaintenance: DateTime     // Last maintenance date
})
```

### 3. Worker
```cypher
(:Worker {
    workerId: String,            // Unique identifier
    name: String,                // Worker name
    skillLevel: Integer,          // 1-5 skill rating
    specialization: String,       // Primary skill area
    experience: Float,           // Years of experience
    currentLoad: Float,           // Current task load (0-100%)
    efficiency: Float,            // Individual efficiency rate
    availability: Boolean,        // Currently available
    hourlyCost: Float,            // Cost per hour
    certifications: [String],      // List of certifications
    lastTraining: DateTime         // Last training date
})
```

### 4. ProductionLine
```cypher
(:ProductionLine {
    lineId: String,             // Unique identifier
    name: String,               // Production line name
    capacity: Integer,           // Daily capacity
    currentSpeed: Float,         // Current operating speed
    qualityRate: Float,         // Quality percentage
    bottleneckRisk: Float,       // Calculated bottleneck risk
    uptime: Float,              // Monthly uptime percentage
    productType: String,         // Type of product
    setupTime: Integer,         // Line setup time
    cycleTime: Integer          // Time per unit
})
```

### 5. Task
```cypher
(:Task {
    taskId: String,              // Unique identifier
    name: String,               // Task name
    type: String,               // ASSEMBLY, TESTING, INSPECTION
    estimatedTime: Integer,      // Minutes to complete
    actualTime: Integer,         // Actual time taken
    status: String,              // PENDING, IN_PROGRESS, COMPLETED
    priority: Integer,           // 1-5 priority
    complexity: Integer,         // 1-5 complexity
    requiredSkills: [String],     // Required skills
    deadline: DateTime,          // Task deadline
    riskLevel: Float            // Calculated risk level
})
```

### 6. Machine
```cypher
(:Machine {
    machineId: String,           // Unique identifier
    name: String,               // Machine name
    type: String,               // CNC, ROBOT, CONVEYOR, PRESS
    model: String,               // Machine model
    capacity: Integer,           // Units per hour
    currentUtilization: Float,    // Current utilization (0-100%)
    status: String,              // RUNNING, IDLE, MAINTENANCE, ERROR
    maintenanceInterval: Integer,   // Hours between maintenance
    lastMaintenance: DateTime,     // Last maintenance
    errorRate: Float,            // Error percentage
    operatingCost: Float,        // Hourly operating cost
    temperature: Float,          // Current temperature
    vibration: Float            // Vibration level
})
```

### 7. Deadline
```cypher
(:Deadline {
    deadlineId: String,          // Unique identifier
    type: String,               // PROJECT, TASK, MAINTENANCE
    date: DateTime,              // Deadline date
    severity: String,             // LOW, MEDIUM, HIGH, CRITICAL
    impact: String,              // Impact description
    bufferDays: Integer,          // Buffer days before deadline
    riskScore: Float,           // Calculated risk score
    dependencies: [String]        // Dependent items
})
```

### 8. Bottleneck
```cypher
(:Bottleneck {
    bottleneckId: String,        // Unique identifier
    type: String,               // STATION, MACHINE, WORKER, LINE
    severity: String,             // LOW, MEDIUM, HIGH, CRITICAL
    description: String,          // Bottleneck description
    impactRate: Float,           // Production impact percentage
    duration: Integer,           // Duration in hours
    affectedItems: [String],      // Affected projects/tasks
    resolution: String,           // Resolution status
    predictedResolution: DateTime,  // Predicted resolution time
    cost: Float               // Financial impact per hour
})
```

## Key Relationships

### 1. Project Relationships
```cypher
// Project to ProductionLine
(:Project)-[:HAS_LINE]->(:ProductionLine)

// Project to Station  
(:Project)-[:USES_STATION]->(:Station)

// Project to Tasks
(:Project)-[:CONTAINS_TASK]->(:Task)

// Project to Deadlines
(:Project)-[:HAS_DEADLINE]->(:Deadline)
```

### 2. Station Relationships
```cypher
// Station to Machines
(:Station)-[:CONTAINS_MACHINE]->(:Machine)

// Station to Workers
(:Station)-[:STAFFED_BY]->(:Worker)

// Station to Bottlenecks
(:Station)-[:HAS_BOTTLENECK]->(:Bottleneck)

// Station to Tasks
(:Station)-[:PERFORMS_TASK]->(:Task)
```

### 3. Worker Relationships
```cypher
// Worker to Tasks
(:Worker)-[:ASSIGNED_TO]->(:Task)

// Worker to Stations
(:Worker)-[:WORKS_AT]->(:Station)

// Worker to Skills (dynamic)
(:Worker)-[:HAS_SKILL]->(:Skill {level: Integer})
```

### 4. Machine Relationships
```cypher
// Machine to Tasks
(:Machine)-[:PRODUCES_FOR]->(:Task)

// Machine to Bottlenecks
(:Machine)-[:CAUSES_BOTTLENECK]->(:Bottleneck)

// Machine to Maintenance
(:Machine)-[:REQUIRES_MAINTENANCE]->(:Deadline)
```

### 5. ProductionLine Relationships
```cypher
// ProductionLine to Stations
(:ProductionLine)-[:INCLUDES_STATION]->(:Station)

// ProductionLine to Projects
(:ProductionLine)-[:PRODUCES_FOR]->(:Project)

// ProductionLine to Bottlenecks
(:ProductionLine)-[:HAS_BOTTLENECK]->(:Bottleneck)
```

### 6. Task Dependencies
```cypher
// Task Dependencies
(:Task)-[:DEPENDS_ON]->(:Task)

// Task to Deadlines
(:Task)-[:HAS_DEADLINE]->(:Deadline)

// Task to Workers
(:Task)-[:REQUIRES_WORKER]->(:Worker)
```

## Constraints and Indexes

### Performance Indexes
```cypher
// Performance indexes
CREATE INDEX project_id FOR (p:Project) ON (p.projectId);
CREATE INDEX station_id FOR (s:Station) ON (s.stationId);
CREATE INDEX worker_id FOR (w:Worker) ON (w.workerId);
CREATE INDEX task_id FOR (t:Task) ON (t.taskId);
CREATE INDEX machine_id FOR (m:Machine) ON (m.machineId);
CREATE INDEX deadline_date FOR (d:Deadline) ON (d.date);

// Composite indexes for common queries
CREATE INDEX project_status FOR (p:Project) ON (p.status, p.priority);
CREATE INDEX station_load FOR (s:Station) ON (s.currentLoad, s.status);
CREATE INDEX worker_availability FOR (w:Worker) ON (w.availability, w.skillLevel);
CREATE INDEX task_status FOR (t:Task) ON (t.status, t.priority);
CREATE INDEX machine_utilization FOR (m:Machine) ON (m.currentUtilization, m.status);
```

### Data Integrity Constraints
```cypher
// Uniqueness constraints
CREATE CONSTRAINT project_unique FOR (p:Project) REQUIRE p.projectId IS UNIQUE;
CREATE CONSTRAINT station_unique FOR (s:Station) REQUIRE s.stationId IS UNIQUE;
CREATE CONSTRAINT worker_unique FOR (w:Worker) REQUIRE w.workerId IS UNIQUE;
CREATE CONSTRAINT task_unique FOR (t:Task) REQUIRE t.taskId IS UNIQUE;
CREATE CONSTRAINT machine_unique FOR (m:Machine) REQUIRE m.machineId IS UNIQUE;

// Value constraints
CREATE CONSTRAINT project_priority FOR (p:Project) REQUIRE p.priority >= 1 AND p.priority <= 5;
CREATE CONSTRAINT worker_skill FOR (w:Worker) REQUIRE w.skillLevel >= 1 AND w.skillLevel <= 5;
CREATE CONSTRAINT task_priority FOR (t:Task) REQUIRE t.priority >= 1 AND t.priority <= 5;
```

## Graph Traversal Patterns

### 1. Project Impact Analysis
```cypher
// Find all entities affected by a delayed project
MATCH (p:Project {status: 'DELAYED'})-[*1..3]-(affected)
RETURN p.projectId, COLLECT(DISTINCT affected) as impactedEntities
```

### 2. Bottleneck Propagation
```cypher
// Trace bottleneck impact through production chain
MATCH (b:Bottleneck)-[:AFFECTS*1..3]-(entity)
WHERE b.severity = 'HIGH'
RETURN b.bottleneckId, COLLECT(DISTINCT entity) as impactedItems
```

### 3. Resource Optimization
```cypher
// Find underutilized resources
MATCH (r)
WHERE r.currentLoad < 70 AND r.status = 'ACTIVE'
RETURN r, r.currentLoad as utilization
ORDER BY r.currentLoad ASC
```

## Schema Benefits

1. **Real-time Visibility**: Complete factory state representation
2. **Predictive Analytics**: Risk scoring and bottleneck prediction
3. **Resource Optimization**: Load balancing and capacity planning
4. **Dependency Management**: Complex relationship tracking
5. **Operational Intelligence**: Data-driven decision support
6. **Scalability**: Handles thousands of entities efficiently
7. **Flexibility**: Easy to extend with new entity types

This schema provides the foundation for intelligent factory operations with comprehensive relationship tracking and predictive capabilities.
