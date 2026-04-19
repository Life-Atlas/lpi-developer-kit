# How I Built My Level 3 Agent

## What I Did (Step-by-Step)
1. **Created a dedicated Agent Repository**: I set up this separate `smile-ai-agent` repository to isolate my agent's codebase from the core LPI platform.
2. **Environment Setup**: I initialized a local Python environment and installed the `requests` library to handle API communication. I also started my local `qwen2.5:1.5b` model via Ollama in the background.
3. **Agent Integration**: I utilized the base `agent.py` example but modified the `_REPO_ROOT` configuration to use the absolute path to my local LPI developer kit clone. This ensured the agent could correctly spawn the Node.js MCP server process as a subprocess.
4. **Testing**: I successfully ran the agent with the prompt "What is the SMILE methodology?" and verified that it correctly queried the `smile_overview`, `query_knowledge`, and `get_case_studies` tools, passing the context to the LLM and returning a response with full provenance.

## Problems Encountered & Solutions
* **Pathing Issue**: Initially, the agent script failed to locate the `dist/src/index.js` file because the relative path `..` was no longer valid after moving the agent to its own repository. I solved this by explicitly hardcoding the absolute path (`C:\Users\Singh\Desktop\lpi-work\lpi-developer-kit`) into the `_REPO_ROOT` variable.

## What I Learned
I learned the mechanics of the Model Context Protocol (MCP) and how a Python script can spin up a Node.js server as a background subprocess, communicate with it via JSON-RPC over `stdio`, and then feed that structured data into a local LLM to generate grounded, explainable answers.
