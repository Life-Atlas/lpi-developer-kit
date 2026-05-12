# Level 4 Submission: Secure Agent Mesh

This submission implements a hardened 3-agent mesh:

- orchestrator-agent: discovers peers via A2A agent cards and composes final recommendation
- smile-agent: SMILE methodology specialist
- case-agent: case-study specialist

The system is intentionally structured to meet all Level 4 criteria:

- A2A discovery through `/.well-known/agent.json`
- Strict JSON request and response schemas for A2A exchange
- Cross-agent value synthesis (methodology + case evidence)
- Defenses for prompt injection, data exfiltration, DoS, and privilege escalation

## Folder Contents

- `orchestrator_agent.py` - coordination and synthesis service
- `specialist_agent.py` - shared specialist server implementation
- `lpi_client.py` - MCP stdio client for LPI tool calls
- `mesh_common.py` - shared protocol validation and security policy enforcement
- `agent_cards/` - A2A cards for all agents
- `demo.py` - runnable end-to-end demo script
- `security_audit.py` - adversarial self-audit script
- `threat-model.md` - attack surface and mitigations
- `security-audit.md` - vulnerabilities found and fixes
- `demo-transcript.md` - sample run transcript

## Run Instructions

From repository root:

```bash
npm install
npm run build
python3 submissions/sanskriti/level4/demo.py
python3 submissions/sanskriti/level4/security_audit.py
```

## API Summary

### Public endpoint

- `POST /recommend` on orchestrator (`127.0.0.1:8100`)

Request:

```json
{
  "request_id": "demo-request-001",
  "question": "How should a manufacturing team start a digital twin rollout with low risk?"
}
```

### Inter-agent endpoint

- `POST /a2a/query` on each specialist (`127.0.0.1:8101` and `127.0.0.1:8102`)

Request envelope:

```json
{
  "request_id": "uuid",
  "from_agent": "orchestrator-agent",
  "to_agent": "smile-agent",
  "intent": "smile_analysis",
  "payload": { "question": "..." },
  "trace": { "hop_count": 1, "max_hops": 3 }
}
```

## Security Hardening Implemented

- Prompt injection filtering via block-pattern detection and strict question sanitization
- Data exfiltration prevention via deny patterns and no exposure of internal prompts/config
- DoS protection via payload size limits, rate limiting, question length limits, hop limits, and process timeouts
- Privilege escalation prevention through:
  - caller authentication (`X-Agent-Id`, `X-Agent-Token`)
  - intent allowlists per specialist
  - recipient validation (`to_agent` must match receiving agent)

## Notes

- The implementation is deterministic and does not rely on external LLM APIs.
- Evidence is returned as structured JSON excerpts from LPI tool outputs.
