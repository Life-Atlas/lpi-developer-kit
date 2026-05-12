# Digital Twin ROI Scoper

An LPI agent that takes your industry, use case, and resource constraints — then tells you exactly what scope is realistic, what outcomes to expect, which SMILE phases to prioritize, and what to defer.

## Requirements

- Node.js 18+ (for the LPI MCP server)
- Python 3.10+
- Ollama running locally

```bash
pip install requests
ollama serve
ollama pull qwen2.5:1.5b
```

## Setup

```bash
# From lpi-developer-kit root
npm install
npm run build
```

## Run

**Interactive mode:**
```bash
cd submissions/shubham-kumar/level3
python agent.py
```

**CLI mode:**
```bash
python agent.py --industry healthcare --usecase "patient flow optimization" --constraints "2 developers, 2 months, no cloud"
python agent.py --industry manufacturing --usecase "predictive maintenance" --constraints "small team, limited budget, 3 months"
python agent.py --industry "smart buildings" --usecase "energy optimization" --constraints "no cloud, 1 engineer, 6 weeks"
```

**Use a different model:**
```bash
python agent.py --model qwen2.5:3b --industry agriculture --usecase "crop monitoring" --constraints "solo developer, 1 month"
```

## What It Outputs

```
== ROI SCOPE REPORT ==

## 1. Realistic Scope
...

## 2. Expected Outcomes
...

## 3. SMILE Phases to Prioritize
...

## 4. What to Skip or Defer
...

## 5. First 3 Actions
...

## Sources
[Tool: get_insights(...)] — provided scenario-specific advice
[Tool: get_case_studies(...)] — provided real-world analogues
[Tool: query_knowledge(...)] — provided technical implementation context

== PROVENANCE ==
[1] get_insights(...)
[2] get_case_studies(...)
[3] query_knowledge(...)
```

## LPI Tools Used

| Tool | Purpose |
|------|---------|
| `get_insights` | Scenario-specific SMILE implementation advice |
| `get_case_studies` | Real-world analogues in the same industry |
| `query_knowledge` | Technical knowledge for the use case |
