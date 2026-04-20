# Threat Model — Level 4 Multi-Agent System

## Overview

This document identifies potential threats in the multi-agent system and outlines basic mitigations.

The system consists of:

* Research Agent (tool access)
* Expert Agent (LLM reasoning)
* Orchestrator (control flow)

---

## 1. Prompt Injection

### Threat

A user may craft input that manipulates the LLM into ignoring constraints or producing unsafe outputs.

### Mitigation

* Prompt explicitly restricts output to provided tool data
* Instructions enforce: "Do not invent new concepts"
* System avoids executing user-provided instructions directly

---

## 2. Tool Misuse

### Threat

Uncontrolled tool selection could lead to irrelevant or unsafe data retrieval.

### Mitigation

* Tool selection is rule-based and restricted to known tools
* No dynamic or user-controlled tool execution
* Fixed arguments used for sensitive queries (e.g., healthcare filtering)

---

## 3. Hallucinated Outputs

### Threat

LLM may generate information not present in tool outputs.

### Mitigation

* Prompt enforces grounding in tool data
* Missing information is explicitly handled ("Not found in provided data")

---

## 4. Subprocess Risks

### Threat

Calling the LPI server via subprocess may fail or hang.

### Mitigation

* Timeout applied to subprocess calls
* Errors handled gracefully without crashing the system

---

## 5. Data Leakage

### Threat

Sensitive information could be exposed through logs or outputs.

### Mitigation

* Only tool-provided data is used
* No external or private data sources are accessed

---

## Summary

The system applies basic safeguards for:

* controlled tool usage
* LLM grounding
* safe execution

Further improvements could include:

* input sanitization
* multi-step validation
* stricter output verification
