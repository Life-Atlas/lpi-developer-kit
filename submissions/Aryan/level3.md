# Level 3 Submission — Aryan

## Project: Explainable Knowledge Agent (LPI)

*Repository:* https://github.com/iamaryan07/lpi-life-agent

*Agent:* https://github.com/iamaryan07/lpi-life-agent/blob/main/agent.py

*A2A Card:* https://github.com/iamaryan07/lpi-life-agent/blob/main/agent.json

---

## Overview

This project presents a Level 3 agent built using the Life Programmable Interface (LPI).
The agent responds to user queries by intelligently selecting multiple tools, executing them, processing their outputs, and producing a well-structured final response.

---

## Tools Used

* `smile_overview` → delivers the SMILE framework and conceptual methodology.
* `get_case_studies` → provides practical, real-world implementations.

---

## How It Works

1. Accepts a user query (for example, a healthcare-related question)
2. Determines the relevant tools to use
3. Sends JSON-RPC requests to the LPI server
4. Receives structured responses from the tools
5. Parses and extracts meaningful text from the output
6. Filters results to focus on healthcare-specific case studies
7. Combines all outputs into a final structured answer

---

## Key Features

* Coordination of multiple tools within a single workflow
* Dynamic handling of tool input arguments
* Communication with LPI via JSON-RPC using subprocess
* Structured output format (summary, analysis, conclusion)
* Context-aware filtering for domain-specific relevance (healthcare)

---

## Example Query

```text id="w3rj9s"
How are digital twins used in healthcare?
```

---

## Example Output (Summary)

* Overview of the SMILE framework
* Healthcare-focused case study (continuous patient twin)
* Combined analysis of methodology and real-world application

---

## Level 3 Criteria Met

* ✔ Utilizes multiple tools in a coordinated manner
* ✔ Integrates outputs from different sources
* ✔ Processes and structures tool responses
* ✔ Generates a meaningful and relevant final answer
* ✔ Demonstrates reasoning based on tool outputs

---

## Notes

* Uses the LPI server (`dist/src/index.js`) instead of the test client
* Applies filtering to ensure outputs match the query context
* Implemented using Python for the agent and Node.js for LPI

---

## Reflection (Beyond Instructions)

### What I did beyond the instructions

* Applied filtering logic to extract only healthcare-relevant case studies rather than returning the entire raw output
* Adjusted tool arguments (e.g., `"healthcare digital twin"`) to improve result relevance instead of directly passing the user query
* Implemented manual parsing for nested JSON-RPC responses (`result → content → text`)
* Switched from the test client to the actual LPI server (`dist/src/index.js`) and handled initialization explicitly

### What I would do differently next time

* Separate tool-calling logic into a reusable client instead of embedding it within the agent
* Improve transparency by explicitly showing reasoning steps behind tool selection and result combination
* Enhance summarization by structuring outputs (e.g., Challenge, Approach, Outcome) instead of simple truncation
* Replace rule-based tool selection with a more adaptive or query-driven approach

---
