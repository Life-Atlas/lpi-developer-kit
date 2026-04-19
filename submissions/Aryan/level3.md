# Level 3 Submission — Aryan

## Project: Explainable Knowledge Agent (LPI)

**Repository:** [https://github.com/iamaryan07/lpi-life-agent/tree/main]

---

## Description

An explainable AI agent that answers user queries by combining general knowledge (Wikipedia) and research-level insights (Arxiv).

The system ensures that every response is:

- **grounded** in real retrieved data
- **synthesized** across multiple sources
- **fully traceable** (Explainable AI requirement)

---

## Key Features

- **Dual-Source Retrieval:** Uses two LPI tools
  - Wikipedia → general understanding
  - Arxiv → research insights

- **Explainable AI:** Clearly shows:
  - what came from Wikipedia
  - what came from Arxiv

- **Structured Output:**
  - Combined Answer
  - Wikipedia Contribution
  - Arxiv Contribution
  - Source trace (papers, authors, URLs)

- **Deterministic Pipeline:** Tools are explicitly called (not left to LLM randomness)

---

## LPI Tools Used

- **WikipediaQueryRun** (langchain-community)  
  Retrieves general explanations and definitions

- **Arxiv Python SDK**  
  Retrieves real research papers (title, authors, summary, URL)

---

## Technical Architecture

- **Language:** Python 3
- **LLM:** HuggingFace (meta-llama/Llama-3.2-1B-Instruct)
- **Framework:** LangChain (tool integration)
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

COMBINED ANSWER:

Machine learning is defined as algorithms that learn from data (Wikipedia).
Arxiv research extends this by highlighting challenges such as model validation
and data reliability in real-world applications.

---

## WIKIPEDIA CONTRIBUTION:

Definition of machine learning

Statistical foundation

---

## ARXIV CONTRIBUTION:

Paper: DOME → validation standards in ML

Paper: Data Sources → importance of reliable data

---

## SOURCES:
Wikipedia snippet + Arxiv paper titles, authors, URLs

text

---

## What Makes This Correct for Level 3

- ✅ Uses 2 real tools (mandatory requirement)
- ✅ Performs actual synthesis, not raw output
- ✅ Provides traceable explanations
- ✅ Shows clear mapping between sources and answer

---

## Files in Repository

- `agent.py` — main implementation
- `README.md` — documentation and setup
- `requirements.txt` — dependencies

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
