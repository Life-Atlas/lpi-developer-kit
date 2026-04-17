# Level 4 — Secure Agent Mesh

**Track A: Agent Builders | Shubham Kumar**

Two agents. One plans, the other tries to break the plan. Neither can produce a useful result on its own — the whole point is that they need each other.

---

## How it works

```
User Input
    │
    ▼
Orchestrator (orchestrator.py)
  │  reads planner.json + validator.json  ← A2A discovery
  │  sanitizes all user input before anything else happens
  │
  ├──► Agent A: SMILE Implementation Planner (planner.py)
  │      Pulls: smile_phase_detail x3, get_methodology_step
  │      Sends back: a structured plan as JSON
  │
  └──► Agent B: Devil's Advocate Validator (validator.py)
         Gets:      Agent A's plan (schema-checked before passing)
         Pulls:     get_case_studies, get_insights
         Sends back: critique JSON — verdict, risk score, red flags, recommendation

Final output: Plan + Critique side by side, with every LPI tool call listed at the bottom
```

Agent A knows SMILE methodology but has no idea what actually fails in practice. Agent B knows real case studies but can't build a plan. Put them together and you get something neither produces alone: a plan that's been stress-tested against real evidence before you act on it.

---

## Setup

```bash
# From the repo root
npm install && npm run build

# Python — only one dependency
pip install requests

# Local LLM
ollama serve
ollama pull qwen2.5:1.5b
```

---

## Running it

```bash
# Just answer the prompts
python submissions/shubham-kumar/level4/orchestrator.py

# Or pass everything upfront
python submissions/shubham-kumar/level4/orchestrator.py \
  --industry healthcare \
  --usecase "patient flow optimization" \
  --constraints "2 developers, 2 months, no cloud"

# Different model
OLLAMA_MODEL=llama3.2 python submissions/shubham-kumar/level4/orchestrator.py ...
```

---

## What's in here

| File | What it does |
|------|---------|
| `orchestrator.py` | Entry point — discovers agents, sanitizes input, chains them, prints report |
| `planner.py` | Agent A — builds the SMILE implementation plan |
| `validator.py` | Agent B — critiques it using real case studies |
| `security.py` | Shared module — injection filter, schema validation, DoS caps |
| `planner.json` | A2A card for Agent A |
| `validator.json` | A2A card for Agent B |
| `threat_model.md` | What I thought could go wrong and why |
| `security_audit.md` | What I actually tried to break and what happened |

---

## Security in short

I tried 7 different attacks on the system before submitting. Found 5 real issues and fixed all of them. Full details in `threat_model.md` and `security_audit.md` but the short version:

- Prompt injection gets caught at the orchestrator before it touches any agent — and again inside the validator in case someone skips the orchestrator entirely
- Inter-agent messages are schema-validated both ways so a compromised Agent A can't send garbage to Agent B
- Timeouts on everything so nothing hangs indefinitely
- LLM prompts don't contain any secrets, so there's nothing to leak even if someone crafts a clever exfiltration prompt
