# Secure Agent Mesh — Level 4 Submission
# Harshit Kumar (hrk0503)

A secure multi-agent system implementing A2A protocol discovery with MCP integration and comprehensive security hardening.

## System Architecture

- **Agent A (Client)**: Handles user input, discovers Agent B via A2A, routes queries
- **Agent B (Server)**: Specializes in SMILE methodology, queries LPI tools, returns structured responses
- **Security Layer**: Prompt injection protection, rate limiting, input validation, output sanitization

## Files

- `agent_a.py` — Client agent with A2A discovery and security validation
- `agent_b.py` — Server agent with MCP/LPI integration
- `.well-known/agent.json` — A2A Agent Cards for both agents
- `threat_model.md` — Threat analysis and attack surface documentation
- `security_audit.md` — Self-audit results and fixes implemented
- `demo.md` — Working demonstration transcript

## How to Run

### Prerequisites
- Python 3.10+, Flask, requests
- Node.js 18+ (for LPI MCP server)
- Ollama with qwen2.5:1.5b

### Steps
1. `pip install flask requests`
2. `ollama serve && ollama pull qwen2.5:1.5b`
3. Start Agent B: `python agent_b.py`
4. Start Agent A: `python agent_a.py`

## Security Features

- Prompt injection pattern detection and blocking
- Rate limiting (10 req/min per client)
- Input length limits and character sanitization
- Output field whitelisting to prevent data leakage
- Request timeout to prevent DoS
