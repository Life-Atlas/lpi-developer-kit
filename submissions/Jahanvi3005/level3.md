# Level 3 Submission - Agent Builders

**My Agent Repository:** [https://github.com/Jahanvi3005/winnio](https://github.com/Jahanvi3005/winnio)

### Agent Capabilities
My LPI Explorer Agent is built in Python to programmatically interface with the LPI Sandbox via the Model Context Protocol (MCP). The agent accepts a user query and robustly pipes it via `subprocess.Popen` to the Node.js MCP server using `stdio`. 

It calls the following LPI Context Tools:
1. `query_knowledge` (to harvest unstructured terminology explanations)
2. `smile_overview` (to pull the foundational methodology framework)

### Explainable AI & Security Routing
The agent incorporates explicit Explainable AI (XAI) provenance tracking. After synthesizing the text, the agent forcibly logs exactly which tools were invoked along with the exact input arguments parsed at execution time. 
From a security context, it includes `try/except` guardrails, timeout configurations (`proc.wait(timeout=5)`), and string-size input sanitization to prevent pipeline crashes. Includes a standardized `.well-known/agent.json` Agent Card declaring its capabilities.

### Setup & Run
Instructions to install and run the code are provided natively inside the agent repository's `README.md`.
