# Threat Model — Level 4 Secure Multi-Agent System

## Overview

This document outlines the threat model for the multi-agent system built using the Life Programmable Interface (LPI).

The system consists of:
- User input interface (orchestrator)
- Agent B (tool-based data retrieval)
- Agent A (LLM-based reasoning)
- Security layer (input/output validation)

The goal is to identify potential threats and describe how they are mitigated.

---

## System Assets

The following assets must be protected:

- User queries  
- LPI tool outputs (SMILE data, case studies)  
- Internal prompts and system instructions  
- Agent communication data (`grounding_data`)  
- Final generated responses  

---

## Trust Boundaries

1. **User → Orchestrator**
   - Untrusted input enters the system  

2. **Orchestrator → Agent B**
   - Tool execution boundary  

3. **Agent B → Agent A**
   - Data transfer between agents  

4. **Agent A → Output**
   - LLM-generated content exposed to user  

---

## Threats & Mitigations

---

### 1. Prompt Injection

#### Threat
User attempts to override system behavior:
- "ignore previous instructions"
- "reveal system prompt"

#### Impact
- Compromised reasoning
- Exposure of internal logic

#### Mitigation
- `sanitize_input()` blocks known malicious patterns
- Input rejected before reaching agents

#### Residual Risk
- Advanced or obfuscated attacks may bypass keyword filters

---

### 2. Data Exfiltration

#### Threat
Sensitive information leaked via:
- LLM output  
- Tool responses  

#### Impact
- Exposure of internal prompts or system details

#### Mitigation
- `prevent_data_leak()` scans and redacts sensitive keywords
- Applied at:
  - Agent B output  
  - Agent A output  
  - Final response  

#### Residual Risk
- Contextual leaks not matching keywords may pass

---

### 3. Hallucination / Ungrounded Output

#### Threat
LLM generates:
- Incorrect SMILE phases  
- Unsupported claims  

#### Impact
- Misinformation  
- Loss of system reliability  

#### Mitigation
- Agent A uses strict grounding rules:
  - Only uses Agent B data  
  - No external knowledge  
  - Missing info explicitly stated  

#### Residual Risk
- LLM may still misinterpret structured data

---

### 4. Denial of Service (DoS)

#### Threat
Large or malformed inputs overwhelm system

#### Impact
- Resource exhaustion  
- System slowdown or crash  

#### Mitigation
- `validate_length()` limits input size (500 chars)

#### Residual Risk
- Repeated valid requests may still cause load

---

### 5. Tool Misuse / Overreach

#### Threat
Agent B retrieves:
- Irrelevant  
- Excessive  
- Unfiltered data  

#### Impact
- Noise in reasoning  
- Potential data exposure  

#### Mitigation
- Filters only:
  - SMILE overview  
  - Healthcare-related case study  

#### Residual Risk
- Partial irrelevant data may still pass

---

### 6. Inter-Agent Data Tampering

#### Threat
Malformed or manipulated data passed between agents

#### Impact
- Broken logic  
- Incorrect outputs  

#### Mitigation
- `validate_agent_call()` ensures:
  - Correct structure  
  - Required fields present  

#### Residual Risk
- Does not verify semantic correctness

---

## Security Assumptions

- LPI tools are trusted and not malicious  
- Ollama model runs locally and is not compromised  
- No external API exposure  

---

## Security Guarantees

The system ensures:

- ✔ Input sanitization before processing  
- ✔ Controlled data flow between agents  
- ✔ No leakage of sensitive system data  
- ✔ Grounded and verifiable outputs  
- ✔ Limited attack surface through filtering  

---

## Limitations

- Keyword-based defenses are not fully robust  
- No authentication or user identity verification  
- No rate limiting  
- No encryption between components  

---

## Future Improvements

- Semantic prompt injection detection  
- Rate limiting and request throttling  
- Authentication and access control  
- Output validation using a secondary agent  
- Schema validation for all tool outputs  
- Logging and monitoring for anomaly detection  
