# LEVEL 3 SUBMISSION

## Overview

This project implements a Level 3 agent using the Life Programmable Interface (LPI).
The agent answers user queries by selecting and calling multiple tools, processing their outputs, and generating a structured response.

---

## Tools Used

* `smile_overview` → provides SMILE methodology
* `get_case_studies` → provides real-world implementations

---

## How It Works

1. Takes user input (e.g., healthcare-related query)
2. Selects two relevant tools
3. Sends JSON-RPC requests to LPI server
4. Receives structured responses
5. Parses and extracts relevant text
6. Filters healthcare-specific case study
7. Combines outputs into final answer

---

## Key Features

* Multi-tool orchestration
* Dynamic argument handling for tools
* JSON-RPC communication via subprocess
* Structured output (summary + analysis + conclusion)
* Domain-specific filtering (healthcare use case)

---

## Example Query

```text
How are digital twins used in healthcare?
```

---

## Example Output (Summary)

* SMILE framework overview
* Healthcare case study (continuous patient twin)
* Analysis of methodology + application

---

## Level 3 Criteria Met

* ✔ Uses multiple tools
* ✔ Combines outputs from different tools
* ✔ Processes and structures responses
* ✔ Produces a meaningful final answer
* ✔ Demonstrates reasoning over tool outputs

---

## Notes

* Uses LPI server (`dist/src/index.js`), not test client
* Filters case studies to match query context
* Built using Python + Node.js (LPI)

---
