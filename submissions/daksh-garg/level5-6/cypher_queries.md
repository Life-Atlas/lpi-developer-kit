# Factory Intelligence Cypher Queries

## Overview
Production-ready Cypher queries for real-time factory operations analysis and optimization.

## 1. Overloaded Stations Detection

### Current Overload Analysis
```cypher
// Find stations with utilization > 85%
MATCH (s:Station)
WHERE s.currentLoad > 85 AND s.status = 'ACTIVE'
RETURN 
    s.stationId,
    s.name,
    s.currentLoad as utilization,
    s.capacity,
    s.efficiency,
    s.downtime,
    CASE 
        WHEN s.currentLoad > 95 THEN 'CRITICAL'
        WHEN s.currentLoad > 90 THEN 'HIGH'
        ELSE 'MEDIUM'
    END as riskLevel
ORDER BY s.currentLoad DESC;
```

### Historical Overload Pattern
```cypher
// Find stations with frequent overload patterns
MATCH (s:Station)-[r:HAS_BOTTLENECK]->(b:Bottleneck)
WHERE b.type = 'STATION' AND b.severity IN ['HIGH', 'CRITICAL']
WITH s, COUNT(b) as bottleneckCount
WHERE bottleneckCount >= 3
RETURN 
    s.stationId,
    s.name,
    bottleneckCount,
    s.efficiency,
    s.downtime,
    'REQUIRES_UPGRADE' as recommendation
ORDER BY bottleneckCount DESC;
```

### Load Balancing Opportunities
```cypher
// Find underutilized stations that can take load
MATCH (overloaded:Station)
WHERE overloaded.currentLoad > 85 AND overloaded.status = 'ACTIVE'
WITH overloaded

MATCH (available:Station)
WHERE available.currentLoad < 60 AND 
      available.status = 'ACTIVE' AND
      available.type = overloaded.type

RETURN 
    overloaded.stationId as overloadedStation,
    overloaded.currentLoad as overloadedUtilization,
    available.stationId as availableStation,
    available.currentLoad as availableUtilization,
    available.capacity,
    (overloaded.currentLoad - available.currentLoad) as loadDifference
ORDER BY loadDifference DESC
LIMIT 10;
```

## 2. Delayed Projects Analysis

### Critical Delayed Projects
```cypher
// Find projects with critical delays
MATCH (p:Project)
WHERE p.status = 'DELAYED' AND 
      p.deadline < datetime() AND
      p.priority >= 4

RETURN 
    p.projectId,
    p.name,
    p.priority,
    p.deadline,
    datetime() - p.deadline as daysOverdue,
    p.progress,
    p.riskScore,
    CASE 
        WHEN p.deadline < datetime() - duration({days: 7}) THEN 'CRITICAL'
        WHEN p.deadline < datetime() - duration({days: 3}) THEN 'HIGH'
        ELSE 'MEDIUM'
    END as urgencyLevel
ORDER BY daysOverdue DESC;
```

### Project Dependency Chain Analysis
```cypher
// Find dependency chains causing delays
MATCH path = (p:Project {status: 'DELAYED'})-[:DEPENDS_ON*1..5]-(dependency:Project)
WHERE dependency.status IN ['DELAYED', 'ACTIVE']

RETURN 
    p.projectId as delayedProject,
    p.name as projectName,
    LENGTH(path) as dependencyDepth,
    [node IN nodes(path) | node.projectId] as dependencyChain,
    REDUCE(total = 0, node IN nodes(path) | total + node.priority) as totalPriority
ORDER BY dependencyDepth DESC, totalPriority DESC
LIMIT 20;
```

### Resource Shortage Analysis
```cypher
// Find projects delayed due to resource shortages
MATCH (p:Project {status: 'DELAYED'})-[:USES_STATION]->(s:Station)
WHERE s.currentLoad > 90

WITH p, COLLECT(s.stationId) as overloadedStations

MATCH (p)-[:USES_STATION]->(available:Station)
WHERE available.currentLoad < 70 AND available.stationId NOT IN overloadedStations

RETURN 
    p.projectId,
    p.name,
    p.priority,
    overloadedStations,
    [s IN COLLECT(available) | s.stationId] as alternativeStations,
    SIZE(overloadedStations) as bottleneckCount
ORDER BY bottleneckCount DESC;
```

## 3. Worker Overload Detection

