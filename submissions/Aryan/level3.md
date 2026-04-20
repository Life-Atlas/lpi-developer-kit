# Level 3 Submission — Aryan

## Project: Explainable Knowledge Agent (LPI)

**Repository**: https://github.com/iamaryan07/lpi-life-agent

**Agent**: https://github.com/iamaryan07/lpi-life-agent/blob/main/agent.py

**A2A Card**: https://github.com/iamaryan07/lpi-life-agent/blob/main/agent.json

---

## Overview

This project implements a Level 3 agent using the Life Programmable Interface (LPI).

The agent answers user queries by:

* selecting appropriate tools based on the query
* retrieving structured knowledge from LPI
* combining multiple sources
* generating a structured, explainable response using an LLM (Qwen via Ollama)

---

## Tools Used

* `smile_overview` → provides SMILE methodology and conceptual framework
* `get_case_studies` → provides real-world digital twin implementations
* `get_methodology_step`, `get_insights` → used for implementation-focused queries

---

## How It Works

1. Accepts a user query
2. Selects tools based on query type (rule-based logic)
3. Sends JSON-RPC requests to LPI server (`dist/src/index.js`)
4. Retrieves structured outputs from multiple tools
5. Extracts and filters relevant content (e.g., healthcare-specific sections)
6. Combines tool outputs into a unified context
7. Uses an LLM (Qwen via Ollama) to generate a structured response

---

## Key Features

* Tool coordination across multiple LPI endpoints
* Query-based tool selection (simple reasoning logic)
* JSON-RPC communication with LPI via subprocess
* Context-aware filtering for domain-specific relevance (healthcare)
* LLM-based reasoning to combine methodology and real-world data
* Structured output format:

  * Understanding
  * SMILE Phases
  * Real-World Application
  * Insight
  * Conclusion
 
---

## Design Decisions & Independent Thinking

**Approach & Trade-offs:**
I used a simple rule-based tool selector instead of an LLM planner to keep tool usage predictable and avoid incorrect tool calls. This trades flexibility for reliability and easier debugging.

**Choices Beyond Instructions:**

* Added an LLM (Qwen via Ollama) to combine tool outputs into a structured answer instead of returning raw data
* Implemented filtering to extract only healthcare-relevant case study content
* Designed a strict prompt to reduce hallucination and enforce grounded responses
* Built custom parsing for nested JSON-RPC responses (`result → content → text`)

**Learning:**
Combining tool outputs with controlled LLM reasoning is more important than just calling tools.

---

## Example Query

```
How are digital twins used in healthcare?
```

---

## Example Output (Summary)

* Explanation of digital twins in healthcare
* Relevant SMILE phases (e.g., Reality Emulation, Concurrent Engineering)
* Healthcare case study (continuous patient twin)
* Insight connecting methodology with real-world application
* Clear structured conclusion

---

## Level 3 Criteria Met

* ✔ Uses multiple tools in coordination
* ✔ Selects tools based on query type
* ✔ Integrates outputs from different sources
* ✔ Uses an LLM to synthesize and structure results
* ✔ Produces explainable, structured answers

---

## Notes

* Uses actual LPI server (`dist/src/index.js`) instead of test client
* Applies filtering to extract healthcare-relevant case study content
* Implemented using Python (agent) and Node.js (LPI server)

---

## Reflection

### What I did beyond the instructions

* Implemented query-based tool selection instead of fixed tool usage
* Applied filtering logic to extract domain-specific (healthcare) insights
* Integrated an LLM (Qwen via Ollama) for reasoning instead of rule-based output
* Designed a structured prompt to enforce grounded, explainable responses
* Handled nested JSON-RPC parsing (`result → content → text`)

### What I would improve next

* Add explicit reasoning trace for better transparency
* Improve error handling for tool and LLM failures
* Support multi-step reasoning instead of single-pass generation
* Expand tool selection strategy for broader query coverage

---
