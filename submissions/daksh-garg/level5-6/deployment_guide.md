# Factory Intelligence Dashboard Deployment Guide

## Overview
Complete deployment guide for the Factory Intelligence Dashboard using Streamlit Cloud and Neo4j AuraDB.

## 1. Streamlit Cloud Deployment

### Prerequisites
- Streamlit account (free tier available)
- GitHub repository with the dashboard code
- Neo4j database (AuraDB or local)

### Step 1: Prepare Repository Structure
```
factory-intelligence/
├── app.py                 # Main Streamlit app
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── secrets.toml      # Environment variables
├── data/
│   ├── projects.csv
│   ├── stations.csv
│   └── workers.csv
├── neo4j_loader.py       # Data loading script
└── README.md
```

### Step 2: Create requirements.txt
```txt
streamlit>=1.28.0
plotly>=5.15.0
pandas>=2.0.0
neo4j>=5.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
```

### Step 3: Configure Environment Variables
Create `.streamlit/secrets.toml`:
```toml
# Neo4j Database Configuration
neo4j_uri = "bolt+s://your-database.neo4j.io"
neo4j_user = "neo4j"
neo4j_password = "your-password"

# Optional: Additional configuration
app_title = "Factory Intelligence Dashboard"
refresh_interval = 30  # seconds
```

