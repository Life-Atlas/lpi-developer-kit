# Comprehensive Threat Model: LPI Level 4

## 1. System Architecture & Attack Surface
The system is built as a highly secure, production-ready Agent Mesh operating over local HTTP communication.
- **Agent A (Gateway Client)**: In-Memory Rate Limiting, regular expression input filtering, lengths restriction.
- **Agent B (LLM Server)**: Native Python HTTP server enforcing strict POST intent structures, safe fallback logic, and restricted local port exposure.

## 2. Identified Threats & Mitigations

### Threat 1: Prompt Injection (User Input → LLM)
**Risk Level: Critical**
Attackers craft input to jailbreak the ultimate LLM or the agent orchestration prompt.
- **Mitigation**: Agent A scans raw regex-normalized inputs for a matrix of known injection signatures (`ignore all`, `system prompt`, `bypass`, `override`). Matching inputs force an immediate 403-equivalent termination before A2A engagement.

### Threat 2: Data Exfiltration (System Data Disclosure)
**Risk Level: High**
A hijacked agent dumping environmental variables or internal JSON states into the A2A stdout.
- **Mitigation**: Output Field Whitelisting. The HTTP server explicitly constructs a fresh Dictionary returning ONLY `status`, `answer`, and `provenance`. Everything else in memory is discarded.

### Threat 3: Denial of Service (Resource Exploitation)
**Risk Level: High**
Spamming Agent A to crash the LLM pipeline and exhaust memory limits.
- **Mitigation**: In-Memory Rate Limiter restricting requests to 10 HTTP routes per minute per user identity. Additional 1000-character max bounds checking prevents buffer inflation.

### Threat 4: Privilege Escalation (Task Manipulation)
**Risk Level: Critical**
Tricking the system into executing unapproved native or system-level tools.
- **Mitigation**: Strict schema logic inside Agent B. A hardware-coded whitelist array (`["query_knowledge", "smile_phase_detail"]`) guards the MCP simulator. Any unseen command immediately throws a 401 Unauthorized Error, crashing the attempt.

### Threat 5: Resource Exhaustion (Zombie Threads & Process Hangs)
**Risk Level: Medium**
Agent B's subprocess or Ollama connection gets stuck eternally waiting for a response, locking up Agent A connections.
- **Mitigation**: Network Timeouts. Both the overarching Agent A request (30s) and the Agent B to Ollama connection (10s) are wrapped in rigid timeout bounds, ensuring failures are fast and graceful.
