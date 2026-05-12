# Level 3 Submission — Sania Gurung

**Track:** A — Agent Builders
**GitHub repo:** https://github.com/SANIAGRG/lpi-agent-builder

---

## What I Built

**Agent Builder Agent** — a meta-agent that generates customised LPI agents.

Most agents answer questions. This agent's output is another agent.

You describe the digital twin you want to build. The meta-agent makes real MCP
jsonrpc tool calls to the LPI server via subprocess stdio transport, understands
your domain from the response data, and generates a ready-to-run `agent.py`
with the right LPI tool calls pre-filled and every decision cited back to the
LPI tool that produced it.

---

## My Approach — What I Decided and Why

I decided to build a meta-agent because the README describes A2A as agents
discovering and describing each other. I tried a simpler question-answering
design first but chose this architecture because I noticed something the
instructions hint at but don't spell out: the output of an agent can itself
be an agent. That trade-off — more complexity for more conceptual depth — is
one I made deliberately.

I also chose to use only Python stdlib (no external packages) because I tried
adding langchain first and realised it was adding friction without adding value
for what this agent actually needs to do. The MCP stdio transport is simple
enough to implement directly. Smaller is better when it works.

---

## LPI Tools Used — Real Subprocess MCP Calls (5 of 7)

The agent makes real jsonrpc `tools/call` requests to the LPI server via
`subprocess.run(["node", "dist/src/index.js"], ...)` on every run.

| Tool | Why the agent chose it | Data returned |
|------|------------------------|---------------|
| `smile_overview` | Maps the use case to SMILE phases — without this the agent cannot explain which phase to start from | Retrieved full 6-phase methodology |
| `query_knowledge` | Retrieves domain-specific knowledge entries from the 63-entry knowledge base | Retrieved domain-matched entries |
| `get_case_studies` | Finds real industry examples — the agent chose this tool because case study tool traces show how others solved the same problem | Retrieved matched case studies |
| `get_insights` | The agent chose this tool because it explains the reason and implementation path for the specific scenario, not just general advice | Retrieved scenario-specific advice |
| `smile_phase_detail` | Deep-dives the primary SMILE phase for the domain — used to pre-fill the generated agent's tool arguments | Retrieved phase implementation steps |

Every tool call result is stored in the provenance log and cited in the
generated agent as `[SOURCE: LPI/tool_name]`.

---

## Explainability — How the Agent Explains Itself

The agent's explainability works at two levels:

**Level 1 — The builder explains itself:**
After every run, the builder prints a full provenance log:
```
📚 PROVENANCE — Every decision traced to its LPI source
[1] Tool:     LPI/smile_overview
    Args:     {}
    Finding:  Full SMILE — 6 phases, 3 perspectives, AI journey
    Returned: 3847 chars of data from LPI

[2] Tool:     LPI/query_knowledge
    Args:     {"query": "health monitoring ICU patients"}
    Finding:  Domain knowledge for: health monitoring ICU patients
    Returned: 2104 chars of data from LPI
```

**Level 2 — The generated agent explains itself:**
Every section of the generated `agent.py` has a comment that explains the
reason the agent chose that tool:
```python
# [SOURCE: LPI/get_insights] — the agent chose this tool because it explains
# the reason and implementation path for this specific scenario.
r2 = call_lpi_tool("get_insights", {"scenario": f"{user_input} in healthcare"})
```

And the LLM prompt instructs the model to cite sources in every answer:
```
For every claim, cite [SOURCE: LPI/tool_name].
Explain the reason for every recommendation. Do not invent facts.
```

This means the agent's answers are explainable not because of a post-hoc log
but because explainability is baked into the data flow from the start.

---

## How to Run

```bash
# Clone the agent repo
git clone https://github.com/SANIAGRG/lpi-agent-builder.git
cd lpi-agent-builder

# No pip install — stdlib only

# Prerequisites (from lpi-developer-kit/)
npm run build
ollama serve
ollama pull qwen2.5:5b

# Run the builder
python agent_builder_agent.py "health monitoring twin for ICU patients"

# Run your generated agent
python generated_agent_health_monitoring_twin_for_icu_patients.py \
  "What data should I collect first?"
```

---

## What Makes This Different

Most Level 3 submissions will query the LPI and return an answer.
This one queries the LPI and returns an agent. The output is executable,
cited, domain-specific code — not a text response. Every line of the generated
file can be traced back to which LPI tool produced the context that informed it.

That is the A2A concept in practice: agents that describe and produce other agents.

---

## A2A Agent Card

`agent.json` is included in the repo root. It describes the agent's capabilities,
what it accepts, what it produces, which LPI tools it uses, and how its
explainability works — so other agents can discover and invoke it.

Signed-off-by: Sania Gurung <saniagurung5452@gmail.com>