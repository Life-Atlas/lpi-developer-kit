# Security Audit — Level 4 Multi-Agent System

## Overview

This document outlines potential risks and mitigation strategies for the multi-agent system using LPI tools and an LLM.

---

## 1. Tool Input Safety

### Risk

User queries are directly passed to LPI tools, which may lead to unexpected or irrelevant outputs.

### Mitigation

* Tool selection is controlled using rule-based logic
* Fixed arguments are used for sensitive tools (e.g., healthcare filtering in `get_case_studies`)
* Only known tool names are allowed

---

## 2. LLM Hallucination

### Risk

The LLM may generate information not present in the tool outputs.

### Mitigation

* Prompt explicitly restricts output to provided data
* Instructions enforce: *"Do not invent new concepts"*
* Missing data is handled with: *"Not found in provided data"*

---

## 3. Data Integrity

### Risk

Incorrect parsing of JSON-RPC responses could lead to incomplete or misleading outputs.

### Mitigation

* Custom parsing ensures extraction from `result → content → text`
* Fallback handling for empty or malformed responses

---

## 4. Process Execution Risk

### Risk

Subprocess calls to the LPI server may fail or hang.

### Mitigation

* Timeout is applied to subprocess communication
* Errors are caught and returned safely
* System does not crash on tool failure

---

## 5. Over-Reliance on Single Pass

### Risk

The system generates answers in a single pass without validation.

### Mitigation (Future Work)

* Introduce reflection or validation step
* Add multi-step reasoning loop

---

## Summary

The system applies basic safeguards for:

* controlled tool usage
* grounded LLM responses
* safe subprocess handling

Further improvements can enhance robustness and reliability in production environments.
