# Level 3 Submission v2 - Track A (Includes Levels 1 & 2)

### Repository Link
Since I developed my AI agent inside a separate local folder (`lpi-level3-agent`), I will be pushing it to the following GitHub repository:

**Agent Repo:** [Track A Agent Repo - temporalzone](https://github.com/temporalzone/lpi-level3-agent)

### Description
### Description
My agent communicates directly with the LPI MCP server to synthesize information regarding digital twin construction using `query_knowledge` and `smile_phase_detail`. It prints clear provenance citing the exact sources it retrieved knowledge from and features LLM processing using local `qwen2.5:1.5b` (with fallback raw parsing) for explainable AI. I've also included the `agent.json` indicating my agent's A2A discovery card. As an added measure of **Initiative** and **Growth Velocity**, I built a fully responsive premium Glassmorphic web User Interface that connects to the `agent.py` logic wrapper—proving readiness to ship production user-facing pipelines!

**Error Handling & Bad Inputs:** If a bad input is provided or if the `Ollama` system experiences an error/timeout, the agent catches the exception gracefully. Instead of crashing, it prevents a generic failure and safely routes the raw synthesized context to the UI, guaranteeing an outcome. The Flask server also handles empty inputs returning `400 Bad Request` safely.
