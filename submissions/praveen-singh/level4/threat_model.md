# Threat Model — Secure Agent Mesh

## System Overview

* Agent A: Decision Agent (no tool access)
* Agent B: Grounding Agent (calls LPI tools)
* Orchestrator: Controls flow and validation

---

## Attack Surface

1. User input
2. Tool outputs (Agent B)
3. Agent A reasoning
4. Inter-agent data exchange

---

## Key Threats & Mitigation

### 1. Prompt Injection

* **Risk:** Malicious input overrides instructions
* **Fix:** Input sanitization blocks keywords like *ignore, bypass, override*

---

### 2. Data Exfiltration

* **Risk:** Leakage of system prompts or internal data
* **Fix:** Output filtering removes sensitive terms

---

### 3. Denial of Service (DoS)

* **Risk:** Very large inputs or heavy processing
* **Fix:** Input length limits + tool timeouts

---

### 4. Privilege Escalation

* **Risk:** Agent A accessing tools or bypassing flow
* **Fix:** Only Agent B can call tools; orchestrator validates data

---

### 5. Data Poisoning

* **Risk:** Irrelevant/misleading tool results
* **Fix:** Agent B filters and returns only relevant data

---

## Summary

* Input is validated
* Output is filtered
* Agents have strict roles
* System resists common LLM attacks
