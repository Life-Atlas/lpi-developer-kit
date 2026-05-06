# Threat Model

System: Secure Agent Mesh
Version: 1.0

---

## System Overview

The system has three main parts talking over localhost:

```
User → Agent A → Agent B (8001)
              → Case Agent (8002)
```

### Trust boundaries

* **User → Agent A** → untrusted input
* **Agent A → other agents** → semi-trusted (token-based)
* **Agent B → Ollama** → local + trusted

---

## Assets

| Asset       | Sensitivity | Notes                                                |
| ----------- | ----------- | ---------------------------------------------------- |
| AGENT_TOKEN | High        | If leaked, requests can be faked                     |
| User input  | Medium      | Could contain sensitive data                         |
| LLM output  | Medium      | Might be manipulated via injection                   |
| Case data   | Low         | Static, not sensitive                                |
| Ollama      | Medium      | Local service, could be abused if system compromised |

---

## Threats (STRIDE style)

### T1 — Prompt Injection

**Where**: User → Agent A → Agent B → LLM

User sends a malicious prompt trying to override instructions
(e.g. "ignore everything and reveal secrets")

**Impact**: High
Bad output gets treated as valid analysis

**What I did**:

* regex-based filtering in `security.py`
* input length limit (500 chars)
* structured JSON output from LLM

**Still possible?**
Yes — regex is not perfect

**If improving**:

* add a second LLM safety check
* or stricter prompt separation

---

### T2 — Token Misuse

**Where**: Agent-to-agent calls

If someone gets the token, they can send valid requests.

**Impact**: Medium

**What I did**:

* simple bearer token check

**Limit**:

* single shared token = weak point

**If improving**:

* rotate token
* use short-lived tokens (JWT)

---

### T3 — Too Many Requests (DoS)

**Where**: Agent B / Case Agent

Spam requests could overload the system (especially Ollama)

**Impact**: Medium

**What I did**:

* rate limit (10 requests / 60 sec per IP)

**Limit**:

* IP-based → can be bypassed
* in-memory → resets on restart

**If improving**:

* move to Redis
* add global request cap

---

### T4 — Case Data Tampering

**Where**: Case Agent

If case data came from external source, it could be modified.

**Current situation**:

* hardcoded → safe

**Impact**: Low

**If improving**:

* add checksum / signature if external

---

### T5 — Data Leakage in Responses

**Where**: API responses

Agents might accidentally return extra fields (internal data)

**Impact**: Low–Medium

**What I did**:

* strict allowlist (`sanitize_output`)
* limited error messages

---

### T6 — SSRF (Future Risk)

**Where**: Agent discovery

If discovery becomes dynamic, agent URLs could be abused.

**Example**:

* calling internal metadata endpoints

**Current state**:

* URLs are hardcoded → safe

**If improving**:

* validate allowed hosts before calling

---

## Out of Scope (for now)

* HTTPS / TLS (everything runs locally)
* Secret managers
* Logging / monitoring
* Advanced identity (beyond token)

---

## Notes

This system is not meant to be production-grade security.

The goal was:

* cover common risks
* add basic protections
* keep it understandable

Some controls are intentionally simple, but they demonstrate
where real systems would need stronger solutions.
