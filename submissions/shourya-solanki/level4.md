# Level 4 Submission — Shourya Solanki

## Project
SMILE Agent Mesh — Secure Two-Agent System

## Repository
https://github.com/Shourya3113/smile-agent-mesh

## What I Built
Two AI agents that discover each other via A2A, communicate over HTTP,
and together produce recommendations neither could generate alone.

- Agent A (SMILE Strategist) — orchestrates, queries smile_overview and smile_phase_detail
- Agent B (Industry Analyst) — FastAPI server, queries get_case_studies, get_insights, query_knowledge

Combined output synthesized by local LLM (qwen2.5:1.5b via Ollama).

## A2A Discovery
Agent A fetches Agent B's card at GET /.well-known/agent.json before querying.
Both agents publish valid A2A Agent Cards describing their capabilities.

## Security Hardening
- Prompt injection detection — 13 patterns on both agents independently
- Zero trust — Agent B sanitizes inputs even from Agent A
- 500 character input limit
- LPI subprocess terminated after every request
- Graceful failure handling
- Self-audit found and fixed 4 issues (see SECURITY_AUDIT.md in repo)

## Scoring Criteria Met
- Agents discover each other via A2A Agent Cards
- Structured JSON exchange between agents
- Combined output adds value beyond single agent
- Threat model covers prompt injection, DoS, exfiltration, privilege escalation
- Self-audit with real findings and fixes
- Working code with clear setup instructions