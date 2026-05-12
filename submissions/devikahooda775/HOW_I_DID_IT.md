# HOW_I_DID_IT

## Level 2

First, I cloned the LPI Developer Kit repository and installed dependencies using `npm install`. Then I built the project using `npm run build` and verified that all tools were working using `npm run test-client`.

After that, I installed Ollama and ran a local LLM. I explored the SMILE methodology using the LPI tools and generated outputs based on tool responses.

---

## Level 3

For Level 3, I built an AI agent using the provided Python example (`agent.py`) as a starting point. The agent accepts a user question and connects to the LPI MCP server.

It queries multiple tools such as:
- smile_overview
- query_knowledge
- get_case_studies

The agent then processes the results and sends them to a local LLM (Ollama) to generate a final response. The output also includes provenance, clearly showing which tools were used to generate the answer.

I tested the agent with real questions like:
"What is SMILE methodology?" and verified that it produced structured and explainable responses.

---

## Problems I Faced

- Git was not installed on my new laptop initially
- `npm run build` failed due to missing dependencies (`tsc not recognized`)
- Ollama was not installed, which caused connection errors
- File path issues while copying files between folders
- Confusion between `main` and `master` branches while pushing changes

---

## How I Solved Them

- Installed Git and configured username and email
- Ran `npm install` to install missing dependencies
- Installed Ollama and started it using `ollama serve`
- Used correct absolute file paths to copy files between directories
- Checked branch status using `git branch` and pushed changes to the correct branch

---

## What I Learned

- How MCP (Model Context Protocol) works for tool-based AI systems
- How AI agents interact with external tools and combine results
- Importance of explainable AI and showing provenance in outputs
- How to run and use a local LLM using Ollama
- Practical Git workflows including branching, committing, and pushing changes
- Debugging environment setup issues step by step