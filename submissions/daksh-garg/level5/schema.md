# Factory Production Graph Schema

## Core Entities (Based on Real Data)

### 1. Project
```cypher
(:Project {
    project_id: String,        // P01, P02, etc.
    project_name: String,     // Stålverket Borås, Kontorshus Mölndal
    product_type: String,      // IQB, SB, SP, SR, etc.
    unit: String,             // meter, styck
    quantity: Integer,          // 600, 1200, etc.
    unit_factor: Float,        // 1.77, 2.80, etc.
    station_code: String,       // 011, 012, etc.
    station_name: String,       // FS IQB, Förmontering IQB
    etapp: String,            // ET1, ET2, etc.
    bop: String,              // BOP1, BOP2, etc.
    week: String,              // w1, w2, etc.
    planned_hours: Float,     // Planned production hours
    actual_hours: Float,      // Actual production hours
    completed_units: Integer    // Completed production units
})
```

### 2. Worker
```cypher
(:Worker {
    worker_id: String,         // W01, W02, etc.
    name: String,              // Erik Lindberg, Anna Berg
    role: String,              // Operator, Inspector, Foreman
    primary_station: String,    // 011, 012, etc.
    can_cover_stations: String,  // "011,012" comma-separated
    certifications: String,     // "MIG/MAG,TIG,ISO 9606"
    hours_per_week: Integer,    // 40 hours/week
    type: String               // permanent, hired
})
```

### 3. Station
```cypher
(:Station {
    station_code: String,       // 011, 012, etc.
    station_name: String,       // FS IQB, Förmontering IQB
    etapp: String,            // ET1, ET2, etc.
})
```

### 4. Week
```cypher
(:Week {
    week_id: String,           // w1, w2, etc.
})
```

### 5. Etapp
```cypher
(:Etapp {
    etapp_id: String,          // ET1, ET2, etc.
    name: String               // Assembly, Testing, etc.
})
```

### 6. BOP
```cypher
(:BOP {
    bop_id: String,            // BOP1, BOP2, etc.
    name: String               // Balance of Plant identifier
})
```

### 7. Product
```cypher
(:Product {
    product_type: String,       // IQB, SB, SP, etc.
    name: String               // Product description
})
```

### 8. Capacity
```cypher
(:Capacity {
    week: String,               // w1, w2, etc.
    own_staff_count: Integer,    // 10 staff
    hired_staff_count: Integer,   // 2 hired staff
    own_hours: Integer,         // 400 hours
    hired_hours: Integer,        // 80 hours
    total_capacity: Integer,     // 480 total hours
    total_planned: Integer,     // 612 planned hours
    deficit: Integer             // -132 hours (shortfall)
})
```

## Key Relationships

### 1. Project Relationships
```cypher
// Project to Station
(:Project)-[:AT_STATION]->(:Station)

// Project to Week
(:Project)-[:IN_WEEK]->(:Week)

// Project to Product
(:Project)-[:PRODUCES]->(:Product)

// Project to BOP
(:Project)-[:UNDER_BOP]->(:BOP)
```

### 2. Worker Relationships
```cypher
// Worker to Primary Station
(:Worker)-[:PRIMARY_STATION]->(:Station)

// Worker to Coverable Stations
(:Worker)-[:CAN_COVER]->(:Station)

// Worker Certifications
(:Worker)-[:HAS_CERTIFICATION]->(:Certification)
```

### 3. Station Relationships
```cypher
// Station to Etapp
(:Station)-[:HAS_ETAPP]->(:Etapp)

// Station to Projects
(:Station)-[:HOSTS_PROJECT]->(:Project)
```

### 4. Capacity Relationships
```cypher
// Week to Capacity
(:Week)-[:HAS_CAPACITY]->(:Capacity)

// Capacity to Bottleneck (when deficit)
(:Capacity)-[:HAS_BOTTLENECK]->(:Bottleneck)
```

## Constraints and Indexes

### Performance Indexes
```cypher
CREATE INDEX project_id FOR (p:Project) ON (p.project_id);
CREATE INDEX worker_id FOR (w:Worker) ON (w.worker_id);
CREATE INDEX station_code FOR (s:Station) ON (s.station_code);
CREATE INDEX week_id FOR (w:Week) ON (w.week_id);
CREATE INDEX project_week FOR (p:Project) ON (p.week);
CREATE INDEX capacity_week FOR (c:Capacity) ON (c.week);
```

### Uniqueness Constraints
```cypher
CREATE CONSTRAINT project_unique FOR (p:Project) REQUIRE p.project_id IS UNIQUE;
CREATE CONSTRAINT worker_unique FOR (w:Worker) REQUIRE w.worker_id IS UNIQUE;
CREATE CONSTRAINT station_unique FOR (s:Station) REQUIRE s.station_code IS UNIQUE;
CREATE CONSTRAINT week_unique FOR (w:Week) REQUIRE w.week_id IS UNIQUE;
```

## Schema Benefits

1. **Real Data Mapping**: Directly maps to actual CSV structure
2. **Production Tracking**: planned vs actual hours by week
3. **Worker Coverage**: Multi-station coverage capabilities
4. **Capacity Planning**: Deficit tracking across weeks
5. **Product Analysis**: Product type and quantity tracking
6. **Temporal Analysis**: Week-based production analysis

This schema provides foundation for factory production intelligence based on actual manufacturing data.
