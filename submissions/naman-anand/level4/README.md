# Level 4: Secure Agent Mesh

**Contributor:** Naman Anand  
**Track:** E (QA & Security) + A (Agent Builders)  
**Challenge:** Build a multi-agent system with A2A discovery, real LPI integration, combined knowledge, and security hardening against four attack classes.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Secure Mesh Orchestrator                      │
│                      (secure_mesh.py)                            │
│                                                                  │
│  ┌──────────────────────┐     ┌──────────────────────────────┐  │
│  │  Agent A              │     │  Agent B                      │  │
│  │  SMILE Security       │◄───►│  Infrastructure               │  │
│  │  Auditor              │     │  Architect                    │  │
│  │                       │     │                               │  │
│  │  Tools:               │     │  Tools:                       │  │
│  │  • smile_overview     │     │  • query_knowledge            │  │
│  │  • smile_phase_detail │     │  • get_insights               │  │
│  │  • query_knowledge    │     │  • get_case_studies            │  │
│  └───────────┬───────────┘     └───────────────┬───────────────┘  │
│              │  HMAC-signed JSON envelopes      │                 │
│              └──────────┬──────────────────────┘                 │
│                         │                                        │
│                ┌────────▼────────┐                                │
│                │  SecurityGuard   │                                │
│                │  • Anti-injection│                                │
│                │  • RBAC          │                                │
│                │  • Rate limiter  │                                │
│                │  • Output filter │                                │
│                └────────┬────────┘                                │
└─────────────────────────┼────────────────────────────────────────┘
                          │ JSON-RPC / stdio
                 ┌────────▼────────┐
                 │  LPI MCP Server  │
                 │  (7 read-only    │
                 │   tools)         │
                 └─────────────────┘
```

### Agent Communication Flow

1. **Discovery** — Both agents load each other's `.well-known/agent.json` (A2A protocol)
2. **Structured exchange** — All messages are HMAC-SHA256 signed JSON envelopes
3. **Real LPI calls** — Each agent queries the actual MCP server via subprocess/stdio
4. **Combined output** — Architect's blueprint + Auditor's SMILE compliance check = Hardened Blueprint

---

## Prerequisites

- **Node.js 18+** and **npm**
- **Python 3.10+**
- LPI server built (`npm run build` from repo root)

No additional Python packages needed — uses only the standard library.

---

## How to Run

```bash
# 1. Clone and set up the LPI sandbox (if not already done)
cd lpi-developer-kit
npm install
npm run build

# 2. Run the secure mesh
python naman-anand/secure_mesh.py
```

### Expected Output

The script runs through 5 phases:

| Phase | What Happens |
|-------|-------------|
| **Phase 1** | Connects to the real LPI MCP server via stdio |
| **Phase 2** | Discovers both agents via A2A Agent Cards |
| **Phase 3** | Collaborative workflow — Architect builds blueprint, Auditor audits it |
| **Phase 3b** | Combined "Hardened Digital Twin Blueprint" output |
| **Phase 4** | Security hardening demos (all 4 attack classes) |
| **Provenance** | Full audit trail of every LPI tool call |

### Optional: Custom Mesh Secret

```bash
# Set a custom HMAC secret for production use
set MESH_SECRET=your-production-secret-here
python naman-anand/secure_mesh.py
```

---

## File Structure

```
naman-anand/
├── secure_mesh.py                    # Main orchestrator (all logic)
├── agent_a/
│   └── .well-known/
│       └── agent.json                # A2A Agent Card — SMILE Security Auditor
├── agent_b/
│   └── .well-known/
│       └── agent.json                # A2A Agent Card — Infrastructure Architect
├── README.md                         # This file
├── DEMO.md                           # Full walkthrough with output
├── threat_model.md                   # Security threat model
└── secure_mesh_output.txt            # Captured run output
```

---

## Security Hardening Summary

| Attack Class | Defence | Code Location |
|---|---|---|
| Prompt Injection | 10 regex patterns + control char stripping | `SecurityGuard.sanitize_text()` |
| Privilege Escalation | Per-agent tool allowlists (RBAC) | `SecurityGuard.check_tool_access()` |
| Denial of Service | Payload size limit (4KB) + rate limiter (20 req/10s) | `check_payload_size()` / `check_rate_limit()` |
| Data Exfiltration | Recursive key filtering on sensitive prefixes | `SecurityGuard.filter_output()` |
| **Bonus:** Auth spoofing | HMAC-SHA256 signed envelopes, constant-time comparison | `sign_message()` / `verify_signature()` |

See [threat_model.md](threat_model.md) for the full threat model with attack trees and mitigations.  
See [DEMO.md](DEMO.md) for a complete walkthrough with real output.

---

## LPI Tools Used

| Agent | Tool | Purpose |
|---|---|---|
| Auditor | `smile_overview` | Get full SMILE methodology for compliance baseline |
| Auditor | `smile_phase_detail` | Deep dive into Reality Emulation phase requirements |
| Auditor | `query_knowledge` | Search for security/zero-trust best practices |
| Architect | `query_knowledge` | Search for home network IoT digital twin patterns |
| Architect | `get_insights` | Get scenario-specific implementation advice |
| Architect | `get_case_studies` | Find relevant smart building/IoT case studies |

**Total real LPI calls per run:** 6 (3 per agent)

---

## What Makes This More Than a Single LPI Query

Neither agent alone can produce the final output:

- **Agent B alone** can design a network topology but has no access to SMILE methodology — it cannot verify compliance or apply security principles from the framework.
- **Agent A alone** knows SMILE inside-out but has no access to infrastructure case studies or deployment insights — it cannot design a real architecture.
- **Together** they produce a *Hardened Digital Twin Blueprint* that combines the Architect's network design with the Auditor's SMILE compliance check, security hardening from the knowledge base, and Reality Emulation phase verification.
