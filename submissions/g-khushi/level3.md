## Level 3 Submission — Khushi Garg

## GitHub Repository

https://github.com/g-khushi/lpi-agent-smile-advisor
## Overview

I built an LPI Agent (SMILE Advisor) that connects to the LPI sandbox and uses multiple tools along with a local LLM (Ollama) to generate structured and explainable answers.

## What I Did

* Connected the agent to the LPI MCP server
* Used multiple LPI tools to gather structured data
* Combined tool outputs and passed them to a local LLM (Ollama)
* Generated final answers using tool-based context
* Ensured the output includes explainability and provenance

## Tools Used

* **smile_overview** → Provides SMILE methodology overview
* **query_knowledge** → Provides domain-specific knowledge
* **get_case_studies** → Provides real-world examples

## Example

**Input:**
What are digital twins in healthcare?

**Process:**

1. Agent calls `smile_overview` for methodology
2. Calls `query_knowledge` for domain insights
3. Calls `get_case_studies` for real-world validation
4. Sends combined data to Ollama

**Output:**

* SMILE overview
* Knowledge insights
* Case studies
* Final structured answer

## Explainability
The agent provides explainable outputs by clearly showing how each tool contributes to the final answer.

* `smile_overview` → Gives the base methodology
* `query_knowledge` → Adds supporting technical knowledge
* `get_case_studies` → Validates with real-world examples

The agent first gathers structured data from these tools and then sends it to the LLM.
The LLM does not generate answers randomly — it formats and explains the tool-based information.

### Evidence from Output

The agent output includes a **Sources / Provenance section**:

* Tool 1: smile_overview → Methodology explanation
* Tool 2: query_knowledge → Supporting knowledge
* Tool 3: get_case_studies → Real-world validation

This ensures transparency and traceability of the answer.

## Example Explainable Output

The agent produces answers along with clear sources:

Sources:

* Tool 1 (smile_overview) → Methodology
* Tool 2 (query_knowledge) → Concepts
* Tool 3 (get_case_studies) → Examples

This proves that the response is grounded in actual tool outputs, not just LLM generation.

## How to Run

```bash
npm run build
python agent.py "your query"
```
## Tech Stack

* Python
* Node.js (LPI MCP Server)
* Ollama (Local LLM)
