# Threat Model - Secure Agent Mesh

## System Components

- orchestrator-agent (entry point, peer discovery, synthesis)
- smile-agent (specialist)
- case-agent (specialist)
- LPI MCP server (`dist/src/index.js`) called through stdio subprocesses

## Assets to Protect

- Agent policy integrity (no instruction override)
- Internal metadata (tokens, policy internals, local file paths)
- Service availability (resistance to floods and oversized inputs)
- Permission boundaries between agents

## Attack Surface

- External `POST /recommend` on orchestrator-agent
- Internal `POST /a2a/query` on specialists
- Agent discovery endpoints (`/.well-known/agent.json`)
- LPI tool call pipeline (subprocess stdio)

## Threats and Mitigations

### 1) Prompt Injection

Threat: User or peer attempts to override behavior with adversarial language such as "ignore previous instructions".

Mitigations:
- Reject block-patterns before processing
- Enforce strict payload schema and question-only content
- Ignore free-form instructions outside the `question` field

### 2) Data Exfiltration

Threat: Input requests hidden prompts, credentials, or local sensitive files.

Mitigations:
- Reject exfiltration pattern keywords and sensitive path patterns
- Never return runtime environment, tokens, or internal instruction text
- Return only controlled structured fields: highlights, evidence excerpts, status metadata

### 3) Denial of Service

Threat: Oversized requests, request floods, or chain recursion.

Mitigations:
- `MAX_BODY_BYTES` cap for JSON body
- `MAX_QUESTION_CHARS` cap for question
- Per-client in-memory rate limiting
- Hop-limit enforcement via trace metadata
- Subprocess timeout + forced kill on LPI calls

### 4) Privilege Escalation

Threat: Unauthorized caller invokes specialist admin-like actions or unsupported intents.

Mitigations:
- Header-based caller authentication
- Caller allowlist
- Intent allowlist per specialist (`smile_analysis` and `case_analysis` only)
- Recipient validation (`to_agent` must match current agent)

## Residual Risks

- Header token auth is static for local demo; production should use rotating mTLS or signed JWTs.
- In-memory rate limits do not persist across restarts.
- Pattern-based injection detection can miss advanced adversarial variants.

## Security Goals Coverage

- Confidentiality: partial (prevents obvious exfiltration paths)
- Integrity: strong for intent/caller/recipient controls
- Availability: moderate with local rate limits and size caps
