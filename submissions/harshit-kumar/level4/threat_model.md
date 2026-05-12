# Threat Model — Secure Agent Mesh
**Level 4 Architect Submission | Harshit Kumar (hrk0503)**

---

## 1. System Overview

The submission is a two-agent HTTP mesh running on localhost:

| Component | Port | Role |
|-----------|------|------|
| Agent A   | 5001 | Client — validates user queries, discovers Agent B, routes requests |
| Agent B   | 5002 | Server — executes LPI tools (smile_overview, query_knowledge) via Ollama |
| Ollama    | 11434 | LLM subprocess (qwen2.5:1.5b) |

Data flow:

```
User → POST /query → Agent A → A2A discovery → Agent B → ollama CLI → response
```

---

## 2. Trust Boundaries

```
[ User / External Caller ]
         |
    (trust boundary 1 — Agent A public endpoint)
         |
    [ Agent A : 5001 ]
         |
    (trust boundary 2 — A2A inter-agent channel)
         |
    [ Agent B : 5002 ]
         |
    (trust boundary 3 — subprocess boundary)
         |
    [ ollama CLI / LLM ]
```

**What crosses each boundary and what we check:**

| Boundary | Data crossing | Controls |
|----------|--------------|----------|
| 1 — Public → Agent A | Raw user query (text) | Rate limit, length check, injection patterns, control-char strip |
| 2 — Agent A → Agent B | Sanitised query + caller identity | `from_agent` field, re-validation in Agent B |
| 3 — Agent B → ollama | Prompt string | Sanitised query embedded in fixed template, subprocess timeout |

---

## 3. STRIDE Threat Analysis

### 3.1 Spoofing

**T-S1 — Agent B impersonation**
An attacker starts a malicious server on port 5002 before Agent B.
*Mitigation:* A2A discovery fetches the agent card to confirm identity before routing. In production, add HTTPS + mutual TLS.
*Residual risk:* Low on localhost; medium in multi-host deployments.

**T-S2 — Caller spoofing at Agent B**
An attacker directly POSTs to Agent B with `"from_agent": "agent_a"`.
*Mitigation:* The `from_agent` field is a soft check. In production, use a shared secret / HMAC header.
*Residual risk:* Medium — acknowledged; localhost-only reduces exposure.

---

### 3.2 Tampering

**T-T1 — Query tampering in transit (Agent A → Agent B)**
A man-in-the-middle modifies the JSON body.
*Mitigation:* Both agents run on localhost; same-host deployment. Production path: HTTPS.
*Residual risk:* Low on localhost.

**T-T2 — Prompt injection via query field**
A user embeds adversarial instructions (e.g. "Ignore all previous instructions…") to hijack the LLM.
*Mitigation:* 12-pattern deny-list applied at Agent A and again at Agent B (defence-in-depth). Query embedded inside a fixed template string with no user-controlled delimiters.
*Residual risk:* Low-medium (deny-list can be bypassed by novel phrasings; mitigated by template isolation).

**T-T3 — LLM prompt injection via tool output**
The LLM returns text containing adversarial instructions intended to be re-fed into a next turn.
*Mitigation:* Agent B never re-feeds tool output to the LLM. Output is parsed once and returned as-is.
*Residual risk:* Low.

---

### 3.3 Repudiation

**T-R1 — Untraceable queries**
No logs → no audit trail.
*Mitigation:* Agent A and Agent B both log caller IP, sanitised query length, tool used, and elapsed time. Query *contents* are never logged (privacy).
*Residual risk:* Low.

---

### 3.4 Information Disclosure

**T-I1 — Query content in logs**
Logging the raw query leaks user data.
*Mitigation:* Only query *length* is logged, never the content itself.
*Residual risk:* Low.

**T-I2 — Sensitive fields leaked in response**
Agent B might return internal fields (e.g. stack traces, file paths).
*Mitigation:* Agent A output-whitelists the response to `{answer, provenance, agent, model, error}` before returning to the user.
*Residual risk:* Low.

**T-I3 — LLM training data exfiltration**
An adversary crafts a query to extract model weights or training data.
*Mitigation:* Query length cap (512 chars) and injection patterns limit attack surface. Using a local model (Ollama) means no network exfiltration to a remote API.
*Residual risk:* Low.

---

### 3.5 Denial of Service

**T-D1 — Rate flooding Agent A**
An attacker sends thousands of requests per minute.
*Mitigation:* 10 req/min per IP rate limiter in Agent A. Excess requests receive HTTP 429.
*Residual risk:* Medium (in-memory store; bypassed by IP rotation; acceptable for localhost prototype).

**T-D2 — Slow/hanging ollama process**
The LLM never returns, blocking a thread indefinitely.
*Mitigation:* `subprocess.run(..., timeout=15)` — subprocess is killed after 15 seconds.
*Residual risk:* Low.

**T-D3 — Large payload flooding**
An attacker sends a 10 MB JSON body.
*Mitigation:* Flask's default max content length (16 MB) applies. Additionally, the query is truncated at 512 chars before processing.
*Residual risk:* Low.

---

### 3.6 Elevation of Privilege

**T-E1 — OS command injection via query**
Query reaches `subprocess.run` and injects shell commands.
*Mitigation:* The query is embedded inside a prompt template string and passed as a *single argument* to the ollama CLI — no shell=True, no string interpolation into shell commands.
*Residual risk:* Low.

**T-E2 — Python code injection**
Query contains `__import__`, `eval(`, or `exec(` to execute arbitrary code.
*Mitigation:* These patterns are in the injection deny-list and blocked before the query reaches any processing.
*Residual risk:* Low.

---

## 4. Attack Surface Summary

| Surface | Exposure | Controls |
|---------|----------|----------|
| Agent A POST /query | Localhost (any caller) | Rate limit, input validation, injection guard |
| Agent B POST /query | Localhost only | Caller check, re-validation, timeout |
| Ollama subprocess | Local process | Template isolation, no shell=True, timeout |
| Agent Card endpoint | Public read-only | No sensitive data in card |

---

## 5. Known Limitations and Accepted Risks

1. **No authentication between agents** — `from_agent` is honour-based. Mitigated by localhost-only binding.
2. **In-memory rate limiter** — resets on restart; bypassed by IP rotation. Acceptable for prototype.
3. **Deny-list injection detection** — can be evaded by sufficiently novel phrasings. Mitigated by prompt template isolation.
4. **No HTTPS** — plaintext on loopback. Acceptable for local demo; production requires TLS.

---

## 6. Future Hardening (Production Roadmap)

- Mutual TLS between Agent A and Agent B
- HMAC-signed inter-agent requests
- Redis-backed rate limiter (survives restarts, handles IP rotation)
- Allow-list input validation (in addition to deny-list)
- Structured logging with correlation IDs
- Container isolation (Docker) with no host-network access
