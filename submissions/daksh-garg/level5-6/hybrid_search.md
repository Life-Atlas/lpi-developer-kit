# Hybrid Search for Factory Intelligence

## Graph + Vector + Metadata Search Architecture

### 1. Graph Search
**Use Case**: Finding relationships and dependencies
```cypher
// Find all machines in bottleneck chain
MATCH (m:Machine)-[:AFFECTS*1..3]-(b:Bottleneck)
WHERE b.severity = 'HIGH'
RETURN m.machineId, b.impactRate
```

### 2. Vector Search  
**Use Case**: Semantic similarity for problem matching
```python
# Embed production issues for similarity search
def embed_problem(description):
    return model.encode(description)

def find_similar_issues(embedding, threshold=0.8):
    return vector_store.search(embedding, threshold)
```

### 3. Metadata Filtering
**Use Case**: Quick filtering by attributes
```cypher
// Filter by machine type and status
MATCH (m:Machine)
WHERE m.type = 'CNC' AND m.status = 'RUNNING'
RETURN m.machineId, m.currentUtilization
```

### 4. Hybrid Query Example
```cypher
// Combine graph traversal with vector similarity
MATCH (m:Machine)
WHERE m.currentUtilization > 85
WITH COLLECT(m) as overloadedMachines

// Vector search for similar historical issues
CALL db.index.vector.search('issues', $problemEmbedding, 10)
YIELD node, score

RETURN overloadedMachines, node.similarIssue, score
```

### Real Manufacturing Examples
- **Machine Failure Prediction**: Similar failure patterns + current sensor data
- **Production Planning**: Graph dependencies + capacity constraints
- **Quality Issues**: Vector similarity + production line context
- **Worker Assignment**: Skill matching + availability constraints

This hybrid approach enables both exact relationship queries and semantic similarity search for comprehensive factory intelligence.
