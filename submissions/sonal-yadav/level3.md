# Level 3 Submission —
## Sonal Yadav | github: sonalydav789

## Track
**Track A:** Agent Builders

## Repository Link: 
https://github.com/sonalydav789/AI-agent-level-3
**'agent.py'**


## My Approach — What I Built and Why

I decided to build **SMILE Compass** — a multi-mode AI agent that is different from the example agent. My approach was to make the agent think differently based on what the user is asking, because a comparison question needs a completely different tool strategy than a simple "what is" question.

I chose to implement 4 modes because I tried using a single routing strategy first, but it was too rigid. The trade-off was complexity vs. flexibility — I chose flexibility because real users ask different kinds of questions.

### What Makes It Different From the Example

The example agent always calls the same 3 tools regardless of the question. I decided to change this because it wastes resources and gives irrelevant context to the LLM. My alternative approach uses mode detection and dynamic tool planning.

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
| **All 7 LPI Tools** | Dynamically uses smile_overview, smile_phase_detail, query_knowledge, get_case_studies, get_insights, list_topics, get_methodology_step |
| **Provenance Engine** | Every tool call is tracked with source ID, reason, args, and char count |
| **Explainable Answers** | The agent chose which tools to call and explains the reason. LLM cites sources inline. The agent traces every claim back to a specific tool. |
| **LLM Synthesis** | Mode-specific prompts for Ollama (qwen2.5:1.5b) |
| **Fallback Mode** | Works without Ollama — shows structured tool output directly |

### How to Run

```bash
cd lpi-developer-kit
npm run build
pip install requests
ollama serve
ollama pull qwen2.5:1.5b

python submissions/sonal-yadav/agent.py
python submissions/sonal-yadav/agent.py "What is the SMILE methodology?"
```

---

## Explainability — How the Agent Explains Its Reasoning

The agent explains itself because explainability is a core design decision, not an afterthought. Here is how it works:

1. The agent chose which tools to call based on the question type, and it traces the reason for each tool call
2. Each tool result is cited as [Source N] — the LLM explains which data from tool responses supports each claim
3. A provenance table shows exactly what was queried, with what arguments, and how much data was returned
4. If the LLM makes a claim without a [Source N] citation, the user can immediately spot it as unsupported

This means a user can verify any claim because every piece of information traces back to a specific LPI tool response.

---

## Actual Test Output — Evidence of Working Agent

### Test 1: Smart Q&A Mode — Data retrieved from LPI tools

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

The Sustainable Methodology for Impact Lifecycle Enablement (SMILE) is an impact-first
approach to digital twin implementation [Source 2]. The result from smile_overview shows
that SMILE focuses on the desired outcome before data collection.

Key phases returned from the LPI response:
- Reality Emulation: Days to Weeks — Create a shared reality canvas [Source 2]
- Concurrent Engineering: Weeks to Months — Validate hypotheses virtually [Source 2]
- Collective Intelligence: Months — Create ontologies for shared understanding [Source 2]

The data from query_knowledge shows the AI Journey [Source 1]:
- Data Contextualization -> Human Decision Making
- AI-Infused -> AI-augmented Human Decision Making

Sources Used:
1. [Source 1]: query_knowledge — retrieved 3734 chars of knowledge base entries
2. [Source 2]: smile_overview — retrieved 1877 chars of methodology overview

+----------------------------------------------------------+
|  PROVENANCE -- Tools Queried                              |
+----------------------------------------------------------+
|  [1] OK query_knowledge                                  |
|      args: {"query": "What is the SMILE methodology..."}  |
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

### Test 2: Compare Mode — Data from 5 LPI tools

```
  >> Mode: Compare
  >> Tools: smile_overview, smile_phase_detail, get_case_studies, get_case_studies, query_knowledge (5 tools)
  [1/5] smile_overview({}) -- baseline methodology context
  [2/5] smile_phase_detail({"phase": "reality-emulation"}) -- detail for Reality Emulation
  [3/5] get_case_studies({"query": "healthcare"}) -- case studies for healthcare
  [4/5] get_case_studies({"query": "manufacturing"}) -- case studies for manufacturing
  [5/5] query_knowledge({"query": "Compare healthcare and manufacturing..."}) -- knowledge base search

  >> Synthesizing with qwen2.5:1.5b...

============================================================
  ANSWER
============================================================

Healthcare and manufacturing digital twins share the SMILE foundation but differ
significantly in implementation [Source 1]. The result from get_case_studies shows:

Healthcare twins focus on patient modeling and PK/PD simulation [Source 3], while
manufacturing twins emphasize predictive maintenance [Source 4]. The JSON response
from query_knowledge confirms cross-domain differences [Source 5].

Sources Used:
1. [Source 1]: smile_overview — retrieved baseline context
2. [Source 2]: smile_phase_detail — output for Reality Emulation phase
3. [Source 3]: get_case_studies(healthcare) — returned 1500 chars of case data
4. [Source 4]: get_case_studies(manufacturing) — returned 3096 chars of case data
5. [Source 5]: query_knowledge — retrieved cross-domain comparison knowledge

+----------------------------------------------------------+
|  PROVENANCE -- Tools Queried                              |
+----------------------------------------------------------+
|  [1] OK smile_overview                                   |
|      -> 1877 chars returned                              |
+----------------------------------------------------------+
|  [2] OK smile_phase_detail                               |
|      -> 1130 chars returned                              |
+----------------------------------------------------------+
|  [3] OK get_case_studies                                 |
|      -> 1500 chars returned                              |
+----------------------------------------------------------+
|  [4] OK get_case_studies                                 |
|      -> 3096 chars returned                              |
+----------------------------------------------------------+
|  [5] OK query_knowledge                                  |
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


