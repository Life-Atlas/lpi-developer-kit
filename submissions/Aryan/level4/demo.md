# Demo — Level 4 Multi-Agent System

## Overview

This demo shows a multi-agent system built using LPI with:

* Research Agent → retrieves data from LPI tools
* Expert Agent → generates structured explanation
* Orchestrator → coordinates agents

---

## How to Run

### 1. Start LPI server

```bash
node dist/src/index.js
```

---

### 2. Start Ollama

```bash
ollama serve
ollama run qwen2.5:1.5b
```

---

### 3. Run orchestrator

```bash
python orchestrator.py
```

---

## Example Query

```
How are digital twins used in healthcare?
```

---

## Expected Flow

1. Orchestrator receives query
2. Research Agent selects tools:

   * `smile_overview`
   * `get_case_studies`
3. Research Agent fetches and filters data
4. Expert Agent processes context using LLM
5. Final structured answer is returned

---

## Sample Output (Summary)

* Explanation of digital twins
* Relevant SMILE phases
* Healthcare case study
* Insight + conclusion

---

## Key Highlights

* Multi-agent architecture (Research + Expert)
* Separation of data retrieval and reasoning
* Grounded responses using LPI tools
* Structured, explainable outputs
