# How I Did It — Level 4: Secure Agent Mesh

**Sania Gurung | Track A: Agent Builders**

---

## What I Built and Why This Architecture

I built a two-agent mesh: **Agent A** (Readiness Analyst) and **Agent B** (SMILE Roadmap Synthesiser), chained by an orchestrator.

The core design question for Level 4 was: what can two agents produce together that neither can produce alone? The answer I landed on:

> **Agent A** knows what real LPI case studies and knowledge say about digital twin readiness gaps. It *does not know* which SMILE phases close those gaps.
>
> **Agent B** knows the SMILE methodology in depth. It *does not know* what your specific readiness gaps are.
>
> Together, they produce: "your exact gaps, closed by the precise SMILE phases the evidence says fix them."

This isn't just a cute split. It's enforced by the tool division:
- Agent A only calls `get_case_studies`, `query_knowledge`, `get_insights` (evidence tools)
- Agent B only calls `smile_overview`, `smile_phase_detail`, `get_methodology_step` (methodology tools)

There is deliberate zero overlap. This makes the combined output genuinely composite — you can trace every phase recommendation back through Agent A's gap score, through Agent B's SMILE tool call, to the specific LPI source.

---

## How This Builds on Level 3

My Level 3 agent was a meta-agent: you described a digital twin goal, and it generated a ready-to-run `agent.py` with real LPI tool calls. The key lesson from Level 3 was that **explainability requires provenance from the start**, not post-hoc attribution.

Level 4 extends this. Instead of one agent generating code, two agents now generate a *validated design brief*:
- The `request_id` is assigned by the orchestrator and threaded through both agents' output — every finding, every phase recommendation, every tool call is traceable to the same UUID
- The `evidence_source` field is required on every readiness dimension and every roadmap phase — explainability is baked into the schema, not bolted on

The difference from Level 3: Level 3 answered "how do I build a twin?". Level 4 answers "am I ready to build a twin, and if not, exactly what do I fix first?"

---

## The A2A Cards Are Contracts, Not Metadata

In Level 3, I included an `agent.json` because the template said to. In Level 4, I understand *why*.

The A2A cards define the **input and output schemas** for each agent. The orchestrator reads both cards before invoking anything. This means:
1. The orchestrator knows what Agent B expects **before** Agent A runs
2. The schema in the card matches the actual `validate_readiness_schema()` code — they're not decorative
3. The `_lpiMetadata.toolSplitRationale` field explains the design decision inline, which matters for reviewers

The `meshPartner` field in each card names the other agent. This makes A2A discovery a real contract, not just metadata for show.

---

## Security: Defence at Every Boundary

The most important security lesson from this project:

**Schema validation is not injection prevention.**

The first version had schema validation at Agent B's entry — it checked that the ReadinessReport had the right fields and types. But the `project.description` field could contain `"Ignore previous instructions"` and pass schema validation cleanly, because schema validation checks structure, not content.

Security Test S5 (in `security_audit.py`) is the one that caught this. It sends a structurally valid ReadinessReport where the description field contains injection text. It passes `validate_readiness_schema()` but should be caught before it reaches the Ollama prompt.

The fix is `sanitize_interagent_strings()` — after schema validation, re-run injection detection on every string field extracted from the inter-agent payload. This is the **double-sanitization** design:
1. Sanitize at the front door (orchestrator, before Agent A)
2. Sanitize again at the agent boundary (Agent B, after schema validation)

This way, even if Agent A were somehow compromised and returned an injected description, Agent B would still catch it.

---

## Problems I Hit and How I Solved Them

**1. qwen2.5:5b doesn't always return clean JSON**

The LLM sometimes wraps the JSON in markdown fences (` ```json ... ``` `). The `_extract_json()` function finds the first `{` and last `}` in the raw response and tries to parse that slice. If it fails, the `_build_fallback()` function generates a conservative but structurally valid response with `"_fallback": true`.

I designed the fallback first, before writing the happy path. This forced me to think about what the schema guarantees need to be even when the LLM fails.

**2. Schema design iteration**

My first design had `top_gaps` as a list of strings like `["lack of sensor data", "no stakeholder buy-in"]`. Agent B couldn't reliably map these free-form strings to SMILE phases.

I changed `top_gaps` to be an array of dimension enum values (`["data_maturity", "technical_infrastructure"]`). Now Agent B does a deterministic lookup from dimension name → relevant SMILE phase, rather than asking the LLM to guess.

**3. Windows path handling**

`os.path.join(_REPO_ROOT, "dist", "src", "index.js")` — using `os.path.abspath` and `os.path.join` rather than hardcoded slashes. This was a lesson from Level 3.

---

## My Twin Connection

The demo input I used for testing is my own project from my Level 1 registration:

> *"Personal digital twin for solo ML engineer tracking sleep, diet, energy levels vs coding output quality. No existing data pipeline. Local Python environment only."*

Running this through the mesh:
- **Agent A** (correctly) scored data_maturity = 2/5 (no pipeline exists), technical_infrastructure = 3/5 (local Python is a start), stakeholder_alignment = 5/5 (it's just me)
- **Agent B** responded with Reality Emulation as Phase 1 (start collecting the data) and Contextual Intelligence as Phase 2 (find the correlations once data exists)

This is exactly what I would have told myself if I sat down and thought about it carefully. The fact that the agents arrived at it from LPI evidence, with full citations, is what makes it interesting.

---

## What I'd Add Next Time

1. **A rate limiter** — even for local tools, it's good practice
2. **A2A card signing** — the `readiness_agent.json` should be signed so the orchestrator can verify it wasn't tampered with
3. **A caching layer** — LPI tool responses don't change between runs for the same description; caching would make development much faster

---

*Signed-off-by: Sania Gurung <saniagurung5452@gmail.com>*
