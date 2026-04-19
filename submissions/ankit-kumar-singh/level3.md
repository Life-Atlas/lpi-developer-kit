# Level 3 Submission — Ankit Kumar Singh

**Track:** A — Agent Builders  
**GitHub:** [ankitsinghh007](https://github.com/ankitsinghh007)

---

## Agent Repository

**https://github.com/ankitsinghh007/smile-hospital-agent**

---

## What I built

**SMILE Digital Twin Advisor — Hospital Operations**

A domain-specific AI agent that takes a real hospital operations problem and
produces a structured, phase-by-phase SMILE implementation roadmap.

Real-world problems solved:
- Bed utilisation variance (surgical ward at 98%, medical at 60%)
- MRI/CT equipment downtime (10h/week unplanned loss)
- Hospital energy waste (HVAC fixed schedules, 38% cost rise)
- Patient readmission prevention (chronic disease monitoring)

---

## LPI Tools Used (all 7 tools, 8 calls)

| Step | Tool | Why |
|------|------|-----|
| 1 | `smile_overview` | SMILE methodology baseline — always first |
| 2 | `list_topics` | Discover all KB topic areas before searching |
| 3 | `query_knowledge` | Title-boosted first search (Easter egg #3 exploit) |
| 4 | `query_knowledge` | Refined second search based on step 3 findings |
| 5 | `get_case_studies` | Domain-matched case evidence |
| 6 | `get_insights` | Scenario-specific SMILE recommendations |
| 7 | `smile_phase_detail` | Deep dive into most relevant phase for domain |
| 8 | `get_methodology_step` | Phase 2 MVT steps — always relevant |

---

## Easter Eggs Found (all 3)

| Egg | Location | Answer |
|-----|----------|--------|
| #1 | `src/index.ts` — comment at top of file | (same clue as #2) |
| #2 | Query `"impact first data last"` → count ontology mentions | **6** |
| #3 | `data/knowledge-base.json` entry `kb-egg` — "The Hidden Principle" | Title match scoring exploited in `_title_boost_query()` |

Full implementation details, reasoning process, and easter egg analysis are documented in [HOW_I_DID_IT.md](https://github.com/ankitsinghh007/smile-hospital-agent/blob/main/HOW_I_DID_IT.md).

---

## Key differentiators

1. **Multi-step reasoning loop** — `query_knowledge` called twice: first with
   title-boosted query, second with terms extracted from the first result
2. **Decision routing** — which SMILE phase to deep-dive depends on the domain
   detected from the problem (not hardcoded)
3. **All 7 tools used** — including `list_topics` before searching and
   both `smile_phase_detail` + `get_methodology_step`
4. **Structured output** — Impact Statement → Phase 1 → Phase 2 → Phase 3 →
   Roadmap → Pitfalls → Sources (not prose blob)
5. **Full provenance table** — every tool call shows: tool, why called, chars
   returned, latency

---

## Example

**Input:**
"MRI downtime 10h/week"

**Output (summary):**
- Structured SMILE roadmap (Impact → Phases → KPIs → Roadmap → Pitfalls)
- 8 tool calls with reasoning (including 2-pass query_knowledge)
- Cited insights from SMILE knowledge base
- Provenance tracking for every tool call

