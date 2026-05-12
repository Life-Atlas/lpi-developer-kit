# Level 4 — Secure Agent Mesh
**Sania Gurung | Track A: Agent Builders**

Two-agent mesh: Digital Twin Readiness Assessor + SMILE Roadmap Synthesiser.

## What It Does

**Agent A** assesses your digital twin project's readiness using LPI case studies and knowledge tools, producing a scored ReadinessReport with gap severity per dimension.

**Agent B** reads that report, calls SMILE methodology tools, and generates a roadmap where every phase explicitly targets a gap Agent A identified.

Neither agent can produce the combined output alone:
- Agent A has no knowledge of SMILE phases
- Agent B has no knowledge of your specific readiness gaps

## Prerequisites

```bash
# From repo root
npm run build
ollama serve
ollama pull qwen2.5:5b
pip install requests
```

## Run

```bash
# From repo root
python submissions/sania-gurung/level4/orchestrator.py \
  --description "Personal digital twin for solo ML engineer tracking sleep, diet, energy vs code quality"
```

Or interactively:
```bash
python submissions/sania-gurung/level4/orchestrator.py
```

## Security Audit

```bash
python submissions/sania-gurung/level4/security_audit.py
# Expected: 6/6 PASS
```

## Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Entry point: A2A discovery, chain agents, render report |
| `readiness_agent.py` | Agent A: calls `get_case_studies`, `query_knowledge`, `get_insights` |
| `roadmap_agent.py` | Agent B: calls `smile_overview`, `smile_phase_detail` (x2), `get_methodology_step` |
| `security.py` | Shared: sanitize, validate schemas, re-sanitize inter-agent strings |
| `readiness_agent.json` | A2A Agent Card for Agent A |
| `roadmap_agent.json` | A2A Agent Card for Agent B |
| `security_audit.py` | Automated 6-scenario attack test runner |
| `threat_model.md` | 5-threat OWASP table with mitigations |
| `security_audit.md` | Findings narrative + fixes implemented |
| `HOW_I_DID_IT.md` | Design decisions and lessons learned |
