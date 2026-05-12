# WINNIIO Intern Program — May-June 2026

**35 interns | 3 streams | 8 weeks (May 9 – July 4)**  
**Sprint 0 (everyone): L5/L6 due Tuesday May 13**  
**Stream work begins: Friday May 16**

---

## Sprint 0: L5/L6 — Universal Foundation (May 6-13)

ALL interns complete L5 (written) + L6 (build) regardless of stream.

| What | Where |
|------|-------|
| L5 Brief (Graph Thinking) | `challenges/level5-knowledge-graph-foundations.md` |
| L6 Brief (Build It) | `challenges/level6-build-a-knowledge-graph.md` |
| Scoring Guide | `challenges/scoring-guide-l5l6.md` |
| Data (3 CSVs) | `challenges/data/` |
| Submissions | `submissions/<github-username>/level5/` and `level6/` |

**Skills taught:** Neo4j, Cypher, Streamlit, Plotly, deployment, hybrid vector+graph thinking.

---

## The 3 Streams

### Stream A — Boardy AI Superconnector (10 interns)

| | |
|---|---|
| **Brief** | `docs/streams/stream-a-boardy.md` |
| **Repo** | [LifeAtlas/lifeatlas-boardy](https://github.com/LifeAtlas/lifeatlas-boardy) |
| **Customer** | Nicolas (internal — WINNIIO ecosystem) |
| **What** | AI-powered professional matching using Neo4j + Vector DB + Hybrid RAG |
| **Week 1 demo** | Top 10 intern pairings with SMILE-reasoned explanations |

**Interns:** Sanskriti, Shubham Kumar, Shourya Solanki, Yash Maheshwari, Praveen Singh, Aryan, Ankit Kumar Singh, Jahanvi Gupta, Vansh Singhal, Adil Islam

---

### Stream B — DataPro+ DealFlow (13 interns)

| | |
|---|---|
| **Brief** | `docs/streams/stream-b-datapro-dealflow.md` |
| **Repos** | [LifeAtlas/datacenter-flow](https://github.com/LifeAtlas/datacenter-flow) (frontend) + [LifeAtlas/DataCenterBackend](https://github.com/LifeAtlas/DataCenterBackend) (backend) |
| **Customer** | Josh Young (DataProPlus / EnergyJobline, UK) |
| **What** | Gated datacenter marketplace with 3-layer access control, NDA workflow, referral engine |
| **Week 1 demo** | Clone running locally, Supabase schema designed, "Request More Info" workflow planned |

**Interns:** Daksh Garg, Abhinav Chaudhary, Varshit Pratap Singh Bhadauria, Touqeer Hamdani, Aditi Mehta, Ananyaa M, Priyanshu Bhardwaj, Rahul Bijarnia, Khushi Garg, Lavanya Parashar, Saima Afroz, Sonal Yadav, V Bharath Raju

---

### Stream C — Industrial Twin Dashboard (12 interns)

| | |
|---|---|
| **Brief** | `docs/streams/stream-c-industrial-twin-dashboard.md` |
| **Repo** | [LifeAtlas/factory-twin-dashboard](https://github.com/LifeAtlas/factory-twin-dashboard) |
| **Customer** | Nicolas (internal — platform play for 160+ Swedish factories) |
| **What** | Generic production planning dashboard replacing Excel, with knowledge graph + 3D visualization |
| **Week 1 demo** | L6 dashboard extended to 6 views, factory floor 3D model started |

**Interns:** Aadyant Sood, Jaivardhan Singh, Harshit Kumar, Kailash Narayana Prasad, Sania Gurung, Yashika Verma, Naman Anand, Dia Vats, Devika Hooda, Srishti Gusain, Anupaul Saikia, Abishek Sharma

---

## Timeline

| Date | Milestone |
|------|-----------|
| **Tue May 6** | L5/L6 challenges live. Interns start. |
| **Tue May 13** | L5/L6 deadline. Submissions via PR. |
| **Wed May 14** | L5/L6 scored. Stream adjustments if needed. |
| **Fri May 16** | Stream work begins. Week 1 demos. |
| **Fri May 23** | Week 2 demos. All streams productive. |
| **Fri May 30** | Week 3 demos. First external stakeholder feedback. |
| **Fri Jun 6** | Week 4 demos. Integration milestones. |
| **Fri Jun 13** | Week 5 demos. Advanced features. |
| **Fri Jun 20** | Week 6 demos. Testing + client feedback. |
| **Fri Jun 27** | Week 7 demos. Hardening + deployment. |
| **Fri Jul 4** | Final demos. Handoff. Retrospective. |

---

## Scoring & Tracking

| Metric | How | Cadence |
|--------|-----|---------|
| PRs merged | GitHub API scan across all 3 stream repos | Weekly (Friday 14:00 IST) |
| Lines changed | Same scan | Weekly |
| Reviews given | Same scan | Weekly |
| Streak weeks | Consecutive weeks with merged PR | Rolling |
| L5/L6 scores | Manual scoring by leads | One-time (May 14) |

LPI leaderboard: `lpi-developer-kit/docs/index.html`

---

## Key Principles

1. **L5/L6 is Sprint 0** — teaches the universal toolchain (Neo4j + Streamlit + Vector + Deploy)
2. **Impact first, data last** — start with the decision, work backward to the data
3. **MVT (Minimal Viable Twin)** — one real answer from one real query = your first twin
4. **Daily commits** — no silent days
5. **Weekly demos** — every Friday, show what works
6. **Staging workflow** — feature branch off staging → PR to staging → never touch main

---

## Management

```
Nicolas (CEO) — vision, stakeholder relationships, weekly demo review
  └── Danial (Tech Lead) — code review, architecture decisions, GitHub admin
       ├── Stream A leads — Boardy coordination
       ├── Stream B leads — DataPro+ coordination
       └── Stream C leads — Industrial Twin coordination
```

**Communication:** WhatsApp for async. Weekly demo Fridays. Danial for technical questions.
