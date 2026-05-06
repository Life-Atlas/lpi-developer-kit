# Scoring Guide — Level 5 & 6

**For team leads. Scoring L6 takes 2 minutes per intern.**

## L6 Scoring Flow (2 min per submission)

1. Open `DASHBOARD_URL.txt` from their PR
2. Click "Self-Test" page → read the auto-score (20 pts)
3. Click through 4 dashboard pages → score each (45 pts)
4. Open PR files tab → scan for `.env` leak, check README exists (15 pts)
5. Post total as PR comment, merge in Friday batch

## L5 Quick Checklist

```
[ ] /20 — Q1: Diagram has 6+ labels, 8+ rels, properties on rels
[ ] /20 — Q2: SQL + Cypher both work, insight isn't generic
[ ] /20 — Q3: Bottleneck analysis uses actual CSV numbers
[ ] /20 — Q4: Hybrid query is practical
[ ] /20 — Q5: Blueprint matches what they built in L6
___/100
```

## L6 Score Sheet (copy-paste into PR comment)

```
## Level 6 Score

**Self-Test:**
[ ] /20 — All 6 checks green (or note which failed)

**Dashboard Pages:**
[ ] /10 — Project Overview (all 8 projects, metrics visible)
[ ] /10 — Station Load (interactive chart, overload highlighted)
[ ] /10 — Capacity Tracker (deficit weeks red/flagged)
[ ] /10 — Worker Coverage (matrix/table, SPOF stations flagged)
[ ] /5  — Navigation works (sidebar or tabs)

**Deployment:**
[ ] /15 — Streamlit URL loads, app runs

**Code:**
[ ] /5  — No credentials in repo
[ ] /5  — README has run instructions
[ ] /5  — seed_graph.py uses MERGE (idempotent)

**TOTAL: __/100**
```

## Red Flags

- `.env` or credentials in code: **-20, mandatory fix before merge**
- Copy-paste from another intern: **both get 0**
- Dashboard reads CSV directly (not Neo4j): **-20 on dashboard points**
- Self-test page missing: **0/20 on self-test + flag as incomplete**

## GitHub Quota

- No CI runs on L5/L6 PRs (existing workflows filter by `level-2`/`level-3` in title)
- Batch-merge all reviewed PRs on Thursday May 15
- One CI trigger total, not 33
