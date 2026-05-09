# Secure Agent Mesh

A minimal multi-agent system built in Python.

The setup is straightforward: one agent (Agent A) takes a query, sends it to two
specialized agents, and combines their responses into a single output.

The goal here is not to overcomplicate things, but to show how agents can
communicate over HTTP with some basic security in place.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  Agent A  (Orchestrator · CLI)          │
│  • Discovers agents via /.well-known/   │
│  • Sends query to both agents           │
│  • Combines responses                  │
└───────────────┬─────────────┬───────────┘
                │             │
    ┌───────────▼──┐   ┌──────▼──────────────┐
    │  Agent B     │   │  Case Agent          │
    │  port 8001   │   │  port 8002           │
    │  SMILE + LPI │   │  simple examples     │
    │  via Ollama  │   │  (keyword-based)     │
    └──────────────┘   └──────────────────────┘
```

### Roles

* **Agent A** → orchestrates and combines results
* **Agent B** → performs SMILE/LPI analysis (via Ollama)
* **Case Agent** → returns relevant real-world examples

---

## Prerequisites

* Python 3.11+
* [Ollama](https://ollama.com) (only required for Agent B)
* Pull model:

  ```
  ollama pull llama3.2
  ```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. (Optional) Set shared token

```bash
export AGENT_TOKEN="mesh-secret-token-2024"
```

All agents must use the same token.

---

### 3. Start Agent B

```bash
python agent_b.py
```

Runs on: http://localhost:8001

---

### 4. Start Case Agent

```bash
python case_agent.py
```

Runs on: http://localhost:8002

---

### 5. Run Agent A

```bash
python agent_a.py "your query here"
```

or interactive mode:

```bash
python agent_a.py
```

---

## Example Flow

Input:

```
How do prompt injection attacks affect AI agents?
```

What happens:

* Agent A discovers both agents
* Sends the query to both
* Agent B analyzes intent and structure
* Case Agent returns related examples
* Agent A combines everything into one response

---

## API Overview

### Agent B — `/analyze`

```json
{ "query": "your question here" }
```

Returns structured SMILE + LPI analysis.

---

### Case Agent — `/cases`

```json
{ "query": "your question here" }
```

Returns a few matching real-world examples.

---

### Discovery — `/.well-known/agent.json`

Both agents expose this endpoint for discovery.

---

## Security (kept simple)

* Bearer token authentication
* Input validation (length + cleanup)
* Basic injection filtering (pattern-based)
* Rate limiting (per IP)
* Output filtering (allowlist)

All implemented in `security.py`.

---

## File Structure

```
agent_mesh/
├── agent_a.py          # Orchestrator (run this)
├── agent_b.py          # SMILE analysis server
├── case_agent.py       # Real-world examples server
├── security.py         # Shared security utilities
├── requirements.txt
├── .well-known/
│   ├── agent_b.json    # Agent B discovery card (reference copy)
│   └── case_agent.json # Case Agent discovery card (reference copy)
├── README.md
├── demo.md
├── threat_model.md
└── security_audit.md
```

---

## Notes

* If Ollama is not running, Agent B falls back to a simple rule-based response
* The system still works, just with less detailed analysis
