# Stream C — Industrial Twin Dashboard

**Customer:** Nicolas (internal — platform play)  
**Repo:** `LifeAtlas/factory-twin-dashboard` (to be created)  
**Team Size:** 12 interns  
**Duration:** May 16 – June 27, 2026

---

## Background

### The Problem

Sweden has ~160 steel and composite fabrication companies (SBI members). Nearly all of them manage production planning in Excel — sometimes 40-50 sheet workbooks maintained by a single person. If that person gets sick, the entire production visibility for a 100M+ SEK company disappears.

This is not unique to steel. Manufacturing across Europe runs on manual spreadsheets, tribal knowledge, and single-person dependencies. The factory floor has sensors and machines, but the planning layer is still a person with a laptop.

### The Opportunity

Life Atlas is building a **reusable industrial digital twin dashboard** that:
- Replaces manual Excel production planning with automated dashboards
- Models the factory as a knowledge graph (projects, stations, workers, products, capacity)
- Visualizes production in 3D (factory floor, station layouts, load heatmaps)
- Predicts bottlenecks before they happen
- Eventually simulates "what-if" scenarios (move 2 welders from station A to B — what happens?)

The first proof point is a Swedish steel fabrication company (real client, paying engagement). Your job is to build the **generic platform** that works for ANY factory — not just one customer.

### Why This Matters for Sweden

From today's industry discussions:
- 160+ metal fabrication companies in Sweden alone use Excel for production planning
- Production resilience is a national security concern (defense customers include major contractors)
- Swedish data sovereignty requirements mean cloud solutions must keep data in-country
- Edge-native, local-first architecture is not optional — it's the business model

### What You're Building On

**L5/L6 is your foundation.** The factory CSV data you're working with this week (8 projects, 9 stations, 13 workers, 8 weeks) is a simplified version of real production planning data. Your Neo4j graph schema from L5 and your Streamlit dashboard from L6 are literally the starting point for Stream C.

---

## The Data Model

A typical steel fabrication factory has:

| Entity | Description | Example |
|--------|-------------|---------|
| **Project** | Construction job with a delivery deadline | "Office Building Gothenburg" |
| **Product Type** | What's being manufactured (7 types) | IQB (beams), IQP (columns), SB (special), etc. |
| **Station** | Production area in the factory (9-10) | Welding, Assembly, Casting, Painting |
| **Worker** | Person with station certifications | Certified for stations 011, 013, 016 |
| **Week** | Time period for planning | Week 1-52, planned vs actual hours |
| **Etapp** | Delivery phase within a project | Phase 1 (foundations), Phase 2 (structure) |

### Key Relationships
- Projects produce Products (with quantities and unit factors)
- Projects are scheduled at Stations (with planned vs actual hours per week)
- Workers work at Stations (primary + can cover others)
- Weeks have Capacity (own staff + hired + overtime vs demand)
- Stations have Bottleneck alerts when actual > planned

### The 17 Formulas

Real production planning uses ~17 core calculations:
- Total time per project = sum(quantity × factor) per product type
- Weekly delta = accumulated hours this week minus last week
- Variance = actual station hours vs planned
- Capacity deficit = (own + hired + overtime) - total demand
- Station load distribution across weeks
- Gjutning/Painting proportional allocation splits
- Average time per unit (rolling and weekly)

These are documented. Your job is to implement them in Python, not invent them.

---

## Architecture

```
Excel / CSV Import (openpyxl, pandas)
    → PostgreSQL / Neo4j (structured + graph)
    → Python Engine (17 formulas)
    → Streamlit Dashboard (6+ views)
    → 3D Visualization (Cesium / Three.js)
```

### Stack
- **Python 3.12** + pandas + openpyxl
- **Streamlit** for dashboards (Plotly for charts)
- **Neo4j** for knowledge graph (relationships, traversals, what-if queries)
- **PostgreSQL** for tabular data (time series, capacity tracking)
- **Cesium** or **Three.js** for 3D factory floor visualization

---

## Dashboard Views (6 minimum)

### 1. Capacity Overview
- Weekly staffing: own staff, hired, overtime
- Surplus/deficit per week (color-coded: green/yellow/red)
- Rolling 8-week forecast

### 2. Project View
- All active projects with plan vs actual hours
- Time series: planned trajectory vs actual trajectory
- Variance percentage per project

### 3. Production Volume
- Product type × week × station matrix
- Etapp breakdown (which delivery phase)
- Completed units vs remaining

### 4. Station Load
- 9-10 stations, hours per week, color-coded by utilization
- Highlight overloaded stations (actual > planned by >10%)
- Worker assignment per station

