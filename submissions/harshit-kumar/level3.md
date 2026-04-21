# Level 3 Submission — Track A: Agent Builders
## Harshit Kumar | GitHub: hrk0503

---

## Agent: LPI FinTech Insight Agent

A Python-based AI agent that connects to the Life Programmable Interface (LPI) MCP server and answers questions about applying the SMILE methodology to fintech and personal digital twin use cases — specifically around trading behavior and decision-making patterns.

### What the Agent Does

1. Accepts a user question as input (e.g., "How do I build a personal finance digital twin using SMILE?")
2. Queries **at least 2 LPI tools** to gather relevant knowledge:
   - `smile_overview` — retrieves the full 6-phase SMILE methodology
   - `query_knowledge` — searches the 63-entry knowledge base for relevant entries
   - Optionally: `get_insights` for scenario-specific implementation advice
3. Processes and combines the results
4. Returns an explainable answer that **cites which LPI tool provided which information**

### Why Fintech / Personal Trading Twin

From my contributor profile (`my_twin` field): I want to track the correlation between my deep-focus coding sessions and the quality of my stock market trade decisions. This agent is the first step — it queries the LPI to understand how SMILE phases map to building that kind of personal behavioral digital twin.

---

## Agent Repository / Code Location

The agent code is in this fork at:
**`agent/agent.py`** → https://github.com/hrk0503/lpi-developer-kit/blob/master/agent/agent.py

### Key Design Decisions

- **Raw Python + subprocess** — same pattern as `examples/agent.py`, no extra framework dependencies
- **Provenance tracking** — every part of the output is labeled with which LPI tool produced it
- **Minimum 2 tools queried** — `smile_overview` + `query_knowledge` are always called; `get_insights` is called conditionally
- **No LLM required** — the agent produces a structured, explainable answer directly from LPI tool outputs (LLM integration is optional/additive)

### Input Validation and Security

The agent includes input validation and security measures:

- **Input sanitization**: user queries are stripped and limited to 100 characters to prevent injection attacks and excessively long inputs
- **Type validation**: arguments to MCP tools are validated as proper `dict` objects before sending — raises `ValueError` for invalid types
- **Error handling**: all MCP communication is wrapped in `try/except Exception` blocks — connection failures return descriptive `[FATAL]` error messages rather than crashing
- **Timeout handling**: the MCP subprocess is terminated with a 5-second timeout limit via `proc.wait(timeout=5)` to prevent hanging
- **Security**: no sensitive data is logged; error messages are sanitized before output
- **Empty query guard**: if the user provides an empty or whitespace-only input after stripping, the agent exits cleanly with an error message

### How to Run

```
# Prerequisites: Node.js 18+, npm, Python 3.8+
git clone https://github.com/hrk0503/lpi-developer-kit.git
cd lpi-developer-kit
npm install
npm run build
python agent/agent.py "How do I build a personal finance digital twin using SMILE?"
```

### Sample Output

```
[Tool: smile_overview] SMILE has 6 phases: Reality Emulation, Concurrent Engineering,
Collective Intelligence, Contextual Intelligence, Continuous Intelligence, Perpetual Wisdom.

[Tool: query_knowledge (query: "fintech behavioral patterns")]
Found 3 relevant entries:
 - Financial decision tracking under SMILE Collective Intelligence phase
 - Behavioral pattern modeling for personal digital twins
 - Real-time data streams for contextual adaptation

Answer (citing sources above):
To build a personal finance digital twin using SMILE, start with Reality Emulation
(smile_overview Phase 1) to capture your current trading state — your portfolio,
historical trades, session logs. Then apply Collective Intelligence (smile_overview Phase 3)
to continuously gather data: trade timestamps, session duration, focus metrics.
The query_knowledge results show that behavioral pattern modeling is key to correlating
cognitive state with decision quality.

SOURCES (Provenance tracking embedded):
[1] LPI Tool Called: query_knowledge (Args: {"query": "fintech behavioral patterns"})
[2] LPI Tool Called: smile_overview (Args: {})
```

### LPI Tools Used

| Tool | Purpose | Required |
|------|---------|----------|
| `smile_overview` | Get full SMILE methodology framework | Yes |
| `query_knowledge` | Search knowledge base for domain-specific entries | Yes |
| `get_insights` | Get scenario-specific implementation advice | Optional |

### HOW_I_DID_IT.md

Full documentation of my process, problems hit, and what I learned:
→ [HOW_I_DID_IT.md](./HOW_I_DID_IT.md)

### Track & Level

- **Track:** A — Agent Builders
- **Level:** 3 (Retry v2)
- **Submission PR title:** level-3: Harshit Kumar
