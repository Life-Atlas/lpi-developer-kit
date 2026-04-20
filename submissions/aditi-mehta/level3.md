# Level 3 Submission - Aditi Mehta

**Repository:** https://github.com/Dynamic-ctrl/lpi-smile-agent

**Agent Code:** https://github.com/Dynamic-ctrl/lpi-smile-agent/blob/main/agent.py

**A2A Card:** https://github.com/Dynamic-ctrl/lpi-smile-agent/blob/main/agent.json

---

## Overview
This project implements a Level 3 agent using the Life Programmable Interface (LPI). Instead of a basic chatbot, I built the **SMILE Gap Analyzer (The Critic Agent)**. It acts as a Senior Architect that audits a user's digital twin concept against the SMILE framework to find physical, human, and architectural blind spots. 

---

## Evaluation Questions Answered

**What choices did you make that weren't in the instructions? What would you do differently next time?**

The most critical choice I made outside the standard instructions was engineering a **Stateless IPC Bridge** and a **Regex Security Layer**.

Initially, I observed that standard persistent `stdio` streams for MCP connections were highly prone to `BrokenPipeError` and terminal freezing. Knowing that an AI agent must be reliable, I built a custom bridge using `subprocess.communicate()`. This isolates every tool call into a fresh process, trading slight overhead for a hard security boundary against state-injection and complete operational stability. Furthermore, I proactively implemented a regex sanitization layer to block command injections *before* terminal input ever reaches the LLM.

If I were to rebuild this for production, the current implementation of spinning up the Node.js MCP server as a Python subprocess per execution is resource-heavy. Next time, I would decouple the architecture by containerizing the LPI tools in a standalone **Docker container** and exposing them over a persistent local network port. I would also rebuild the IPC bridge using `asyncio` to allow the agent to fire off multiple LPI tool calls simultaneously to drastically reduce latency.

---

## Design Decisions & Independent Thinking

**My Approach & Tool Selection Trade-offs:**
Instead of relying on basic LLM reasoning, I prioritized absolute data integrity.
* **Trade-off:** I sacrificed the simplicity of standard prompting to implement **Few-Shot Template Forcing**. This strictly enforces a Provenance Logging protocol, preventing the LLM from hallucinating citations and guaranteeing that every critique is tied directly to retrieved LPI data.

**Enterprise Deployment & Reproducibility:**
To ensure zero-friction reproducibility, I have structured my repository with production-grade deployment protocols:
* **Deterministic Execution:** The architecture isolates the LPI server execution from the Python agent logic, ensuring the agent executes identically across all local environments without pathing conflicts.

---

## Explainability Evidence
Explainability is deeply integrated into the LLM's response. The agent doesn't just give advice; it provides inline provenance to trace its logic back to the tools.

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
