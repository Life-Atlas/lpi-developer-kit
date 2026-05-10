# Level 4 Submission — Shubham Kumar
**Track A: Agent Builders**

## What I built: Adversarial Agent Mesh

**Code:** `submissions/shubham-kumar/level4/`
**Demo output:** `submissions/shubham-kumar/level4/demo.md`

---

## The core idea

Most multi-agent demos have two agents doing the same thing from different angles. I wanted something where the collaboration is structurally necessary — where neither agent can produce a useful result without the other.

**Agent A — SMILE Implementation Planner** only knows theory. It queries SMILE methodology phases and step-by-step guides from the LPI, then synthesizes a structured implementation roadmap tailored to the user's constraints. It has no idea what fails in practice.

**Agent B — Devil's Advocate Validator** only knows what's gone wrong. It receives Agent A's plan and immediately goes looking for reasons it'll fail — querying real case studies in the same industry and scenario-specific insights. It can't build a plan. It can only break one.

Together they produce something neither can alone: a plan that's been stress-tested against real-world evidence before anyone acts on it. The validator's verdict directly shapes whether you proceed, adjust, or scrap the plan entirely.

---

## Architecture

```
User Input (industry, use case, constraints)
    │
    ▼
Orchestrator
  ├─ [A2A Discovery] reads planner.json + validator.json
  ├─ [Security Gate] sanitizes all 3 input fields — injection blocked here
  │
  ├──► Agent A: SMILE Planner  (planner.py)
  │      LPI calls: smile_phase_detail ×3, get_methodology_step
  │      Output: typed plan JSON {phases, milestones, risks, tools_used}
  │
  │    [Schema validation] orchestrator checks plan structure before passing
  │
  └──► Agent B: Devil's Advocate  (validator.py)
         LPI calls: get_case_studies, get_insights
         [Re-validates + re-sanitizes] all fields from the plan
         Output: typed critique JSON {verdict, risk_score, red_flags, critiques}
    │
    ▼
Final Report: Plan + Critique side by side, full provenance
```

---

## LPI tools used

| Agent | Tool | Why |
|-------|------|-----|
| A (Planner) | `smile_phase_detail` × 3 | Reality-emulation, concurrent-engineering, collaboration-to-innovate details |
| A (Planner) | `get_methodology_step` | Step-by-step execution guide for the first phase |
| B (Validator) | `get_case_studies` | Real-world analogues — where did similar projects succeed or fail |
| B (Validator) | `get_insights` | Scenario-specific pitfalls and known failure patterns |

---

## How A2A works here

The orchestrator reads `planner.json` and `validator.json` before invoking either agent. These cards describe exactly what each agent expects as input and what it returns. I decided to treat A2A discovery as an actual enforcement mechanism — the orchestrator uses the declared schema to validate the plan payload before passing it to Agent B. If Agent A returned something structurally wrong, the message is rejected at the boundary, not inside Agent B.

A `.well-known/agent.json` card at the top of the level4 folder describes the full mesh — both agents, their roles, and the security model.

---

## Security — I tried to break it first

I didn't just add security checks after writing the agents. I wrote the agents, then spent time actively trying to break the system. Five real vulnerabilities found and fixed before submission.

| Attack attempted | What I found | Fix |
|-----------------|-------------|-----|
| Prompt injection through `industry` field | String reached LLM unfiltered | Regex sanitizer on all 3 input fields at orchestrator entry |
| Bypassing orchestrator — injecting via plan payload directly to `validator.py` | Validator trusted plan strings without checking them | Validator re-sanitizes all string fields from plan even from "trusted" Agent A |
| Malformed plan with missing fields piped to validator | Caused undefined behavior / crash | Schema validation runs as first step in validator — rejects before any LPI call |
| Oversized input (1000-char field) | Slow LLM response, potential DoS | Hard 500-char cap per field |
| Bad Ollama model / slow response | System hangs indefinitely | 180s LLM timeout + 300s subprocess timeout |

The most interesting bug was Test 5 (in `security_audit.md`): I could bypass the orchestrator entirely and pipe injection text directly into the validator via the plan payload. The front-door sanitizer meant nothing if someone called the validator directly. Fixing it meant adding re-sanitization inside the validator — treating every agent boundary as a potential entry point, not just the first one.

Full breakdown: `threat_model.md` (what I thought could go wrong) and `security_audit.md` (exact attack commands and outputs).

---

## Run it

```bash
# Setup (from repo root)
npm install && npm run build
pip install requests
ollama serve && ollama pull qwen2.5:1.5b

# Interactive
python submissions/shubham-kumar/level4/orchestrator.py

# Or pass everything directly
python submissions/shubham-kumar/level4/orchestrator.py \
  --industry manufacturing \
  --usecase "predictive maintenance" \
  --constraints "2 developers, 3 months, limited budget"
```

See `demo.md` for full sample output including blocked attack attempts.

---

## Files

```
level4/
├── orchestrator.py       Entry point — A2A discovery, security gate, chains agents, prints report
├── planner.py            Agent A — queries LPI for SMILE data, synthesizes implementation plan
├── validator.py          Agent B — queries LPI for case studies, critiques the plan with evidence
├── security.py           Shared — injection filter, schema validators, timeout constants
├── planner.json          A2A Agent Card for Agent A (input/output schema)
├── validator.json        A2A Agent Card for Agent B (input/output schema)
├── .well-known/
│   └── agent.json        A2A discovery card for the full mesh system
├── demo.md               Full sample run with real output + blocked attack demos
├── threat_model.md       Attack surface analysis — what I thought could go wrong and why
├── security_audit.md     What I actually tried to break, exact commands, exact outputs
├── HOW_I_DID_IT.md       How I built it, what problems I hit, what I learned
└── README.md             Setup and run instructions
```
