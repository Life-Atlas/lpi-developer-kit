# How I Did It

## Level 2

1. Forked and cloned the lpi-developer-kit repo
2. Ran `npm install` and `npm run build` to set up the project
3. Ran `npm run test-client` — all 8 tests passed (7 tools, one tested twice)
4. Installed Ollama and pulled the qwen3.5:cloud model
5. Ran the example agent (`examples/agent.py`) which connects to the LPI MCP server and feeds results to Ollama
6. Captured all outputs for my submission

### Problems I Hit
- Model mismatch between qwen2.5:1.5b in the examples/agent.py and qwen3.5:cloud model

### What I Learned
- That Ollama runs as a local HTTP API server and the agent just sends POST requests to it
- That the LLM doesn't know about SMILE natively, it only reasons over the context provided

## Level 3

### What I Did
- Studied examples/agent.py to understand how MCP tool calling works (subprocess + JSON-RPC)
- Tried running agent/agent.py first — it crashed because it pointed to a wrong path (../winnio/)
- Ran the official examples/agent.py — got a 404 because no model was pulled
- Pulled qwen2.5:1.5b and got the example agent working
- Created a separate repo (lpi-smile-agent) with an extended agent that calls 4 tools instead of 3
- Added get_insights as a 4th tool for richer context
- Built a class-based LPIConnection to manage the MCP server lifecycle
- Added input sanitization, error handling, and an interactive mode
- Added an A2A Agent Card (agent.json)
- Tested the agent, pushed to GitHub

### Problems I Hit
- qwen3.5:cloud returned 500 errors (cloud-routed model, unreliable) — switched to local qwen2.5:1.5b
- Had to figure out that ollama serve was already running (port binding error)

### What I Learned
- How MCP works (JSON-RPC over stdin/stdout via subprocess)
- The RAG pattern — retrieve data from tools, feed as context to LLM
- How A2A Agent Cards work for agent discovery
