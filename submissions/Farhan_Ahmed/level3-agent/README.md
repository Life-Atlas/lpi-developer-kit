# SMILE Digital Twin Advisor — Level 3 Agent

**Author:** Farhan Ahmed Siddique | [Farhan-Ahmed-code](https://github.com/Farhan-Ahmed-code)  
**Track:** A — Agent Builders  
**Model:** `qwen2.5:1.5b` via Ollama (local, no cloud API)

---

## What It Does

An AI agent that:
1. Accepts a natural language question about digital twins / SMILE
2. Queries **4 LPI MCP tools** to gather relevant knowledge
3. Passes the combined context to a local LLM (Ollama)
4. Returns an answer with **full provenance** — every answer cites which tool provided what

### LPI Tools Used
| # | Tool | Purpose |
|---|------|---------|
| 1 | `smile_overview` | Full SMILE methodology backbone |
| 2 | `smile_phase_detail` | Deep dive into Phase 1: Reality Emulation |
| 3 | `query_knowledge` | Semantic search on the user's question |
| 4 | `get_case_studies` | Real-world grounding across industries |

---

## Setup

```bash
# 1. Build LPI server (from repo root)
npm run build

# 2. Install Python dep
pip install requests

# 3. Start Ollama (separate terminal)
ollama serve
ollama pull qwen2.5:1.5b
```

## Usage

```bash
# Single question
python agent.py "What is Phase 1 of SMILE and how do I start?"

# Interactive multi-turn mode
python agent.py --interactive
```

## Example Output

```
────────────────────────────────────────────────────────────
  Question: What is Phase 1 of SMILE?
────────────────────────────────────────────────────────────
  Gathering context from LPI tools...
  → [1/4] smile_overview()
  → [2/4] smile_phase_detail({"phase": "reality-emulation"})
  → [3/4] query_knowledge({"query": "What is Phase 1 of SMILE?"})
  → [4/4] get_case_studies()
  Reasoning with LLM...

============================================================
  ANSWER
============================================================

Phase 1 of SMILE is Reality Emulation — the process of creating
a digital replica of a physical system by capturing its structure,
behaviour, and environment...

Sources:
[Tool 1: smile_overview] — Provided the 6-phase SMILE structure
[Tool 2: smile_phase_detail] — Deep detail on Reality Emulation activities
[Tool 3: query_knowledge] — Returned specific KB entries on Phase 1
[Tool 4: get_case_studies] — Grounded answer in real hospital/manufacturing examples
```

---

## Design Decisions

- **4 tools instead of 2**: Richer context = better, more grounded answers
- **Local LLM only**: No API keys, no cost, fully reproducible
- **Provenance-first**: Every call logs tool name, args, and chars retrieved
- **Interactive mode**: Supports multi-turn Q&A without restarting
