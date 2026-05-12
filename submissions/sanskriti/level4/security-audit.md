# Security Audit Report - Secure Agent Mesh

## Audit Method

I executed `security_audit.py` to run adversarial tests directly against live endpoints.

## Tests Executed

1. Safe baseline request (should succeed)
2. Prompt injection payload (should be blocked)
3. Data exfiltration payload (should be blocked)
4. Oversized request for DoS pressure (should be blocked)
5. Privilege escalation with forbidden intent (should be blocked)
6. Hop-limit bypass attempt (should be blocked)

## Findings and Fixes

### Finding A: Specialists originally accepted any intent string

Risk:
- A caller could request actions outside specialist responsibilities.

Fix implemented:
- Added strict intent allowlist in `specialist_agent.py`.
- `smile-agent` only accepts `smile_analysis`.
- `case-agent` only accepts `case_analysis`.
- Invalid intents return HTTP 403 with structured error payload.

### Finding B: Missing caller identity validation would allow rogue peer calls

Risk:
- Any process could call specialist APIs and impersonate orchestrator behavior.

Fix implemented:
- Added `X-Agent-Id` + `X-Agent-Token` verification.
- Added caller allowlist using `auth_ok` in shared policy module.

### Finding C: Trace metadata could be abused for recursive chains

Risk:
- Excessive hop counts can lead to chaining loops or orchestration abuse.

Fix implemented:
- Added strict `validate_trace` policy with bounded `MAX_HOPS`.
- Requests exceeding hop constraints are rejected.

### Finding D: Oversized payload handling needed explicit rejection

Risk:
- Large requests can degrade service responsiveness.

Fix implemented:
- Added body-size cap (`MAX_BODY_BYTES`) and question-length cap (`MAX_QUESTION_CHARS`).
- Requests beyond limits are rejected before expensive work.

## Audit Outcome

Expected outcome after fixes:
- Baseline request succeeds.
- All attack simulations return explicit errors and no sensitive leakage.

See `demo-transcript.md` for sample output details captured from execution.
