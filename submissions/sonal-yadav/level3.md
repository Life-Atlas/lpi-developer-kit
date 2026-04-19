# Level 3 Submission — Sonal Yadav

## Track
**Track A:** Agent Builders

## Agent Location
The agent code is located at [`submissions/sonal-yadav/agent.py`](agent.py) in this repository.

## What It Does

**SMILE Compass** — a multi-mode AI agent that connects to the LPI MCP server, intelligently orchestrates multiple tools based on the type of question, and returns explainable answers with full provenance tracking.

### What Makes It Different

Unlike the example agent (which always calls the same 3 tools), SMILE Compass has **4 distinct modes** that change how it approaches each question:

| Mode | Trigger Words | What It Does |
|------|--------------|--------------|
| **Smart Q&A** | (default) | Routes to 2-4 relevant tools based on question content |
| **Compare** | "compare", "vs", "difference" | Gathers data from multiple tools for side-by-side analysis |
| **Maturity Scan** | "assess", "maturity", "readiness" | Maps the user's current state against SMILE phases |
| **Deep Dive** | "deep dive", "comprehensive" | Exhaustive analysis pulling from 4-6+ tools |

### Key Features

| Feature | Description |
|---------|-------------|
| **4 Agent Modes** | Different reasoning strategies for different question types |
| **Conversation Memory** | Tracks session history, provides context hints to LLM |
| **Smart Tool Routing** | Phase detection, industry detection, and intent-based routing |
| **All 7 LPI Tools** | Dynamically uses `smile_overview`, `smile_phase_detail`, `query_knowledge`, `get_case_studies`, `get_insights`, `list_topics`, `get_methodology_step` |
| **Provenance Engine** | Every tool call is tracked with source ID, reason, args, and char count |
| **LLM Synthesis** | Mode-specific prompts for Ollama (qwen2.5:1.5b) |
| **Fallback Mode** | Works without Ollama — shows structured tool output directly |
| **Interactive CLI** | `/help`, `/tools`, `/modes`, `/history`, `/quit` commands |

### How to Run

```bash
cd lpi-developer-kit
npm run build                            # Compile the LPI server
pip install requests                     # Python dependency
ollama serve                             # Start Ollama (separate terminal)
ollama pull qwen2.5:1.5b                 # Pull the model

# Interactive mode
python submissions/sonal-yadav/agent.py

# Single question mode
python submissions/sonal-yadav/agent.py "What is the SMILE methodology?"
```

### Example Session

```
  You > Compare healthcare and manufacturing digital twins

  >> Mode: Compare
  >> Tools: smile_overview, get_case_studies, get_case_studies, query_knowledge (4 tools)
  [1/4] smile_overview({}) -- baseline methodology context
  [2/4] get_case_studies({"query": "healthcare"}) -- case studies for healthcare
  [3/4] get_case_studies({"query": "manufacturing"}) -- case studies for manufacturing
  [4/4] query_knowledge({"query": "Compare healthcare and manufacturing..."}) -- knowledge base search

  >> Synthesizing with qwen2.5:1.5b...

  ============================================================
    ANSWER
  ============================================================

  Healthcare and manufacturing digital twins share the SMILE foundation but differ
  significantly in implementation [Source 1]...

  Healthcare twins focus on patient modeling and PK/PD simulation [Source 2], while
  manufacturing twins emphasize process optimization and predictive maintenance [Source 3]...

  +----------------------------------------------------------+
  |  PROVENANCE -- Tools Queried                              |
  +----------------------------------------------------------+
  |  [1] OK smile_overview                                    |
  |      args: {}                                             |
  |      why:  baseline methodology context                   |
  |      -> 2341 chars returned                               |
  +----------------------------------------------------------+
  |  [2] OK get_case_studies                                  |
  |      args: {"query": "healthcare"}                        |
  |      why:  case studies for healthcare                    |
  |      -> 4521 chars returned                               |
  +----------------------------------------------------------+
  |  [3] OK get_case_studies                                  |
  |      args: {"query": "manufacturing"}                     |
  |      why:  case studies for manufacturing                 |
  |      -> 3892 chars returned                               |
  +----------------------------------------------------------+
  |  [4] OK query_knowledge                                   |
  |      args: {"query": "Compare healthcare and manu..."}    |
  |      why:  knowledge base search                          |
  |      -> 3102 chars returned                               |
  +----------------------------------------------------------+
```

### Architecture

```
User Question
    |
    v
Mode Detector --> qa / compare / maturity / deep
    |
    v
Tool Planner --> [(tool, args, reason), ...]  (2-6 tools)
    |
    v
MCP Server (stdio JSON-RPC subprocess)
    |
    v
Provenance Engine --> tracks every call with source IDs
    |
    v
Mode-Specific LLM Prompt (Ollama qwen2.5:1.5b)
    |
    v
Structured Answer with [Source N] citations + Provenance Table
```

## A2A Agent Card
See [`agent.json`](agent.json) for the A2A Agent Card (bonus).