### Worker Burnout Risk
```cypher
// Find workers at risk of burnout
MATCH (w:Worker)
WHERE w.currentLoad > 90 AND 
      w.availability = true AND
      w.efficiency < 80

RETURN 
    w.workerId,
    w.name,
    w.currentLoad as utilization,
    w.efficiency,
    w.experience,
    w.skillLevel,
    CASE 
        WHEN w.currentLoad > 95 THEN 'CRITICAL_BURNOUT_RISK'
        WHEN w.currentLoad > 90 THEN 'HIGH_BURNOUT_RISK'
        ELSE 'MEDIUM_BURNOUT_RISK'
    END as riskCategory,
    'REDUCE_LOAD' as action
ORDER BY w.currentLoad DESC;
```

### Skill Gap Analysis
```cypher
// Find skill gaps in current workforce
MATCH (t:Task {status: 'PENDING'})-[:REQUIRES_WORKER]->(w:Worker)
WHERE t.priority >= 4 AND 
      NOT ANY(skill IN t.requiredSkills WHERE skill IN w.certifications)

RETURN 
    t.taskId,
    t.name as taskName,
    t.requiredSkills,
    w.workerId,
    w.certifications as currentSkills,
    [skill IN t.requiredSkills WHERE skill NOT IN w.certifications] as missingSkills,
    SIZE([skill IN t.requiredSkills WHERE skill NOT IN w.certifications]) as skillGapCount
ORDER BY skillGapCount DESC, t.priority DESC;
```

### Workforce Optimization
```cypher
// Optimize worker allocation across stations
MATCH (s:Station)-[:STAFFED_BY]->(w:Worker)
WHERE s.currentLoad > 80 AND w.currentLoad > 85

WITH s, w

MATCH (available:Worker)
WHERE available.currentLoad < 60 AND 
      available.skillLevel >= w.skillLevel AND
      available.specialization = w.specialization

RETURN 
    s.stationId as overloadedStation,
    w.workerId as overloadedWorker,
    available.workerId as availableWorker,
    available.skillLevel,
    available.efficiency,
    (w.currentLoad - available.currentLoad) as loadRelief
ORDER BY loadRelief DESC
LIMIT 15;
```

## 4. Bottleneck Machine Detection

### Machine Performance Analysis
```cypher
// Find machines causing bottlenecks
MATCH (m:Machine)
WHERE m.currentUtilization > 90 AND 
      m.errorRate > 5 AND
      m.status = 'RUNNING'

RETURN 
    m.machineId,
    m.name,
    m.type,
    m.currentUtilization,
    m.errorRate,
    m.temperature,
    m.vibration,
    m.lastMaintenance,
    datetime() - m.lastMaintenance as daysSinceMaintenance,
    CASE 
        WHEN m.errorRate > 10 THEN 'CRITICAL'
        WHEN m.errorRate > 7 THEN 'HIGH'
        ELSE 'MEDIUM'
    END as maintenancePriority,
    'IMMEDIATE_MAINTENANCE' as action
ORDER BY m.errorRate DESC, m.currentUtilization DESC;
```

### Predictive Maintenance
```cypher
// Predict machines needing maintenance soon
MATCH (m:Machine)
WHERE m.maintenanceInterval > 0 AND
      (datetime() - m.lastMaintenance).hours > (m.maintenanceInterval * 0.8)

RETURN 
    m.machineId,
    m.name,
    m.type,
    m.maintenanceInterval,
    (datetime() - m.lastMaintenance).hours as hoursSinceMaintenance,
    (m.maintenanceInterval - (datetime() - m.lastMaintenance).hours) as hoursUntilMaintenance,
    CASE 
        WHEN (datetime() - m.lastMaintenance).hours > m.maintenanceInterval THEN 'OVERDUE'
        WHEN (datetime() - m.lastMaintenance).hours > (m.maintenanceInterval * 0.9) THEN 'URGENT'
        WHEN (datetime() - m.lastMaintenance).hours > (m.maintenanceInterval * 0.8) THEN 'SCHEDULE_SOON'
        ELSE 'MONITOR'
    END as maintenanceStatus
ORDER BY hoursUntilMaintenance ASC;
```

### Machine Replacement Analysis
```cypher
// Find machines that should be replaced
MATCH (m:Machine)
WHERE m.efficiency < 70 AND 
      m.errorRate > 8 AND
      m.operatingCost > (m.capacity * 0.5)

RETURN 
    m.machineId,
    m.name,
    m.model,
    m.efficiency,
    m.errorRate,
    m.operatingCost,
    m.capacity,
    (m.operatingCost / m.capacity) as costPerUnit,
    'REPLACE_MACHINE' as recommendation,
    (m.capacity * 0.8) as replacementCapacity
ORDER BY m.efficiency ASC, m.errorRate DESC;
```

