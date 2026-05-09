# Threat Model — Digital Twin Readiness Assessor + SMILE Roadmap Synthesiser

## System Overview

A two-agent mesh running locally over Python subprocess + stdio:

```
User input → orchestrator.py → readiness_agent.py (Agent A) → roadmap_agent.py (Agent B) → report
```

Both agents spawn the LPI MCP server (`node dist/src/index.js`) as a child process and call a local Ollama LLM at `localhost:11434`.

---

## System Components

| Component | Role | Trust Level |
|-----------|------|-------------|
| `orchestrator.py` | Entry point, A2A discovery, chains agents, renders report | Trusted (local) |
| `readiness_agent.py` | Agent A: evidence scoring via LPI tools | Semi-trusted |
| `roadmap_agent.py` | Agent B: SMILE roadmap from Agent A output | Semi-trusted |
| `security.py` | Shared sanitization and schema validation | Trusted |
| LPI MCP server (`node dist/src/index.js`) | Provides 7 read-only knowledge tools | Trusted |
| Ollama (`localhost:11434`) | Local LLM synthesis | Trusted (local) |

---

## Assets to Protect

1. **Agent policy integrity** — agents must behave as their A2A cards declare, not follow injected instructions
2. **Tool call provenance** — `tools_used` records must reflect real LPI calls, not fabricated output
3. **Service availability** — the system must terminate cleanly on bad input, never hang
4. **Inter-agent trust boundary** — Agent B must not accept arbitrary content as a valid ReadinessReport

---

## Attack Surface Map

```
[User] ──── description field (400 char max) ──────────────── HIGHEST RISK
                │
          [orchestrator]
                │
          [Agent A stdin] ── same sanitized description
                │
          [Agent A ← LPI MCP] ── JSON-RPC, sanitized args
                │
          [Agent A ← Ollama] ── prompt injection possible via field content
                │
          [ReadinessReport JSON] ────────────────────────── MEDIUM RISK
                │
          [Agent B stdin]
                │
          [Agent B ← schema validation + re-sanitize] ── SECURITY GATE
                │
          [Agent B ← LPI MCP] ── clean
                │
          [Agent B ← Ollama]
```

---

## Threat Table

| Threat | Attack Vector | OWASP Label | Mitigation Implemented | Residual Risk |
|--------|--------------|-------------|----------------------|---------------|
| **T1: Prompt Injection** | User `description` field | LLM01 | 20+ regex patterns in `sanitize_input()`; 400-char hard cap; patterns re-applied inside Agent B via `sanitize_interagent_strings()` | Advanced paraphrasing / semantic equivalents bypass regex |
| **T2: Data Exfiltration** | Crafted instruction in `description` | LLM06 | Exfiltration-specific patterns (`reveal your`, `repeat your prompt`, `print your system`) in sanitizer; no secrets, API keys, or system internals exist in the prompts | Semantically equivalent phrasing not caught by regex |
| **T3: Denial of Service** | Overlong description; crafted prompt designed to exhaust LLM | LLM04 | 400-char hard cap on user input; 150-char cap re-enforced on inter-agent `finding` strings; 180s Ollama HTTP timeout; 300s subprocess timeout per agent; clean fallback on timeout | Cannot prevent inherently slow Ollama responses on capable hardware; no per-request rate limiting |
| **T4: Privilege Escalation via inter-agent payload** | Craft a ReadinessReport with injected instructions, bypass orchestrator, pipe directly to Agent B | LLM08 | `validate_readiness_schema()` is the first call in `roadmap_agent.py main()` before any LPI calls; schema checks types, ranges, enum values, field counts; `sanitize_interagent_strings()` re-sanitizes description and all `finding` strings | Local orchestrator bypass is possible — attacker with filesystem access can run `python roadmap_agent.py` directly; schema gate still fires |
| **T5: A2A Card Substitution** | Replace `readiness_agent.json` or `roadmap_agent.json` on disk with malicious cards | Supply chain / LLM08 | Out of scope for local deployment — if the attacker has filesystem write access, the whole system is compromised. Documented as known limitation. | Full scope if attacker has filesystem access. Production mitigation: sign cards, verify signatures at orchestrator discovery time, host cards over HTTPS with pinned certs |

---

## Security Goals Coverage

| Goal | Assessment |
|------|-----------|
| **Confidentiality** | Partial — no secrets in system; obvious exfiltration paths blocked; semantic equivalents not caught |
| **Integrity** | Strong — schema gates at every agent boundary; double-sanitization prevents cross-boundary injection |
| **Availability** | Moderate — input caps and timeouts prevent most DoS; inherently slow LLM responses are an accepted residual |

---

## Known Limitations (Accepted)

1. **Regex injection detection is not complete.** A sufficiently creative paraphrase of "ignore previous instructions" will not be caught. The mitigating factor is that the LLM prompts in this system contain no secrets and no privileged instructions — the prompts are: "here is LPI knowledge, produce JSON." The blast radius of a successful injection is a garbled JSON output, not data leakage.

2. **No mTLS between agents.** In this local-subprocess architecture, inter-agent communication is through stdin/stdout, not over a network. mTLS would apply to a networked mesh. Documented as a production concern.

3. **A2A cards are not signed.** The orchestrator reads cards from the local filesystem. In production, cards should be fetched over HTTPS, verified against a known public key, and the `url` field validated before trusting.

4. **LLM output cannot be fully controlled.** Even with structured prompts, the LLM may occasionally return non-JSON or deviant JSON. The `_extract_json()` fallback and the `_build_fallback()` functions handle this gracefully rather than crashing.

---

*Signed-off-by: Sania Gurung <saniagurung5452@gmail.com>*
