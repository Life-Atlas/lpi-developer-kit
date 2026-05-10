# Level 3 Submission — Adil Islam (Track A)

## Agent Repository
https://github.com/Adilislam0/lpi-smile-agent

## Files in Repository

| File | Description |
|------|-------------|
| `agent.py` | Main agent — MCP client, Ollama integration, teaching prompt |
| `README.md` | This file |
| `HOW_I_DID_IT.md` | Development process, bugs hit, lessons learned |
| `requirements.txt` | Python dependencies (`requests`) |


## Description

An explainable AI agent that acts as a personal learning coach for the SMILE 
methodology. Instead of giving generic query responses, it teaches — breaking 
down concepts, grounding every answer in LPI knowledge, and prompting the user 
to think deeper with follow-up questions.

Built on the insight that retrieval alone isn't learning. The agent combines 
LPI tool retrieval with a structured teaching format: Answer → Follow-Up → Sources.

---

## Key Features

- **Teaching-First Design:** Responds like a coach, not a search engine where
  every answer ends with a follow-up question to deepen understanding
- **Explainable AI:** Every claim cites exactly which LPI tool provided
  which insight with no black-box outputs
- **Structured Output:** Consistent ANSWER / FOLLOW-UP / SOURCES format
  across all question types
- **Robust Error Handling:** Graceful fallbacks if MCP server or Ollama
  fail, agent reports the error clearly instead of hanging
- **Memory-Safe:** Context trimmed to 1200 chars per tool and 300 token
  output cap to prevents small model overload and infinite generation



## LPI Tools Used
| Tool               | Purpose                                              |
|--------------------|------------------------------------------------------|
| `smile_overview`   | Full SMILE methodology context as base knowledge     |
| `query_knowledge`  | Semantic search - it finds relevant knowledge entries|
| `get_case_studies` | Real-world implementations across industries         |

## How to Run
```bash
# Prerequisites
pip install requests
ollama pull qwen2.5:0.5b         #version 1.5 was not supported to device config (CPU-safe, no GPU required)
ollama serve              # keep running in background
cd lpi-developer-kit && npm run build

# Run agent
python agent.py "What SMILE phases apply to healthcare digital twins?"
```
## Sample Output
The agent prints:
1. Step-by-step tool queries with progress indicators
2. LLM-generated answer grounded in LPI data
3. PROVENANCE section listing every tool called and its arguments


============================================================
  LPI Agent — Question: What SMILE phases apply to healthcare digital twins?
============================================================

[1/3] Querying SMILE overview...
[2/3] Searching knowledge base...
[3/3] Checking case studies...

Sending to LLM (Ollama)...


============================================================
  ANSWER
============================================================

The SMILE phases that apply to healthcare digital twins are:

1. **Reality Emulation** (Days to Weeks)
   - Create a shared reality canvas â€” establishing where, when, and who.

2. **Concurrent Engineering** (Weeks to Months)
   - Define the scope (as-is to to-be), invite stakeholders to innovate together, validate hypotheses virtually before committing resources.

3. **Collective Intelligence** (Months)
   - Connect physical sensors, meet initial KPIs, create ontologies for shared understanding.

4. **Contextual Intelligence** (Months to Years)
   - Connected everything â€” command & control, real-time decisions, uptime optimization, predictive analytics, root cause analysis.

5. **Continuous Intelligence** (Years)
   - Leverage accumulated knowledge â€” prescriptive maintenance, AI-driven prognostics, universal event pipelines.

6. **Perpetual Wisdom** (Perpetual (decades+))
   - Share impact across the planet.

Sources:
- Tool 1: smile_overview
- Tool 2: query_knowledge("What SMILE phases apply to healthcare digital twins?")
- Tool 3: get_case_studies

============================================================
  PROVENANCE (tools used)
============================================================
  [1] smile_overview (no args)
  [2] query_knowledge {"query": "What SMILE phases apply to healthcare digital twins?"}
  [3] get_case_studies (no args)


## What Makes This Unique

- **Applies SMILE to learning itself** - the agent doesn't just retrieve
  SMILE knowledge, it uses SMILE's feedback-loop philosophy to teach it
- **Follow-up questions built into every response** - forces active recall,
  not passive reading
- **Provenance block is separate from the answer** - reviewers and users can
  verify every claim independently without it cluttering the response
- **Engineered for low-resource hardware** - works on CPU-only machines with
  0.5b model, no GPU required

## Architecture
User question → MCP subprocess → 3 LPI tools → Ollama prompt (with context)
→ Cited answer + provenance log