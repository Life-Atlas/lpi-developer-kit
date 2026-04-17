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
