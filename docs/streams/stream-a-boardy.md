# Stream A — Boardy AI Superconnector

**Customer:** Nicolas (internal — WINNIIO ecosystem)  
**Repo:** `LifeAtlas/lifeatlas-boardy`  
**Team Size:** 10 interns  
**Duration:** May 16 – June 27, 2026  
**Reference product:** boardy.ai

---

## Background

### The Problem

Professional networking is broken. LinkedIn connects people who are SIMILAR. But the most valuable introductions connect people whose REALITIES COMPLEMENT each other — someone who has what you need, and needs what you have, RIGHT NOW.

No platform does timing-aware, context-sensitive, explained introductions at scale.

### The Concept

**Boardy.ai** is an AI that predicts who you should meet and makes the introduction — via conversational interface, proactively, with reasoning.

**WINNIIO's version:** Same concept, powered by SMILE methodology. The matching isn't keyword similarity — it's reality-aware, timing-sensitive, and explains its reasoning.

### Cold Start Solution

Every matching system dies without data. Our unfair advantage: **we already have a real network.**

| Data source | What it gives us | Available now? |
|-------------|-----------------|:-:|
| 32 intern soul files | Skills, interests, tracks, identity statements | YES |
| Stream assignments | Who's working on what, who needs what help | YES |
| Meeting transcripts | Who spoke, engagement signals | YES |
| GitHub activity | Actual contribution patterns | Week 2+ |
| Daily standups | Blockers, progress, collaboration signals | Week 2+ |

**Day 1 network = the intern cohort. Day 30 network = WINNIIO's full ecosystem.**

---

## SMILE-Powered Matching vs Normal Matching

| Normal matching | SMILE matching |
|----------------|---------------|
| Cosine similarity on profile embeddings | What's each person's REALITY right now? |
| Static: "you're both in AI" | Hypothesis: "If A meets B, expected outcome is X" — testable |
| One signal (skills overlap) | Multi-signal: skills + needs + timing + personality + complementarity |
| Profile-based | Context-based: "A just hit a blocker that B solved yesterday" |
| Reactive: user searches | Proactive: "Something changed. This intro is now more relevant." |

**The SMILE difference:** We don't match people who are SIMILAR — we match people whose REALITIES complement each other RIGHT NOW.

---

## Architecture — Neo4j + Vector DB + Hybrid RAG

```
Input Layer:
  ├── Soul files (structured profiles)
  ├── Conversation agent (learns needs/offers over time)
  └── Activity signals (git, standups, meetings)

Knowledge Layer:
  ├── Neo4j Graph:
  │     ├── Nodes: Person, Skill, Interest, Project, Track
  │     ├── Edges: HAS_SKILL, NEEDS, OFFERS, WORKS_ON, COLLABORATED_WITH
  │     └── Graph algorithms: community detection, centrality, structural holes
  │
  ├── Vector DB (Qdrant or pgvector):
  │     ├── Profile embeddings (identity + skills + interests)
  │     ├── Need embeddings / Offer embeddings
  │     └── Semantic similarity matching
  │
  └── Hybrid RAG Matching:
        ├── Graph retrieval: structural matches (network position, communities)
        ├── Vector retrieval: semantic matches (meaning similarity)
        ├── Fusion: weighted combination of both signals
        └── LLM Re-ranker: scores top candidates with SMILE reasoning

Output Layer:
  ├── Introduction message (personalized, contextual)
  ├── Match reasoning (transparent: "Graph says X + Semantics say Y → therefore Z")
  └── Feedback capture (did it work? → updates weights)
```

---

## The Hybrid RAG Pipeline

```
Step 1 — Graph Retrieval (Neo4j):
  MATCH (a:Person)-[:HAS_SKILL]->(s)<-[:NEEDS]-(b:Person)
  WHERE a <> b AND NOT (a)-[:CONNECTED_TO]-(b)
  → Candidates from structural opportunity

Step 2 — Vector Retrieval:
  embed(A.needs) → nearest neighbors in offers_index
  → Candidates from semantic similarity

Step 3 — Hybrid Fusion:
  graph_score + vector_score + timing_score + reciprocity
  → Unified ranked list

Step 4 — LLM Re-rank:
  Top 20 → Claude: "Rate match quality, explain WHY using SMILE reasoning"
  → Final top 10 with explanations
```

---

## Progressive Build

### Phase A: Static Matching (Week 1)
- Input: 32 soul files (already exist)
- Output: Top 10 recommended pairings with SMILE-reasoned explanations
- Validation: Nicolas evaluates — "yes that's smart" or "no that's wrong"
- No LLM needed for scoring. LLM only for generating explanation text.

### Phase B: Conversational (Week 2-3)
- User messages Boardy → asks questions → builds reality canvas
- Matches recalculate based on new information
- Proactive: "Based on what you just told me, you should meet X"

### Phase C: Live Network (Week 4-6)
- Activity signals (git, standups) feed into graph automatically
- Feedback loop: "Did this intro help?" → improves scoring
- Multi-vertical config (extend beyond intern network)

### Phase D: Platform (Week 7-8)
- Polish, hardening, demo-ready
- Evaluation metrics: does hybrid beat graph-only? Beat vector-only?
- Documentation and handoff

---

## What Makes This Not "LinkedIn People You May Know"

1. **Complementarity over similarity.** Matches people whose gaps fill each other's strengths.
2. **Timing-aware.** Matches change as situations change.
3. **Explains WHY.** Every intro comes with SMILE-reasoned explanation.
4. **Reciprocal.** Won't suggest a match unless BOTH sides benefit.
5. **Domain-aware.** Understands manufacturing vs health vs telecom.
6. **Proactive.** Notices changes and surfaces opportunities.

---

## Connection to L5/L6

| L5/L6 Component | Stream A Extension |
|-----------------|-------------------|
| Neo4j graph schema (L5 Q1) | Person-Skill-Need-Offer knowledge graph |
| Vector + Graph hybrid (L5 Q4) | The entire matching engine |
| Streamlit dashboard (L6) | Match visualization + network graph |
| Self-test page (L6) | Automated match quality evaluation |

**L5 Bonus A** is specifically designed for this stream: model 5 intern profiles as a knowledge graph, write a complementary-skills query.

---

## Budget + Constraints

- Week 1 API cost: ~$2-5. Scoring is pure Python. Only explanations use LLM.
- Week 2+: Conversation agent adds cost. Budget: $10/day cap.
- Token tracking from Day 1.
- No hallucinated profiles. Use only soul file data.
- Prompts versioned in `prompts/`.

---

## Rules

- The intern network is your test data AND your first product.
- Impact first, data last. "What introduction changes someone's week?"
- MVT: One good match, well-explained. That's your twin.
- Daily commits. Weekly demos.
- Every match must explain WHY — no black-box recommendations.
