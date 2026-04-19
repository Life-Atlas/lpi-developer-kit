# Level 3 Submission — Aryan

## Project: Explainable Knowledge Agent (LPI)

**Repository:** https://github.com/iamaryan07/lpi-life-agent/tree/main

---

## Description

An explainable AI agent that answers user queries by combining **general knowledge (Wikipedia)** and **research-level insights (Arxiv)**.

The system ensures that every response is:

- **grounded** in real retrieved data  
- **synthesized** across multiple sources  
- **fully traceable** (Explainable AI requirement)  

---

## Key Features

- **Dual-Source Retrieval:** Uses two LPI tools  
  - LPI_Wikipedia → general understanding  
  - LPI_Arxiv → research insights  

- **Explainable AI:**  
  - Explicit tool trace included  
  - Every part of the answer is mapped to a source  

- **Structured Output:**  
  - Combined Answer  
  - Wikipedia Contribution  
  - Arxiv Contribution  
  - Tool Trace  
  - Source details (papers, authors, URLs)  

- **Deterministic Pipeline:**  
  Tools are explicitly called (not left to LLM randomness)

---

## Explainability (Tool Trace)

The system provides explicit traceability for every answer:

- **LPI_Wikipedia** → provides definition and general explanation  
- **LPI_Arxiv** → provides research insights and technical findings  

This ensures that every part of the answer can be traced back to its source.

---

## LPI Tools Used

1. **LPI_Wikipedia** (via WikipediaQueryRun)  
   - Provides general knowledge and definitions  

2. **LPI_Arxiv** (via Arxiv Python SDK)  
   - Provides research papers (title, authors, summary, URL)  

---

## Technical Architecture

- **Language:** Python 3  
- **LLM:** HuggingFace (`meta-llama/Llama-3.2-1B-Instruct`)  
- **Framework:** LangChain  
- **Data Sources:**  
  - Wikipedia API  
  - Arxiv API  

---



## Agent Pipeline
User Query
↓
Wikipedia Tool (general knowledge)
↓
Arxiv Tool (research papers)
↓
LLM (Llama) synthesis
↓
Structured Answer + Source Attribution

text

---

## Example Usage

```bash
python agent.py "What is machine learning?"
```
---

## Sample Output (Simplified)

**COMBINED ANSWER**

Machine learning is defined as algorithms that learn from data (Wikipedia).
Arxiv research extends this by highlighting challenges such as model validation
and data reliability in real-world applications.

**WIKIPEDIA CONTRIBUTION** 

Definition of machine learning
Statistical foundation

**ARXIV CONTRIBUTION**

Paper: DOME → validation standards in ML
Paper: Data Sources → importance of reliable data

**TOOL TRACE**

LPI_Wikipedia → definition of machine learning
LPI_Arxiv → research insights (validation, data reliability)

**SOURCES**

Wikipedia snippet
Arxiv paper titles, authors, URLs


---

## What Makes This Correct for Level 3

- ✅ Uses 2 real tools (mandatory requirement)
- ✅ Performs actual synthesis, not raw output
- ✅ Provides traceable explanations
- ✅ Shows clear mapping between sources and answer

---

## Files in Repository

- agent.py — main implementation
- README.md — documentation and setup
- HOW_I_DID_IT.md — design decisions, challenges, improvements
- requirements.txt — dependencies
---

## Testing Results

**Tested with:**  
`"What is machine learning?"`

---

**Results:**

- Wikipedia data retrieved successfully
- Arxiv papers retrieved (titles, authors, summaries)
- LLM combined both sources
- Output remained structured and traceable
