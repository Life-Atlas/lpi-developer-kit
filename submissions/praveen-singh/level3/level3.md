# Level 3 Submission — Praveen Singh
## Project: Explainable Knowledge Agent (LPI)
**Repository:** https://github.com/praveen-singh-007/lpi-life-agent

---

## Description

An explainable AI agent that answers user queries by combining **general methodology overview (smile_overview)**, **targeted knowledge base search (query_knowledge)**, and **research-level case studies (get_case_studies)**.

The tool names mirror the LPI MCP reference implementation exactly. The system ensures that every response is:
- **grounded** in real retrieved data
- **synthesized** across three distinct sources
- **fully traceable** (Explainable AI requirement)

---

## Key Features

- **Three-Source Retrieval:** Uses three LPI tools matching MCP reference names
  - `smile_overview` → general overview and methodology background
  - `query_knowledge` → targeted search using the user's exact question
  - `get_case_studies` → research papers and real-world application examples
- **Explainable AI:**
  - Explicit PROVENANCE block included in every run
  - Every part of the answer is mapped back to a named tool
- **Structured Output:**
  - Combined Answer with per-tool source citations
  - Sources section (tool name + what it contributed)
  - PROVENANCE block (tool name + arguments used)
- **Deterministic Pipeline:**
  Tools are explicitly called in sequence (not left to LLM randomness)
- **MCP-Compatible Structure:**
  Tool names, `tools_used` list, and terminal output format mirror the reference `agent.py` exactly

---

## Explainability (Provenance)

The system provides explicit traceability for every answer:

- **smile_overview** → provides definition and general methodology context
- **query_knowledge** → provides targeted knowledge base result for the specific question
- **get_case_studies** → provides research papers with titles, authors, URLs, and summaries

This ensures every part of the answer can be traced back to its source tool and the arguments it was called with.

---

## LPI Tools Used

1. **smile_overview** (via WikipediaQueryRun)
   - Provides general knowledge, definitions, and methodology overview

2. **query_knowledge** (via WikipediaQueryRun with exact question)
   - Provides targeted knowledge base result using the user's question directly

3. **get_case_studies** (via Arxiv Python SDK)
   - Provides research papers (title, authors, summary, URL)

---

## Technical Architecture

- **Language:** Python 3
- **LLM:** HuggingFace (`meta-llama/Llama-3.2-1B-Instruct`)
- **Framework:** LangChain
- **Data Sources:**
  - Wikipedia API (Tools 1 & 2)
  - Arxiv API (Tool 3)

---

## Agent Pipeline

```
User Query (sys.argv[1])
↓
smile_overview    (general overview)
↓
query_knowledge   (targeted knowledge base search)
↓
get_case_studies  (research papers / case studies)
↓
LLM (Llama via HuggingFace) synthesis
↓
Structured Answer + Sources + PROVENANCE
```

---

## Example Usage

```bash
python agents.py "What are the phases of SMILE and how do I start?"
```

---

## Sample Output (Simplified)

```
============================================================
  LPI Agent — Question: What are the phases of SMILE and how do I start?
============================================================
[1/3] Querying SMILE overview...
[2/3] Searching knowledge base...
[3/3] Checking case studies...

Sending to LLM (HuggingFace)...

============================================================
  ANSWER
============================================================
The SMILE methodology consists of phases designed to guide digital twin creation.
[Tool 1: smile_overview] provided the phase definitions and general context.
[Tool 2: query_knowledge] explained how to start and practical first steps.
[Tool 3: get_case_studies] supported the answer with real-world application examples.

Sources:
  - [Tool 1: smile_overview] — General overview and methodology background
  - [Tool 2: query_knowledge] — Targeted knowledge base result for the question
  - [Tool 3: get_case_studies] — Research papers with real-world applications

============================================================
  PROVENANCE (tools used)
============================================================
  [1] smile_overview {}
  [2] query_knowledge {"query": "What are the phases of SMILE and how do I start?"}
  [3] get_case_studies {}
```

---

## What Makes This Correct for Level 3

- ✅ Uses 3 real tools (exceeds the 2-tool minimum requirement)
- ✅ Tool names match the LPI MCP reference (`smile_overview`, `query_knowledge`, `get_case_studies`)
- ✅ All tools registered as `langchain.tools.Tool` objects with explicit `name=` fields
- ✅ Performs actual synthesis across all three sources, not raw output passthrough
- ✅ Provides traceable explanations via Sources + PROVENANCE in every run
- ✅ Shows clear mapping between sources and answer
- ✅ Full error handling — try/except on every tool call and LLM call

---

## Files in Repository

- `agents.py` — main implementation with all three tool definitions and pipeline
- `README.md` — documentation and setup
- `HOW_I_DID_IT.md` — design decisions, challenges, improvements
- `requirements.txt` — dependencies

---

## Testing Results

**Tested with:**
`"What are the phases of SMILE and how do I start?"`

---

**Results:**
- `smile_overview` data retrieved successfully from Wikipedia
- `query_knowledge` targeted result retrieved successfully from Wikipedia
- `get_case_studies` Arxiv papers retrieved (titles, authors, summaries, URLs)
- LLM synthesized all three sources into a structured, cited answer
- Output remained structured and fully traceable via PROVENANCE block
