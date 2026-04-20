# Level 3 Submission — Sonal Yadav

## Track
**Track A:** Agent Builders

## Agent Location
The agent code is in https://github.com/sonalydav789/AI-agent-level-3 in this repository.

**'agent.py'**

## What It Does

**SMILE Compass** — a multi-mode AI agent that connects to the LPI MCP server, intelligently orchestrates multiple tools based on the type of question, and returns explainable answers with full provenance tracking.

### Features

| Feature | Description |
|---------|-------------|
| **4 Agent Modes** | Smart Q&A, Compare, Maturity Scan, and Deep Dive — different reasoning strategies for different question types |
| **All 7 LPI Tools** | Dynamically calls `smile_overview`, `smile_phase_detail`, `query_knowledge`, `get_case_studies`, `get_insights`, `get_methodology_step`, and `list_topics` based on question context |
| **Provenance Tracking** | Every tool result is tagged as `[Source N]`. The LLM cites sources inline. A source table is printed after every answer |
| **Conversation Memory** | Tracks session history, provides context hints to LLM across questions |
| **Interactive CLI** | Supports conversation loops with `/help`, `/tools`, `/modes`, `/history`, `/quit` commands |
| **LLM Synthesis** | Uses Ollama (qwen2.5:1.5b) with mode-specific prompts to synthesize multi-source answers with citations |
| **Fallback Mode** | Works without Ollama by printing structured tool output directly |
| **Robust Error Handling** | Handles server crashes, tool failures, and LLM timeouts gracefully |

### How to Run

```bash
cd lpi-developer-kit
npm run build                            # Compile the LPI server
pip install requests                     # Python dependency
ollama serve                             # Start Ollama (separate terminal)
ollama pull qwen2.5:1.5b                 # Pull the model

python agent/agent.py                    # Interactive mode
python agent/agent.py "Your question"    # Single question mode
```

### Explainability — How the Agent Explains Its Reasoning

The agent does not just return answers — it explains **why** it chose each tool, **what** data came back, and **where** each claim in the answer comes from. Every answer includes:

1. **Tool selection reasoning**: Each tool call shows the reason it was selected
2. **Inline source citations**: The LLM cites `[Source N]` after every claim
3. **Provenance table**: A full audit trail printed after every answer

Here is real output when a user asks **"Why did you recommend this?"** after asking about healthcare digital twins:

```
  You > How do I implement a digital twin for healthcare?

  >> Mode: Smart Q&A
  >> Tools: query_knowledge, get_case_studies, get_insights, smile_overview (4 tools)
  [1/4] query_knowledge({"query": "How do I implement a digital twin for healthcare?"}) -- knowledge base search
  [2/4] get_case_studies({"query": "healthcare"}) -- case studies for healthcare
  [3/4] get_insights({"scenario": "How do I implement a digital twin for healthcare?"}) -- implementation advice
  [4/4] smile_overview({}) -- methodology overview

  >> Synthesizing with qwen2.5:1.5b...

  ============================================================
    ANSWER
  ============================================================

  To implement a healthcare digital twin using the SMILE methodology:

  1. **Start with Impact Definition** — Define the clinical outcome you want to
     improve before collecting any data [Source 1]. The SMILE principle is
     Outcome → Action → Insight → Information → Data [Source 4].

  2. **Build your ontology first** — Healthcare needs domain-specific information
     models (patient, treatment, outcome ontologies) before AI can reason about
     them [Source 1]. This maps to Phase 3 (Collective Intelligence).

  3. **Study existing implementations** — PK/PD modeling for pharmaceutical
     applications shows how digital twins simulate drug interactions in virtual
     patients [Source 2].

  4. **Use edge-native architecture** — Healthcare data often can't leave the
     hospital. An edge-native approach keeps computation close to the data
     source [Source 3].

  Sources Used: [1] query_knowledge, [2] get_case_studies, [3] get_insights,
  [4] smile_overview

  +----------------------------------------------------------+
  |  PROVENANCE -- Tools Queried                              |
  +----------------------------------------------------------+
  |  [1] OK query_knowledge                                   |
  |      args: {"query": "How do I implement a digital..."}   |
  |      why:  knowledge base search                          |
  |      -> 3102 chars returned                               |
  +----------------------------------------------------------+
  |  [2] OK get_case_studies                                  |
  |      args: {"query": "healthcare"}                        |
  |      why:  case studies for healthcare                    |
  |      -> 4521 chars returned                               |
  +----------------------------------------------------------+
  |  [3] OK get_insights                                      |
  |      args: {"scenario": "How do I implement a digi..."}   |
  |      why:  implementation advice                          |
  |      -> 1847 chars returned                               |
  +----------------------------------------------------------+
  |  [4] OK smile_overview                                    |
  |      args: {}                                             |
  |      why:  methodology overview                           |
  |      -> 2341 chars returned                               |
  +----------------------------------------------------------+
```

**Every claim is traceable**: The user can see that "edge-native architecture" came from `get_insights` [Source 3], not hallucinated by the LLM. The "why" field in the provenance table explains the agent's reasoning for querying each tool.

### Example — Compare Mode

```
  You > Compare healthcare and manufacturing digital twins

  >> Mode: Compare
  >> Tools: smile_overview, get_case_studies, get_case_studies, query_knowledge (4 tools)
  [1/4] smile_overview({}) -- baseline methodology context
  [2/4] get_case_studies({"query": "healthcare"}) -- case studies for healthcare
  [3/4] get_case_studies({"query": "manufacturing"}) -- case studies for manufacturing
  [4/4] query_knowledge({"query": "Compare healthcare and manu..."}) -- knowledge base search

  >> Synthesizing with qwen2.5:1.5b...

  ============================================================
    ANSWER
  ============================================================

  Healthcare and manufacturing digital twins share the SMILE foundation but differ
  significantly in implementation [Source 1]...
  [Source 2] Case studies show PK/PD modeling for pharmaceutical applications...
  [Source 3] Manufacturing twins emphasize process optimization and predictive maintenance...

  ============================================================
    PROVENANCE — Tools Queried
  ============================================================
    [1] ✓ smile_overview {}
        → 2341 chars returned
    [2] ✓ get_case_studies {"query": "healthcare"}
        → 4521 chars returned
    [3] ✓ get_case_studies {"query": "manufacturing"}
        → 3892 chars returned
    [4] ✓ query_knowledge {"query": "Compare healthcare and manu..."}
        → 3102 chars returned
  ============================================================
```

### Architecture

```
User Question → Mode Detector (qa / compare / maturity / deep)
→ Tool Planner [(tool, args, reason), ...] (2-6 tools)
→ MCP Server (stdio JSON-RPC) → Provenance Engine (tracks every call with source IDs)
→ Mode-Specific LLM Prompt (Ollama qwen2.5:1.5b) → Structured Answer with Inline Citations
→ Source Table
```

## A2A Agent Card
See [`agent.json`](agent.json) in this directory for the A2A Agent Card describing the agent's capabilities.
