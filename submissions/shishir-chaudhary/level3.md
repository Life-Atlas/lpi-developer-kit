# Level 3 Submission — Shishir Chaudhary

## Track
**Track A:** Agent Builders

## Agent Location
The agent code is in (https://github.com/Shishir-DS28/lpi-level3-agent) in this repository.

**'agent.py'**

## What It Does

**SMILE Digital Twin Advisor** — an intelligent AI agent that connects to the LPI MCP server, dynamically selects relevant tools based on user questions, and returns explainable answers with full provenance tracking.

### Features

| Feature | Description |
|---------|-------------|
| **Intelligent Routing** | Classifies questions and picks 2-5 relevant LPI tools instead of always querying the same ones |
| **4+ LPI Tools** | Dynamically calls `smile_overview`, `smile_phase_detail`, `query_knowledge`, `get_case_studies`, `get_insights`, `get_methodology_step`, and `list_topics` based on question context |
| **Provenance Tracking** | Every tool result is tagged as `[Source N]`. The LLM cites sources inline. A source table is printed after every answer |
| **Interactive CLI** | Supports conversation loops with `/help`, `/tools`, `/quit` commands |
| **LLM Synthesis** | Uses Ollama (qwen2.5:1.5b) to synthesize multi-source answers with citations |
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
  You > How do I implement a digital twin for healthcare?

  📋 Tool plan: get_case_studies, query_knowledge, get_insights (3 tools)
  [1/3] Querying get_case_studies({"query": "healthcare"})...
  [2/3] Querying query_knowledge({"query": "How do I implement a digital twin for healthcare?"})...
  [3/3] Querying get_insights({"scenario": "How do I implement a digital twin for healthcare?"})...

  🤖 Sending to qwen2.5:1.5b for synthesis...

  ============================================================
    ANSWER
  ============================================================

  Healthcare digital twins can be implemented using the SMILE methodology...
  [Source 1] Case studies show PK/PD modeling for pharmaceutical applications...
  [Source 2] The knowledge base emphasizes starting with impact definition...
  [Source 3] Implementation insights recommend an edge-native architecture...

  ============================================================
    PROVENANCE — Tools Queried
  ============================================================
    [1] ✓ get_case_studies {"query": "healthcare"}
        → 4521 chars returned
    [2] ✓ query_knowledge {"query": "How do I implement..."}
        → 3102 chars returned
    [3] ✓ get_insights {"scenario": "How do I implement..."}
        → 1847 chars returned
  ============================================================
```

### Architecture

```
User Question → Question Classifier → Dynamic Tool Selection (2-5 tools)
→ MCP Server (stdio JSON-RPC) → Provenance-Tagged Context
→ Ollama LLM (qwen2.5:1.5b) → Structured Answer with Inline Citations
→ Source Table
```

## A2A Agent Card
See [`agent.json`](agent.json) in this directory for the A2A Agent Card describing the agent's capabilities.
