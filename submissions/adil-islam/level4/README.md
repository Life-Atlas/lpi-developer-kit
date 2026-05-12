# Level 4 — Secure Agent Mesh
**Author:** Adil Islam (@adil-islam) | LPI Developer Kit — Track A

---

## What This Builds

Two AI agents that discover each other via A2A, communicate structured data, and together produce a recommendation neither could produce alone.

| Agent | Port | LPI Tools | Role |
|-------|------|-----------|------|
| Agent A — SMILE Specialist | 8001 | `smile_overview`, `query_knowledge` | Orchestrator — analyses problem, delegates to B |
| Agent B — Case Study Analyst | 8002 | `query_knowledge`, `get_insights` | Specialist — retrieves case study evidence |

**Combined output:** SMILE methodology roadmap (Agent A) + supporting case study evidence (Agent B) → structured recommendation neither could produce alone.

---

## Prerequisites

```bash
# 1. Ollama running with the right model
ollama serve                      # keep running in background
ollama pull qwen2.5:0.5b

# 2. LPI MCP server built
cd <repo-root>
npm install
npm run build                     # produces dist/src/index.js

# 3. Python dependencies
cd submissions/adil-islam/level4
python -m venv venv
venv\Scripts\activate             # Windows
# source venv/bin/activate        # Mac/Linux
pip install -r requirements.txt
```

---

## Run the Demo (recommended)

```bash
python run_demo.py
```

This starts both agents automatically, waits for them to be ready, runs the A2A discovery handshake, sends a factory problem query, and prints the full multi-agent transcript. Transcript is saved to `demo_transcript.md`.

---

## Run Agents Manually (two terminals)

```bash
# Terminal 1 — start Agent B FIRST
python agent_b.py

# Terminal 2 — start Agent A
python agent_a.py

# Terminal 3 — send a query
curl -X POST http://localhost:8001/task \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Station 016 is 15% over planned hours. Apply SMILE methodology.\"}"
```

---

## Project Structure

```
level4/
├── agent_a.py          # SMILE Specialist (orchestrator, port 8001)
├── agent_b.py          # Case Study Analyst (specialist, port 8002)
├── mcp_client.py       # Shared MCP stdio client (reusable)
├── security.py         # SecurityGuard — 4 attack surfaces covered
├── run_demo.py         # Starts both agents + runs end-to-end demo
├── .well-known/
│   ├── agent_a.json    # A2A card for Agent A
│   └── agent_b.json    # A2A card for Agent B
├── threat_model.md     # 4 attack surfaces, risk matrix
├── security_audit.md   # Self-test results — what was found and fixed
├── demo_transcript.md  # Generated output from run_demo.py
├── requirements.txt
└── README.md
```

---

## Security

Four attack surfaces addressed — all with working code defenses:

| Attack | Defense |
|--------|---------|
| Prompt injection | 12-pattern regex in `SecurityGuard.sanitize_input()` |
| Data exfiltration | Input filter + `scrub_output()` on every LLM response |
| Denial of service | 600-char input cap, 300-token output cap, 120s timeout |
| Privilege escalation | Per-agent tool allowlist enforced in `MCPClient.call_tool()` |

See `threat_model.md` and `security_audit.md` for full details including 5 bugs found and fixed during self-testing.

---

## A2A Discovery

Agent A discovers Agent B at startup by fetching `http://localhost:8002/.well-known/agent.json`. This follows the Google A2A protocol — Agent A reads Agent B's capabilities before delegating, rather than hardcoding the interface. The cards are at `.well-known/agent_a.json` and `.well-known/agent_b.json`.

---

## What Makes This Multi-Agent (not just two scripts)

- **Structured communication:** Agent A sends `{query, smile_phases, domain}` JSON to Agent B — not plain text
- **A2A discovery:** Agent A reads Agent B's card to confirm capabilities before calling it
- **Divided knowledge:** Agent A is forbidden from calling `get_insights`; Agent B cannot call `smile_overview` — enforced by `SecurityGuard`
- **Unique combined output:** Methodology roadmap (A) + real-world evidence (B) = recommendation neither produces alone
