# Level 3 Submission — Shubham Kumar
**Track A: Agent Builders**

## Agent: Digital Twin ROI Scoper

**Repo:** https://github.com/kshubham090/lpi-roi-scoper
**Code:** `submissions/shubham-kumar/level3/agent.py`
**A2A Card:** `submissions/shubham-kumar/level3/agent.json`

## What It Does

I built a constraint-aware scoping agent — not a generic digital twin explainer, but something that gives different answers depending on who's asking. A hospital with two developers and no cloud budget gets a completely different plan than a manufacturer with a dedicated ML team. The agent explains *why* each recommendation fits the stated constraints, not just *what* the SMILE phases are.

Takes three inputs:
- Industry (e.g. healthcare, manufacturing, smart buildings)
- Use case (e.g. predictive maintenance, energy optimization)
- Constraints (e.g. small team, 3 months, limited budget)

Queries four LPI tools in sequence, synthesizes via local Ollama LLM, and outputs a structured ROI scope report:

1. **Realistic scope** — what can actually be done given constraints, with reasons
2. **Expected outcomes** — grounded in real case studies returned from the LPI
3. **SMILE phases to prioritize** — the agent chose these phases based on scenario-specific advice from `get_insights`
4. **What to skip/defer** — backed by case study evidence of what fails when done too early
5. **First 3 actions** — concrete steps citing the source tool that informed each one

Every claim cites its source tool. Provenance is printed separately at the end so the reasoning chain is fully traceable.

## Design Decisions

**My approach** was to structure this around constraints first, not features. Most digital twin advice tells you what's possible. The harder problem — and the more useful one — is telling someone what to *skip* given their specific situation. I decided to make "What to Defer" a required output section, not optional, because that's where most failed projects go wrong.

**Tool selection trade-off:** I chose `get_insights` + `get_case_studies` + `query_knowledge` as the three primary tools because together they cover three different perspectives — advice, evidence, and technical depth. I added `smile_overview` as a fourth call to give the LLM a baseline understanding of the full methodology before it reasons about which phases to prioritize. I tried using only three tools first, but the output kept conflating phases — adding the overview grounded the LLM's recommendations noticeably.

**LLM choice:** I chose Ollama (local) over a cloud API because the submission environment has no API key requirement and Ollama runs on any machine without setup friction. The trade-off is output quality — `qwen2.5:1.5b` is fast but sometimes truncates. I fixed this by trimming the context slices fed to the model and adding a fallback plan constructed directly from the raw tool data when JSON parsing fails.

**Why this approach is different from just calling the tools manually:** The agent reasons *against* the constraints. It doesn't just summarize what `get_insights` returned — it filters recommendations through the constraint lens and explains the decision. If the constraint is "no cloud", the agent explicitly flags which SMILE activities require cloud infrastructure and recommends deferring them, citing the source that informed that call.

## LPI Tools Used

| Tool | Arguments | Purpose |
|------|-----------|---------|
| `smile_overview` | *(no args)* | Baseline understanding of all SMILE phases before reasoning begins |
| `get_insights` | `scenario: "{usecase} in {industry}"` | Scenario-specific advice — the agent chose recommendations based on this data |
| `get_case_studies` | `query: "{industry}"` | Real-world evidence; every outcome claim traces back to a case study returned here |
| `query_knowledge` | `query: "{usecase} digital twin implementation"` | Technical implementation depth; decision on what to defer was grounded in this |

## Sample Tool Output (Real)

When I ran: `get_case_studies(query="manufacturing")`, the response included:

```
result: [
  { "name": "Siemens Amberg", "outcome": "99.9988% quality rate after Reality Emulation phase",
    "constraint": "required 18 months of sensor data before model was useful" },
  { "name": "BMW Leipzig", "outcome": "30% reduction in retooling time via concurrent engineering",
    "constraint": "needed dedicated integration team — not viable for small shops" }
]
```

The agent uses this retrieved data directly in the "Expected Outcomes" section — it doesn't hallucinate analogues, it cites what the tool returned.

## Tech Stack

- Python 3.10+
- Ollama (local LLM — no API key required)
- LPI MCP server via subprocess (JSON-RPC stdio)
- Standard library only (+ `requests`)

## Run It

```bash
# Interactive
python submissions/shubham-kumar/level3/agent.py

# CLI
python submissions/shubham-kumar/level3/agent.py \
  --industry healthcare \
  --usecase "patient flow optimization" \
  --constraints "2 developers, 2 months, no cloud"
```

## What I'd Do Differently

The current implementation re-starts the MCP subprocess for every run. A better approach would be to keep the process alive across sessions and cache tool responses — `get_case_studies` results don't change, so re-querying them on every run is wasteful. I'd also replace the regex-based JSON extraction with a structured output mode if the LLM supports it, which would eliminate the fallback path entirely.
