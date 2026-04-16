# Level 3 Submission - Aditi Mehta

### Agent Repository Linked
**URL:** https://github.com/Dynamic-ctrl/lpi-smile-agent

### Agent Description
I chose to build this using raw Python rather than a heavy framework because I wanted to see how the MCP communication actually works under the hood. I used the `subprocess` module to set up a direct bridge to the Node MCP server via `stdio`. The agent takes a project idea, pulls context from the LPI tools, and then feeds that raw data into a local Ollama model (`qwen2.5:1.5b`) to build out a plan. I also included an `agent.json` card to handle the A2A requirement.

### LPI Tools Referenced
1. `smile_overview`
2. `get_insights`

### Setup Instructions
You'll need Ollama (running `qwen2.5:1.5b`) and the LPI MCP Server built and ready.

1. **Clone it:** `git clone https://github.com/Dynamic-ctrl/lpi-smile-agent`
2. **Install deps:** `pip install -r requirements.txt`
3. **Run a query:** `python agent.py "Create a smart hospital"`

### Explainability Evidence
To keep the AI from being a "black box," I added a strict rule in the system prompt that forces the model to act as a citation engine. It has to explicitly tag where its information is coming from (like printing `[Source: smile_overview]`) before it gives an answer. This way, you can actually trace the advice back to the specific tool that provided the data.

### Security Awareness
Since the agent takes arguments directly from the terminal, I added a regex-based sanitization layer. It scrubs the input for any weird characters and caps the string length. This helps block basic prompt injection or terminal exploits before the data ever touches the LLM or the backend subprocess.