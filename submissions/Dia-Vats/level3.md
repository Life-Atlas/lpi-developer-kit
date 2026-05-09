# Level 3 Submission : Dia Vats

## Agent Repository
https://github.com/Diavats/LPI-AI-agent

## Agent Description : What it does
The Health SMILE Agent is a personal health digital twin agent that accepts
user health inputs (sleep hours, energy level, steps, main complaint) and
maps them to SMILE methodology insights using the LifeAtlas LPI MCP sandbox.

It queries 4 LPI tools, synthesizes results using a local LLM (qwen2.5:3b
via Ollama), and returns a structured cited health optimization report.
Every claim in the output is traced back to a specific LPI tool — based on
the provenance block printed after each response.

## LPI Tools Used
- `smile_overview` - SMILE methodology foundation and phase structure
- `get_insights` - personalised health digital twin guidance for user scenario
- `query_knowledge` - knowledge base searched using the actual user complaint
- `get_case_studies` - real-world digital twin implementation examples

## Setup Instructions

### Requirements
- Python 3.10+
- Node.js
- Ollama installed locally
- Built LPI sandbox

### Clone and install agent
```bash
git clone https://github.com/Diavats/LPI-AI-agent.git
cd LPI-AI-agent
pip install -r requirements.txt
```

### Pull model and run Ollama
```bash
ollama pull qwen2.5:3b
ollama serve
```

### Clone and build LPI sandbox
```bash
git clone https://github.com/Life-Atlas/lpi-developer-kit
cd lpi-developer-kit
npm install && npm run build
```

### Update path in agent.py
```python
LPI_REPO = r"C:\your\path\to\lpi-developer-kit"
```

### Run
```bash
python agent.py
```

## Explainability
Every section of the output cites which LPI tool it came from using
[Tool 1], [Tool 2], [Tool 3], [Tool 4] inline labels. A full provenance
block at the end lists every tool called with exact arguments used.
No claim is made without a cited source - every statement is based on or from tool outputs only.

## Security and Error Handling
- Input validated before any tool calls (type, range, length checks)
- Injection protection: all inputs sanitized with a 300 character limit
- Error handling: all tool calls wrapped in try/except blocks
- MCP server path verified before subprocess spawn
- Timeout handling for Ollama with graceful error messages
- KeyboardInterrupt caught cleanly

## Sample Interaction
Hours of sleep last night: 6.5
Energy level today (1-10): 7
Steps taken today: 4000
Challenge: I feel tired and lose focus every afternoon after lunch

Output:
[Tool 1] smile_overview (no args)
[Tool 2] get_insights {"scenario": "Person sleeping 6.5 hours, energy 7/10..."}
[Tool 3] query_knowledge {"query": "I feel tired and lose focus after lunch"}
[Tool 4] get_case_studies (no args)

## A2A Agent Card
Included as `agent.json` in the repository root. Describes capabilities,
LPI tools used, security properties, explainability approach, and runtime.

## How I Did It

I chose to focus on personal health optimization rather than a generic
SMILE explainer — mapping real health inputs directly to methodology phases.

I noticed that input validation matters more than expected when user text
goes directly into subprocess calls. I realized the get_insights tool
surprised me with how specifically it mapped health scenarios to SMILE phases.

I thought about using LangChain but decided to learn the MCP JSON-RPC
protocol directly instead — the initialize handshake and tool call structure.

What I'd do differently: dynamic tool routing based on question type,
and streaming LLM output instead of waiting for full response.

## What I learned
Working on this ai agent, I noticed that connecting raw health numbers to SMILE phases required more context than I expected. The get_insights tool surprised me with
how specifically it mapped personal scenarios to methodology phases.
I also realized input validation matters more than I thought when the agent
is the only layer between user text and subprocess calls.