### 5. Average Times
- Accumulated and weekly average time per product type
- Trend lines showing if efficiency is improving or degrading

### 6. Worker Coverage
- Matrix: which workers can cover which stations
- Single-point-of-failure alerts (station with only 1 certified worker)
- Certification gaps

---

## Week 0 — This Week (May 6-13): L5/L6 + Study

### L5/L6 (Individual — LPI Leaderboard)
Everyone does L5 (graph thinking) and L6 (build factory dashboard). This IS your Stream C onboarding:
- L5 Q1: Design the graph schema → this becomes your Stream C data model
- L5 Q5: Write your L6 blueprint → this becomes your Stream C architecture
- L6: Build the Streamlit dashboard → this is literally what you'll extend in Stream C

### Study Up
1. Read about digital twins in manufacturing (what they are, why they matter)
2. Understand Neo4j graph modeling for production planning
3. Look at Cesium (cesium.com) for 3D geospatial visualization
4. Read about Swedish manufacturing (SBI, steel fabrication, production stations)

---

## Your Mission (8 Weeks, starting May 16)

### Sub-Teams (suggested, 12 interns)

| Sub-Team | Focus | Size |
|----------|-------|------|
| **Dashboard Core** | Streamlit views, Plotly charts, 17 formula engine | 4 |
| **Data Pipeline** | Excel parser, CSV/DB import, Neo4j graph seeding | 3 |
| **Analytics & Alerts** | Bottleneck detection, capacity forecasting, what-if scenarios | 3 |
| **3D Visualization** | Cesium/Three.js factory floor, station layout, load heatmaps | 2 |

### Week 1-2: Foundation
- Extend L6 dashboard from 4 views to 6 views
- Build Excel parser (openpyxl) for real-format production spreadsheets
- Set up PostgreSQL + Neo4j for dual storage
- 3D team: first factory floor model (rectangles for stations, positioned in grid)

### Week 3-4: Formula Engine + Graph Queries
- Implement all 17 production formulas in Python
- Power dashboards from Neo4j queries (not raw CSV)
- Capacity forecasting: "Given current trajectory, which station overloads in week 9?"
- 3D team: color-code stations by load, click station → show projects

### Week 5-6: Intelligence Layer
- Bottleneck alerts (automated detection when actual > planned by threshold)
- What-if scenarios: "Move 2 workers from station 014 to 013 — what happens?"
- Worker coverage gap analysis
- 3D team: embed visualization in Streamlit dashboard

### Week 7-8: Polish + Platform
- Make the dashboard configurable for ANY factory (not hardcoded to one dataset)
- Template system: upload your Excel → get your dashboard
- Performance optimization, mobile responsive
- **Goal: Demo to a real factory owner**

---

## The Future

This dashboard is the **beachhead product** for Life Atlas's industrial digital twin platform.

### Phase 2: Simulation + Optimization (post-intern)
- What-if scenarios with constraint optimization
- Predictive bottleneck detection using historical patterns
- Copilot queries: "Which projects are at risk this month?"
- Integration with real factory systems (AGDA PS for station hours, Visma Net for cost/revenue)

### Phase 3: Full Digital Twin
- Real-time sensor data integration
- 3D walkthrough of factory with live production status
- Multi-factory visualization (combine physical sites into unified virtual factory)
- Edge-native deployment (data stays in-country, on-premise option)

### Scale
- 160 SBI member factories in Sweden alone
- Thousands of similar manufacturers across Europe
- Every factory that runs on Excel is a potential customer
- The platform pattern applies to ANY production environment (not just steel)

---

## Connection to L5/L6

| L5/L6 Component | Stream C Extension |
|-----------------|-------------------|
| Neo4j graph schema (L5 Q1) | Production knowledge graph with all 17 formulas |
| SQL vs Cypher comparison (L5 Q2) | Graph-powered dashboard queries |
| Bottleneck analysis (L5 Q3) | Automated alert system |
| Vector + Graph hybrid (L5 Q4) | "Find similar past projects" for new order estimation |
| Streamlit dashboard (L6) | 6-view production planning dashboard |
| Self-test page (L6) | CI/CD quality gates |

**L5/L6 is not homework. It's your first sprint.**

---

## Key Context

- This is a PLATFORM play, not a one-off dashboard. Think "Shopify for factory dashboards."
- The synthetic data in `challenges/data/` mirrors real production planning patterns
- Real customers exist and are paying — but interns work on the GENERIC platform, not on customer-specific data
- 3D visualization is the differentiator that no competitor has
- Swedish data sovereignty is a requirement, not a nice-to-have
