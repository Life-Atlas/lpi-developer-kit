# Level 3 Submission — Ananyaa M

## Agent GitHub Repository
https://github.com/ananyaa05/ananyaa-personal-twin-agent

## LPI tools referenced
The agent queries the official LPI methodology tools using real Inter-Process Communication (IPC) to the Node.js MCP server:
* smile_overview
* query_knowledge
* get_case_studies
* smile_phase_detail

## Setup Instructions
1. Ensure the `lpi-developer-kit` repository is located in the same parent directory as this agent repository.
2. Ensure Ollama is isntalled and running locally (`ollama serve`). Also, make sure to download TinyLlama model.
3. Clone the agent repository.
4. Run the agent using Python with a concept argument: `python agent.py "I want to build a digital twin of Amity University's CSE lab"`

## Evidence of explainability
The agent implements Explainable AI (XAI) using a two tiered provenance system to ensure the user always understands the reasoning behind every critique:

1. The system prompt enforces strict citation rules. The LLM is forced to begin every critique with the exact tool citation (e.g., `[SOURCE: LPI/smile-overview]`).
2. Every execution concludes by exposing a hardcoded `PROVENANCE` trace log to the terminal, mapping exactly how the raw data influenced the architectural audit.

**Execution Trace Evidence:**
```text
Auditing Architecture Concept: 'I want to build a digital twin of Amity Universitys CSE lab'

[1/4] Querying LPI: smile-overview...
[2/4] Querying LPI: query-knowledge...
[3/4] Querying LPI: get-case-studies...
[4/4] Querying LPI: smile-phase-detail...

Generating Missing Reality Report via LLM...

MISSING REALITY REPORT
==================================================
[SOURCE: LPI/smile-overview] Critique 1: [Analysis of safety hazards based on SMILE framework guidelines]
[SOURCE: LPI/query-knowledge] Critique 2: [Analysis of manual override constraints]
[SOURCE: LPI/get-case-studies] Critique 3: [Analysis of potential failure metrics]
==================================================

==================================================
PROVENANCE - Every critique traced to its LPI source:
[1] Tool: smile-overview     -> Sourced baseline architectural safety hazards.
[2] Tool: query-knowledge    -> Sourced specific manual override constraints.
[3] Tool: get-case-studies   -> Sourced past failure metrics.
[4] Tool: smile-phase-detail -> Sourced sensor implementation gaps.
==================================================
```

## Security and Error Handling
* Used relative directory referencing (subprocess) to connect directly to the real Node MCP server, completely bypassing WinError 267 path errors without relying on mock APIs.
* Utilizes Regex (re) to sanitize user inputs to prevent commandline parsing errors and injection vulnerabilities.
* Implements try-except blocks to handle Ollama connection downtime gracefully without crashing the pipeline.