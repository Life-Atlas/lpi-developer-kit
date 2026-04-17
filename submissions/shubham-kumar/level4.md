# Level 4 Submission — Shubham Kumar
**Track A: Agent Builders**

## What I built: SMILE Planner + Devil's Advocate Validator

**Code:** `submissions/shubham-kumar/level4/`

---

## The idea

I wanted two agents where the collaboration actually meant something — not just two scripts answering the same question from different angles, but two agents doing completely different jobs that only produce value together.

So: one agent plans, the other one tries to break the plan.

**Agent A — SMILE Implementation Planner** takes your industry, use case, and constraints. It queries the SMILE methodology phases and step-by-step guides from the LPI, and synthesizes a structured implementation roadmap — which phases to tackle first, why, how long each should take, what the milestones are. Output is typed JSON.

**Agent B — Devil's Advocate Validator** receives that plan and immediately goes looking for reasons it'll fail. It queries real case studies in the same industry and scenario-specific insights from the LPI, then comes back with a risk score, phase-level critiques with evidence, red flags, and one concrete recommendation. Every finding cites the LPI source it came from.

Agent A has no idea what actually goes wrong in practice. Agent B can't build a plan. Together they produce something neither can on its own: a plan that's been stress-tested against real-world evidence before anyone acts on it.

---

## LPI tools used

| Agent | Tool | Why |
|-------|------|-----|
| A (Planner) | `smile_phase_detail` × 3 | Gets reality-emulation, concurrent-engineering, collaboration-to-innovate details |
| A (Planner) | `get_methodology_step` | Step-by-step guide for the first phase the team should execute |
| B (Validator) | `get_case_studies` | Finds real-world analogues in the same industry — where did similar projects succeed or fail |
| B (Validator) | `get_insights` | Scenario-specific pitfalls and advice for the exact use case |

---

## How A2A works here

The orchestrator reads `planner.json` and `validator.json` before invoking either agent. These cards describe what each agent does, what it expects as input, and what it returns. The orchestrator uses this to validate the plan schema before passing it from Agent A to Agent B — it's not just documentation, it's an actual enforcement boundary.

---

## Security

I didn't just add security as an afterthought — I tried to break the system first and fixed what I found. Seven attacks attempted, five real vulnerabilities found and fixed.

| What I tried to exploit | What I did about it |
|------------------------|---------------------|
| Prompt injection via user input fields | Regex sanitizer on all 3 fields before anything runs |
| Bypassing the orchestrator and injecting via the plan payload directly into the validator | Validator re-sanitizes all string fields it receives, even from "trusted" Agent A |
| Sending a malformed plan with missing fields to trigger undefined behavior | Schema validation as first step in validator — rejects anything structurally wrong |
| Flooding with oversized inputs | Hard cap of 500 chars per field |
| Making the system hang via a slow or broken LLM | 180s Ollama timeout, 300s subprocess timeout |

Full breakdown in `threat_model.md` (what I thought could happen and why) and `security_audit.md` (what I actually tried and the exact outputs).

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
  --industry healthcare \
  --usecase "patient flow optimization" \
  --constraints "2 developers, 2 months, no cloud"
```

---

## Files

```
level4/
├── orchestrator.py     Entry point — discovers agents, chains them, prints report
├── planner.py          Agent A — builds the implementation plan
├── validator.py        Agent B — critiques it with real evidence
├── security.py         Shared — injection filter, schema validators, timeouts
├── planner.json        A2A Agent Card for Agent A
├── validator.json      A2A Agent Card for Agent B
├── threat_model.md     What I thought could go wrong
├── security_audit.md   What I actually tried to break + what I fixed
├── HOW_I_DID_IT.md     How I built it and what I learned
└── README.md           Setup and run instructions
```