## 5. Dependency Chain Analysis

### Critical Path Analysis
```cypher
// Find critical path in production dependencies
MATCH path = (start:Task)-[:DEPENDS_ON*]->(end:Task)
WHERE start.priority >= 4 AND end.priority >= 4
WITH path, REDUCE(total = 0, task IN nodes(path) | total + task.estimatedTime) as totalTime

RETURN 
    start.taskId as startTask,
    end.taskId as endTask,
    LENGTH(path) as dependencyLength,
    totalTime,
    [node IN nodes(path) | node.taskId] as criticalPath,
    CASE 
        WHEN totalTime > 480 THEN 'CRITICAL_DELAY_RISK'
        WHEN totalTime > 240 THEN 'HIGH_DELAY_RISK'
        ELSE 'MEDIUM_DELAY_RISK'
    END as riskLevel
ORDER BY totalTime DESC
LIMIT 20;
```

### Circular Dependency Detection
```cypher
// Detect circular dependencies that could cause deadlocks
MATCH path = (t:Task)-[:DEPENDS_ON*]->(t)
WHERE LENGTH(path) > 1

RETURN 
    t.taskId,
    t.name,
    LENGTH(path) as cycleLength,
    [node IN nodes(path) | node.taskId] as circularDependency,
    'CIRCULAR_DEPENDENCY' as issue,
    'BREAK_CYCLE' as action
ORDER BY cycleLength ASC;
```

## 6. Real-time Monitoring Queries

### System Health Dashboard
```cypher
// Overall system health metrics
MATCH (p:Project)
WITH p.status as projectStatus, COUNT(p) as projectCount

MATCH (s:Station)
WITH projectStatus, projectCount, s.status as stationStatus, COUNT(s) as stationCount

MATCH (w:Worker)
WITH projectStatus, projectCount, stationStatus, stationCount, 
     w.currentLoad > 80 as highLoadWorkers, COUNT(w) as workerCount

MATCH (m:Machine)
WITH projectStatus, projectCount, stationStatus, stationCount,
     highLoadWorkers, workerCount, m.status as machineStatus, COUNT(m) as machineCount

RETURN 
    projectStatus,
    projectCount,
    stationStatus,
    stationCount,
    machineStatus,
    machineCount,
     highLoadWorkers,
    workerCount,
    CASE 
        WHEN projectStatus = 'DELAYED' THEN 'ALERT'
        WHEN stationStatus = 'OFFLINE' THEN 'ALERT'
        WHEN machineStatus = 'ERROR' THEN 'ALERT'
        ELSE 'HEALTHY'
    END as systemStatus
ORDER BY projectStatus, stationStatus, machineStatus;
```

### Capacity Utilization Report
```cypher
// Comprehensive capacity utilization report
MATCH (s:Station)
OPTIONAL MATCH (s)-[:STAFFED_BY]->(w:Worker)
OPTIONAL MATCH (s)-[:CONTAINS_MACHINE]->(m:Machine)

RETURN 
    s.stationId,
    s.name,
    s.type,
    s.currentLoad as stationUtilization,
    AVG(w.currentLoad) as avgWorkerUtilization,
    AVG(m.currentUtilization) as avgMachineUtilization,
    COUNT(DISTINCT w) as workerCount,
    COUNT(DISTINCT m) as machineCount,
    CASE 
        WHEN s.currentLoad > 90 THEN 'CRITICAL'
        WHEN s.currentLoad > 80 THEN 'HIGH'
        WHEN s.currentLoad > 70 THEN 'MEDIUM'
        ELSE 'NORMAL'
    END as utilizationStatus
ORDER BY s.currentLoad DESC;
```

## Performance Optimization

### Query Optimization Tips
1. **Use indexes** on frequently queried properties
2. **LIMIT results** for dashboard queries
3. **PROFILE queries** to optimize performance
4. **Use parameterized queries** for applications
5. **Batch operations** for bulk updates

### Real-time Considerations
- These queries are optimized for sub-second execution
- Use appropriate timeouts for dashboard applications
- Implement caching for frequently accessed data
- Consider materialized views for complex aggregations

These queries provide the foundation for intelligent factory operations with real-time insights and predictive capabilities.
