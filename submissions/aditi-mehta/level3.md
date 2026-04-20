# Level 3 Submission - Aditi Mehta

**Repository:** https://github.com/Dynamic-ctrl/lpi-smile-agent
**Agent Code:** https://github.com/Dynamic-ctrl/lpi-smile-agent/blob/main/agent.py
**A2A Card:** https://github.com/Dynamic-ctrl/lpi-smile-agent/blob/main/agent.json

---

## Overview
This project implements a Level 3 agent using the Life Programmable Interface (LPI). Instead of a basic chatbot, I built the **SMILE Gap Analyzer (The Critic Agent)**. It acts as a Senior Architect that audits a user's digital twin concept against the SMILE framework to find physical, human, and architectural blind spots. 

## Tools Used
* `smile_overview` — Audits high-level architecture phases.
* `query_knowledge` — Retrieves domain-specific constraints.
* `get_case_studies` — Finds real-world failure risks and metrics.
* `smile_phase_detail` — Deep-dives into implementation gaps.

---

## How It Works
1. Accepts a user's digital twin concept via terminal.
2. Sanitizes input using a regex-based security layer.
3. Selects relevant SMILE framework tools based on the query.
4. Executes a stateless IPC bridge (`subprocess.communicate()`) to query the LPI MCP Server.
5. Retrieves historical data and architectural constraints.
6. Uses an LLM (Qwen via Ollama) with Few-Shot Template Forcing to generate a structured, explainable critique.

---

## Design Decisions & Independent Thinking

### What choices did I make that weren't in the instructions?
I made three major architectural choices that went beyond the base requirements:

1. **Stateless IPC Bridge over Persistent Streams:** I chose to build this in raw Python. Instead of relying on standard persistent `stdio` streams for the MCP connection, I engineered a stateless IPC bridge using `subprocess.communicate()`. I noticed persistent streams were prone to `BrokenPipeError` and terminal freezing. By making each tool call a fresh process, I traded slight overhead for complete stability and a hard security boundary against state-injection.
2. **Regex Security Layer:** I implemented a regex-based sanitization layer that cleans the terminal input for special characters and command injections *before* the data ever goes to the LLM or the MCP server.
3. **Strict Provenance Logging:** The instructions asked for explainability, but I implemented "Few-Shot Template Forcing." The agent doesn't just explain its reasoning; it prints a strict Provenance Log tracing every single critique back to the specific LPI tool it fired, actively preventing hallucinated citations.

---

## Reflection

### What would I do differently next time?
* **Structured Data Validation (Pydantic):** Right now, the Provenance Log relies on prompt engineering to format correctly. Next time, I would implement strict structured data validation (like Pydantic) to force the LLM to output its critique and tool-citations as a validated JSON object, rather than raw text. This would make it much easier to parse the agent's output in a larger microservice architecture.
* **Asynchronous Tool Execution:** My current stateless bridge runs synchronously, querying one tool after another. Next time, I would rebuild the IPC bridge using `asyncio` to allow the agent to fire off multiple LPI tool calls (e.g., querying `smile_overview` and `get_case_studies` simultaneously) to drastically reduce the agent's overall response latency.

---

## Explainability Evidence
Explainability is a core requirement of this agent. It doesn't just give advice; it explains the "Why" behind every recommendation.

**Example Query:**
`python3 agent.py "I want to build a digital twin of a smart grid"`

**Actual Agent Output Evidence:**
> `[SOURCE: LPI/get_case_studies] Critique: You must implement a dedicated backup power supply for your sensors.`
> `Why I recommend this: According to the case studies tool, historical data shows that power outages frequently lead to sensor calibration loss. This evidence-based recommendation mitigates a specific real-world failure risk.`

**Provenance Log Output:**
```text
PROVENANCE - Every critique traced to its LPI source:
[1] Tool: smile_overview     -> Sourced baseline safety hazards.
[2] Tool: query_knowledge    -> Sourced manual override constraints.
[3] Tool: get_case_studies   -> Sourced past failure metrics.
[4] Tool: smile_phase_detail -> Sourced sensor implementation gaps.
```

### Setup Instructions
You'll need Ollama (running `qwen2.5:1.5b`) and the LPI MCP Server built and ready.

1. **Clone it:** `git clone https://github.com/Dynamic-ctrl/lpi-smile-agent`
2. **Setup Path:** Update `LPI_SERVER_PATH` in `agent.py` to point to your local `index.js`.
3. **Run a query:** `python3 agent.py "I want to build a digital twin of a smart grid"`

### Security Awareness
I implemented a **regex-based sanitization layer** that sanitizes the terminal input for special characters and command injections before the data ever goes to the LLM or the MCP server. Additionally, **stateless subprocess bridge** provides a security boundary; because each tool call is a fresh process, it prevents memory leaks or state-injection attacks that can stop persistent `stdio` streams.

