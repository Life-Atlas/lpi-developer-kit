# Level 5 — Graph Thinking

**Type:** Written + 1 diagram  
**Deadline:** Tuesday May 13, 2026 23:59 UTC  
**Submission:** PR to `lpi-developer-kit` → `submissions/<your-github-username>/level5/answers.md`  
**PR title:** `level-5: Your Name`  
**Time:** 2-3 hours  

---

## Why This Matters

This isn't a homework exercise. You're about to work on real products for real clients:
- **VSAB Dashboard** → replacing a 46-sheet Excel for a steel manufacturer (paying client, 150K SEK)
- **Boardy** → AI-powered networking agent (matching people using graph + vector)
- **Factory 3D** → digital twin with spatial visualization
- **DataPro+** → datacenter marketplace

**ALL of these run on knowledge graphs + vector search.** L5 teaches you to THINK in graphs. L6 proves you can BUILD one. Your performance here determines your readiness for stream work starting May 16.

---

## Context

You've been given a **real factory production dataset** (`challenges/data/`). It comes from a Swedish steel fabrication company running 8 construction projects across 9 production stations. The data is in 3 CSV files:

- `factory_production.csv` — 68 rows: projects × products × stations × weeks (hours planned vs actual)
- `factory_workers.csv` — 13 workers with stations, certifications, roles
- `factory_capacity.csv` — 8 weeks of capacity vs demand

This is actual production planning data. The company currently manages it in a 46-sheet Excel workbook. Your job over L5+L6 is to turn it into something better.

**Pro tip:** Do L5 FIRST (design your schema), then L6 (build it). L5 Q5 IS your blueprint for L6.

---

## 5 Questions (20 pts each)

### Q1. Model It (20 pts)

Look at the 3 CSVs. Design a **graph schema** that captures the relationships between projects, products, stations, workers, and weeks.

- Draw a diagram with node labels and relationship types (hand-drawn photo, draw.io, Mermaid, ASCII — any format)
- At least **6 node labels** and **8 relationship types**
- At least 2 relationships must carry data (e.g., `WORKED_AT {hours: 38.5, week: "w1"}`)
- Save as `schema.png` (or `schema.md` if using Mermaid)

### Q2. Why Not Just SQL? (20 pts)

Write ONE query that answers: *"Which workers are certified to cover Station 016 (Gjutning) when Per Gustafsson is on vacation, and which projects would be affected?"*

1. Write it in SQL (assume reasonable tables)
2. Write it in Cypher (using your schema from Q1)
3. In 2-3 sentences: what does the graph version make obvious that SQL hides?

### Q3. Spot the Bottleneck (20 pts)

Look at `factory_capacity.csv`. Multiple weeks show capacity deficits.

1. Using `factory_production.csv`, identify which projects/stations are causing the overload
2. Write a Cypher query that would find: *"All projects where actual_hours > planned_hours by more than 10%, grouped by station"*
3. How would you model this alert as a graph pattern? (e.g., a `(:Bottleneck)` node, a relationship property, or something else?)

### Q4. Vector + Graph Hybrid (20 pts)

The factory gets new project requests described in free text, like:
> "450 meters of IQB beams for a hospital extension in Linköping, similar scope to previous hospital projects, tight timeline"

1. What would you embed? (project descriptions? product specs? worker skills? something else?)
2. Write a query that combines: "find similar past projects [vector] that used the same stations and had variance < 5% [graph]"
3. Why is this more useful than just filtering by product type?

**Think about this:** The Boardy team will use this EXACT pattern — but instead of matching projects, they'll match PEOPLE (whose needs embed close to whose offers, AND who are in the same graph community).

### Q5. Your L6 Plan (20 pts)

Write your blueprint for Level 6. Be specific:
1. Your node labels and what CSV columns map to them
2. Your relationship types and what creates them
3. 3+ Streamlit dashboard panels you'll build (e.g., "project timeline heatmap", "station load bar chart", "worker coverage matrix")
4. Which Cypher queries power each panel

---

## Submission

```
submissions/<your-github-username>/level5/
├── answers.md
└── schema.png (or schema.md)
```

---

## How This Connects to Your Stream

| If you're on... | L5/L6 teaches you... |
|-----------------|---------------------|
| **VSAB Dashboard** | The exact graph schema + Streamlit skills you'll use with real client data |
| **Boardy** | Graph modeling + hybrid query patterns — your matching engine is built on this |
| **3D Factory** | The station/project data model that feeds your 3D visualization |
| **DataPro+** | Graph thinking for datacenter relationship mapping |
| **LifeAtlas** | Knowledge graph foundations for the professional matching layer |

**Everyone does L5/L6. No exceptions. This is your Sprint 0.**
