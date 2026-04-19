# Level 3 Submission — Sonal Yadav

## Track
**Track A:** Agent Builders

## Agent Location
The agent code is in (https://github.com/sonalydav789/AI-agent-level-3) in this repository.

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

### Example

```
  You > Compare healthcare and manufacturing digital twins

  >> Mode: Compare
  >> Tools: smile_overview, get_case_studies, get_case_studies, query_knowledge (4 tools)
  [1/4] smile_overview({}) -- baseline methodology context
  [2/4] get_case_studies({"query": "healthcare"}) -- case studies for healthcare
  [3/4] get_case_studies({"query": "manufacturing"}) -- case studies for manufacturing
  [4/4] query_knowledge({"query": "Compare healthcare and manu..."}) -- knowledge base search

  🤖 Sending to qwen2.5:1.5b for synthesis...

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