### Step 4: Deploy to Streamlit Cloud
1. Go to [Streamlit Cloud](https://cloud.streamlit.io/)
2. Click "New app" → "From existing repo"
3. Connect your GitHub repository
4. Select the main Python file (`app.py`)
5. Configure environment variables in the Streamlit dashboard
6. Click "Deploy"

### Step 5: Verify Deployment
- Check deployment logs for any errors
- Test all dashboard pages
- Verify database connectivity
- Monitor performance metrics

## 2. Neo4j Setup

### Option A: Neo4j AuraDB (Recommended for Production)

#### Step 1: Create AuraDB Account
1. Go to [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. Sign up for free tier (includes 1 database, 200k nodes)
3. Create new database instance

#### Step 2: Configure Database
- Choose region closest to your users
- Set database password
- Select version (Neo4j 5.x recommended)
- Wait for database to be ready

#### Step 3: Get Connection Details
```python
# Connection details from AuraDB console
uri = "bolt+s://your-database.neo4j.io"
user = "neo4j"
password = "your-password"
```

#### Step 4: Load Data
```bash
# Install dependencies
pip install neo4j pandas

# Run data loader
python neo4j_loader.py
```

### Option B: Local Neo4j (Development)

#### Step 1: Install Neo4j Desktop
1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create new project
3. Add new DBMS (Neo4j 5.x)
4. Set password

#### Step 2: Start Database
- Click "Start" on your database
- Wait for it to be ready
- Note the bolt://localhost:7687 connection

#### Step 3: Load Data
```bash
# Run the loader script
python neo4j_loader.py
```

## 3. Data Preparation

### Step 1: Create Sample CSV Files

#### projects.csv
```csv
projectId,name,description,priority,startDate,deadline,status,budget,progress,complexity,daysToDeadline,riskScore
P001,Factory Automation,Automate assembly line,4,2024-01-15,2024-06-15,ACTIVE,500000,65.5,3,45,0.65
P002,Quality Control System,Implement quality checks,5,2024-02-01,2024-05-01,ACTIVE,300000,42.0,4,30,0.78
P003,Inventory Management,Smart inventory tracking,3,2024-03-01,2024-08-01,PLANNING,200000,15.0,2,120,0.25
P004,Safety Protocol,Enhanced safety measures,5,2024-01-01,2024-04-01,DELAYED,150000,85.0,4,-5,0.92
P005,Energy Optimization,Reduce energy consumption,2,2024-04-01,2024-09-01,PLANNING,100000,5.0,2,150,0.15
```

#### stations.csv
```csv
stationId,name,type,capacity,currentLoad,status,efficiency,location,downtime
ST001,Assembly Station Alpha,ASSEMBLY,50,92.5,ACTIVE,78.5,Floor A,5.2
ST002,Testing Station Beta,TESTING,30,78.0,ACTIVE,85.2,Floor B,3.1
ST003,Packaging Station Gamma,PACKAGING,100,65.5,ACTIVE,92.1,Floor C,2.8
ST004,Quality Control Delta,QUALITY,20,88.0,ACTIVE,79.8,Floor A,4.5
ST005,Maintenance Station Epsilon,MAINTENANCE,10,45.0,ACTIVE,88.9,Floor B,8.2
```

#### workers.csv
```csv
workerId,name,skillLevel,specialization,experience,currentLoad,efficiency,availability,hourlyCost,certifications
W001,John Smith,4,Assembly,8.5,95.0,82.5,true,45.0,assembly,quality,safety
W002,Jane Doe,5,Testing,12.0,75.0,91.2,true,55.0,testing,calibration,automation
W003,Bob Johnson,3,Packaging,6.0,85.0,76.8,true,35.0,packaging,logistics
W004,Alice Brown,4,Quality,10.0,90.0,88.5,true,50.0,quality,inspection,iso
W005,Charlie Wilson,3,Maintenance,7.5,60.0,85.0,true,40.0,maintenance,electrical,mechanical
```

### Step 2: Upload CSV Files
- For Streamlit Cloud: Add CSV files to your GitHub repository
- For local deployment: Place in `data/` directory

## 4. Environment Variables

### Production Environment
```bash
# Streamlit Cloud (set in dashboard)
NEO4J_URI=bolt+s://your-database.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
APP_TITLE=Factory Intelligence Dashboard
REFRESH_INTERVAL=30
```

### Development Environment
```bash
# .env file for local development
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-local-password
APP_TITLE=Factory Intelligence Dashboard (Dev)
REFRESH_INTERVAL=10
```

## 5. Security Configuration

### Database Security
- Use strong passwords
- Enable SSL/TLS connections
- Restrict IP access (AuraDB)
- Regular password rotation

### Application Security
```python
# Secure database connection
def get_neo4j_connection():
    return GraphDatabase.driver(
        st.secrets.get("neo4j_uri"),
        auth=(st.secrets.get("neo4j_user"), st.secrets.get("neo4j_password")),
        max_connection_lifetime=3600,
        max_connection_pool_size=50
    )
```

### Streamlit Security
- Use secrets.toml for sensitive data
- Enable authentication if needed
- Regular dependency updates
- Input validation and sanitization

## 6. Performance Optimization

### Database Optimization
```cypher
# Create indexes for performance
CREATE INDEX project_status FOR (p:Project) ON (p.status);
CREATE INDEX station_load FOR (s:Station) ON (s.currentLoad);
CREATE INDEX worker_availability FOR (w:Worker) ON (w.availability);
```

### Application Optimization
```python
# Cache expensive queries
@st.cache_data(ttl=300)  # 5 minutes cache
def get_overloaded_stations():
    query = "MATCH (s:Station) WHERE s.currentLoad > 85 RETURN s"
    return session.run(query).data()
```

### Streamlit Optimization
- Use `@st.cache_data` for expensive operations
- Limit data returned from queries
- Optimize chart rendering
- Use pagination for large datasets

## 7. Monitoring and Maintenance

### Health Checks
```python
def health_check():
    try:
        # Test database connection
        session.run("RETURN 1")
        # Test data availability
        result = session.run("MATCH (n) RETURN count(n) as count").single()
        return result["count"] > 0
    except Exception as e:
        st.error(f"Health check failed: {e}")
        return False
```

### Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Monitoring Metrics
- Database connection count
- Query execution time
- Error rates
- User activity
- Resource utilization

## 8. Backup and Recovery

### Database Backup (AuraDB)
- Automatic backups enabled
- Point-in-time recovery available
- Export capabilities for manual backups

### Data Export
```python
# Export data for backup
def export_data():
    query = "MATCH (n) RETURN n"
    result = session.run(query)
    # Save to CSV or JSON
```

### Disaster Recovery
- Document recovery procedures
- Test backup restoration
- Maintain offline copies
- Version control for schema changes

## 9. Troubleshooting

### Common Issues

#### Database Connection Errors
```python
# Connection troubleshooting
try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
except Exception as e:
    st.error(f"Database connection failed: {e}")
```

#### Performance Issues
- Check query execution plans
- Monitor database load
- Optimize slow queries
- Consider caching strategies

#### Data Loading Problems
```python
# CSV validation
def validate_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        required_columns = ['projectId', 'name', 'status']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")
        return True
    except Exception as e:
        st.error(f"CSV validation failed: {e}")
        return False
```

## 10. Scaling Considerations

### Horizontal Scaling
- Multiple Streamlit instances
- Load balancer configuration
- Session state management
- Database connection pooling

### Vertical Scaling
- Increase memory allocation
- CPU optimization
- Storage capacity planning
- Network bandwidth

### Cost Optimization
- Monitor resource usage
- Optimize query patterns
- Implement caching strategies
- Right-size database instances

## 11. CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest
      - name: Deploy to Streamlit
        run: streamlit deploy
```

This deployment guide provides a comprehensive approach to deploying the Factory Intelligence Dashboard in both development and production environments.
