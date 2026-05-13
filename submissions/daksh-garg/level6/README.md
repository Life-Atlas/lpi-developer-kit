# Factory Production Dashboard

Real-time factory production intelligence built on Neo4j graph database and Streamlit.

## Architecture

```
CSV Data → Neo4j Graph → Streamlit Dashboard
```

- **Data Source**: Real factory production CSV files
- **Database**: Neo4j graph database for relationship analytics
- **Frontend**: Streamlit dashboard with Plotly visualizations

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Neo4j
```bash
# Using Neo4j Desktop or Docker
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.x
```

### 3. Load Data
```bash
python seed_graph.py
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

### 5. Run Dashboard
```bash
streamlit run app.py
```

## Dashboard Pages

### Project Overview
- 8 projects with planned vs actual hours
- Variance analysis by project
- Total production metrics

### Station Load
- Station performance comparison
- Load variance identification
- Overload alerts

### Capacity Tracker
- Weekly capacity utilization
- Deficit analysis with bottleneck detection
- Critical week identification

### Worker Coverage
- Worker station coverage mapping
- Single point of failure analysis
- Coverage optimization opportunities

### Forecast
- Week 9 capacity prediction
- Historical trend analysis
- Overload warnings

### Self-Test
- Database connectivity checks
- Node/relationship validation
- System health scoring

## Data Schema

### Core Entities
- **Project**: Production projects with hours and units
- **Worker**: Staff with coverage capabilities
- **Station**: Production stations
- **Week**: Time dimension
- **Capacity**: Weekly capacity planning

### Key Relationships
- Project → Station (AT_STATION)
- Worker → Station (CAN_COVER)
- Week → Capacity (HAS_CAPACITY)

## Deployment

### Streamlit Cloud
1. Push code to GitHub
2. Connect Streamlit Cloud to repository
3. Set environment variables in Streamlit dashboard
4. Deploy

### Environment Variables
```
NEO4J_URI=bolt+s://your-database.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## Known Limitations

- Read-only dashboard (no data editing)
- Simple linear forecasting
- No real-time data updates
- Limited to provided CSV structure

## Screenshots

*Placeholder for dashboard screenshots*

## Troubleshooting

### Database Connection
```python
# Test connection manually
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
driver.verify_connectivity()
```

### Common Issues
- **Connection refused**: Check Neo4j is running
- **Authentication failed**: Verify credentials
- **No data**: Run seed_graph.py first

## Development

### Adding New Queries
```python
def execute_query(query, params=None):
    driver = get_neo4j_connection()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]
```

### Adding New Pages
1. Add page to sidebar navigation
2. Create page section with `if page == "Page Name":`
3. Use `execute_query()` for data
4. Use Plotly for visualizations

## Data Source

Based on real factory production data:
- `factory_production.csv` - Project production records
- `factory_workers.csv` - Worker coverage data  
- `factory_capacity.csv` - Weekly capacity planning
