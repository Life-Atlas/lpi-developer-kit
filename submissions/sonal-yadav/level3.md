# Level 3 Submission — Sonal Yadav

## Track
**Track A:** Agent Builders

## GitHub Repository
**https://github.com/sonalydav789/lpi-developer-kit**

Agent code: [`submissions/sonal-yadav/agent.py`](https://github.com/sonalydav789/lpi-developer-kit/blob/master/submissions/sonal-yadav/agent.py)

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
| **Explainable Answers** | LLM cites [Source N] inline; provenance table shows exactly which tools provided which data |
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

---

## Explainability — How the Agent Cites Its Sources

The agent is designed to be **fully explainable**. Every answer traces back to specific LPI tools:

1. **Each tool call gets a Source ID** — `[Source 1]`, `[Source 2]`, etc.
2. **Each source includes a reason** — why the agent chose to query that specific tool
3. **The LLM is prompted to cite `[Source N]`** inline after every claim
4. **A provenance table** is printed after every answer showing tool name, arguments, reason, and data volume

This means a user can **verify any claim** by checking which source it came from and what data that tool returned. If the LLM makes something up, it won't have a `[Source N]` citation — making hallucinations easy to spot.

---

## Actual Test Output — Evidence of Working Agent

### Test 1: Smart Q&A Mode — "What is the SMILE methodology?"

```
  [*] Starting LPI MCP server...
  [OK] Connected to LPI MCP server
  [*] Checking Ollama LLM...
  [OK] Ollama ready (qwen2.5:1.5b)

============================================================
  SMILE Compass v2.0.0
  Question: What is the SMILE methodology and how does it work?
============================================================

  >> Mode: Smart Q&A
  >> Tools: query_knowledge, smile_overview (2 tools)
  [1/2] query_knowledge({"query": "What is the SMILE methodology and how does it work?"}) -- knowledge base search
  [2/2] smile_overview({}) -- methodology overview

  >> Synthesizing with qwen2.5:1.5b...

============================================================
  ANSWER
============================================================

### SMILE Methodology Overview

The Sustainable Methodology for Impact Lifecycle Enablement (SMILE) is an impact-first
approach to digital twin implementation that focuses on the desired outcome before data
collection. This methodology ensures investment aligns with value creation, reducing
unnecessary data collection and focusing on impactful activities.

#### Key Components of SMILE:

1. **Impact Sequence**:
   - Outcome/Impact -> Action -> Insight -> Information -> Data

2. **Phases**:
   - **Reality Emulation**: Days to Weeks — Create a shared reality canvas. [Source 2]
   - **Concurrent Engineering**: Weeks to Months — Define scope, innovate together,
     validate hypotheses virtually before committing resources. [Source 2]
   - **Collective Intelligence**: Months — Connect physical sensors, meet initial KPIs,
     create ontologies for shared understanding. [Source 2]
   - **Contextual Intelligence**: Months to Years — Connected everything, real-time
     decisions, predictive analytics, root cause analysis. [Source 2]
   - **Continuous Intelligence**: Years — Prescriptive maintenance, AI-driven
     prognostics, universal event pipelines. [Source 2]
   - **Perpetual Wisdom** (Years+) — Share impact across the planet. [Source 2]

3. **AI Journey**: [Source 1]
   - Data Contextualization -> Human Decision Making
   - AI-Ready -> Human Decision Making with AI support
   - AI-Infused -> AI-augmented Human Decision Making
   - AI-Ingrained -> Autonomous AI with Human oversight

### Sources Used
1. [Source 1]: query_knowledge — Knowledge base entries on SMILE methodology
2. [Source 2]: smile_overview — Full methodology overview with phases and principles

+----------------------------------------------------------+
|  PROVENANCE -- Tools Queried                              |
+----------------------------------------------------------+
|  [1] OK query_knowledge                                  |
|      args: {"query": "What is the SMILE methodology and h|
|      why:  knowledge base search                         |
|      -> 3734 chars returned                              |
+----------------------------------------------------------+
|  [2] OK smile_overview                                   |
|      args: {}                                            |
|      why:  methodology overview                          |
|      -> 1877 chars returned                              |
+----------------------------------------------------------+
  [*] Disconnected from LPI server.
```

### Test 2: Compare Mode — "Compare healthcare and manufacturing digital twins"

```
  >> Mode: Compare
  >> Tools: smile_overview, smile_phase_detail, get_case_studies, get_case_studies, query_knowledge (5 tools)
  [1/5] smile_overview({}) -- baseline methodology context
  [2/5] smile_phase_detail({"phase": "reality-emulation"}) -- detail for Reality Emulation
  [3/5] get_case_studies({"query": "healthcare"}) -- case studies for healthcare
  [4/5] get_case_studies({"query": "manufacturing"}) -- case studies for manufacturing
  [5/5] query_knowledge({"query": "Compare healthcare and manufacturing digital twins"}) -- knowledge base search

  >> Synthesizing with qwen2.5:1.5b...

============================================================
  ANSWER
============================================================

### Comparison of Healthcare and Manufacturing Digital Twins

Healthcare and manufacturing digital twins share the SMILE foundation but differ
significantly in implementation [Source 1]...

Healthcare twins focus on patient modeling and PK/PD simulation [Source 3], while
manufacturing twins emphasize process optimization and predictive maintenance [Source 4].

Both require the Reality Emulation phase to map their ecosystem first [Source 2],
but healthcare involves more regulatory and privacy concerns [Source 5].

### Sources Used
1. [Source 1]: smile_overview — baseline SMILE context
2. [Source 2]: smile_phase_detail — Reality Emulation phase details
3. [Source 3]: get_case_studies(healthcare) — healthcare case studies
4. [Source 4]: get_case_studies(manufacturing) — manufacturing case studies
5. [Source 5]: query_knowledge — cross-domain comparison knowledge

+----------------------------------------------------------+
|  PROVENANCE -- Tools Queried                              |
+----------------------------------------------------------+
|  [1] OK smile_overview                                   |
|      args: {}                                            |
|      why:  baseline methodology context                  |
|      -> 1877 chars returned                              |
+----------------------------------------------------------+
|  [2] OK smile_phase_detail                               |
|      args: {"phase": "reality-emulation"}                |
|      why:  detail for Reality Emulation                  |
|      -> 1130 chars returned                              |
+----------------------------------------------------------+
|  [3] OK get_case_studies                                 |
|      args: {"query": "healthcare"}                       |
|      why:  case studies for healthcare                   |
|      -> 1500 chars returned                              |
+----------------------------------------------------------+
|  [4] OK get_case_studies                                 |
|      args: {"query": "manufacturing"}                    |
|      why:  case studies for manufacturing                |
|      -> 3096 chars returned                              |
+----------------------------------------------------------+
|  [5] OK query_knowledge                                  |
|      args: {"query": "Compare healthcare and manufactur..|
|      why:  knowledge base search                         |
|      -> 2382 chars returned                              |
+----------------------------------------------------------+
```

---

## Architecture

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
