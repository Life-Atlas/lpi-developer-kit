# Level 3 Submission — Track A: Agent Builders

## Project
Life Twin Insight Agent

## Repository
https://github.com/Shourya3113/life-twin-insight-agent

## What it does
The Life Twin Insight Agent converts sleep, focus, energy, and habit-loop questions
into SMILE-based personal digital twin optimization reports.

It queries 3 LPI MCP tools, then synthesizes the results using a local LLM
(qwen2.5:1.5b via Ollama) to produce a grounded, cited answer specific to the user's question.

## LPI Tools Used
- smile_overview — SMILE methodology foundation
- get_insights — personal health digital twin guidance
- query_knowledge — dynamically searched using the actual user question

## LLM
- Model: qwen2.5:1.5b
- Runtime: Ollama (local, no API key, runs on M4 Pro)
- Role: synthesizes tool outputs into structured answer with SMILE phase mapping

## Example Usage
    python3 agent.py "Why do I crash every afternoon?"

Output includes: direct answer, SMILE phase mapping, actionable recommendations,
surprising insight from knowledge base, full tool provenance.

## Key Design Decisions
- Query routing: query_knowledge uses the actual user question, not a hardcoded string
- Path detection: auto-resolves repo root relative to script (portable across machines)
- No external dependencies — uses stdlib urllib for Ollama calls
- Explainability: every answer section traced to a specific LPI tool

## A2A Agent Card
Included as agent.json — describes capabilities, tools used, and example inputs.

## What I built beyond the instructions

I skipped LangChain and CrewAI even though they were suggested. I wanted to
understand the MCP protocol directly — the JSON-RPC handshake, initialize
sequence, tool call structure — before abstracting it away. If I can't explain
what a library does underneath, I don't trust it in production.

I dropped the requests dependency entirely and used stdlib urllib instead.
This was forced by macOS pip restrictions on campus WiFi, but turned out to
be the right call — fewer dependencies, fewer failure points.

I focused the agent on personal health optimization rather than a generic
SMILE explainer. My Level 1 my_twin answer was about tracking afternoon
energy crashes — so I built the agent to actually answer that question.

## What I'd do differently

Make tool selection dynamic — right now it always calls the same 3 tools
regardless of the question. A smarter agent would route to different tools
based on what the question is actually about. I'd also add streaming so
the LLM response appears token by token, and a multi-turn loop so the
agent can ask clarifying questions before querying tools.