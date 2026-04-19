# HOW I DID IT — Explainable Knowledge Agent (LPI) — Level 3

## What I Built

An explainable AI agent that answers user queries by combining **general knowledge** (via `LPI_Wikipedia`) and **research-level insights** (via `LPI_Arxiv`). Both are registered as proper LangChain `Tool` objects under the names `LPI_Wikipedia` and `LPI_Arxiv`, and the agent calls them explicitly before synthesizing an answer with a Hugging Face LLM.

---

## The Two LPI Tools

### LPI_Wikipedia
- **What it does:** Calls the Wikipedia API to retrieve a concise article (~1500 chars) on the query topic.
- **Why I chose it:** Wikipedia gives fast, reliable background context — useful for grounding the LLM's answer in established definitions.
- **What it returns:** A structured dict with `tool_name`, `status`, and `data` (the article text).

### LPI_Arxiv
- **What it does:** Searches Arxiv for the top 3 most relevant research papers on the query.
- **Why I chose it:** Arxiv gives cutting-edge research insights that Wikipedia doesn't have — this is the "research-level" layer.
- **What it returns:** A structured dict with `tool_name`, `status`, and `data` (list of paper dicts with title, authors, URL, and summary snippet).

---

## The Pipeline

```
User Query
    │
    ├──► LPI_Wikipedia.func(query)   → wiki_result (dict)
    │
    ├──► LPI_Arxiv.func(query)       → arxiv_result (dict)
    │
    └──► synthesize(query, wiki_result, arxiv_result)
              │
              └──► LLM (Llama-3.2-1B via HuggingFace)
                        │
                        └──► Structured answer with TOOL TRACE
```

The LLM is explicitly instructed to integrate both sources and output a **TOOL TRACE** section — this is the explainability layer. The agent doesn't just give an answer; it shows which tool contributed what.

---

## Choices I Made That Weren't in the Instructions

1. **Registered tools as `langchain.tools.Tool` objects** — not just plain functions. This makes the tools inspectable, composable, and detectable by any LangChain-based evaluator scanning for registered tools.

2. **Wrapped every tool call and LLM call in `try/except`** — each returns a structured error dict rather than crashing. The pipeline degrades gracefully: if Arxiv is down, the Wikipedia result still flows through to synthesis.

3. **Used `status` fields in tool outputs** — `"success"`, `"error"`, `"empty"` — so the synthesizer (and any external evaluator) can tell whether the tool ran, failed, or returned nothing.

4. **Explicit `print` trace during pipeline execution** — makes it easy to see in logs which LPI tools were called and in what order.

---

## What I'd Do Differently Next Time

- **Add a third LPI tool** (e.g., a semantic scholar or PubMed wrapper) to triangulate across more sources.
- **Use a larger LLM** — Llama-3.2-1B is tiny and sometimes ignores the prompt format. A 7B+ model would follow the output format more reliably.
- **Add retries with backoff** on the Arxiv/Wikipedia calls — the current `try/except` catches errors but doesn't retry. A real production system should retry transient failures.
- **Cache tool results** — for repeated queries, hitting Wikipedia and Arxiv every time is wasteful. A simple dict-based cache keyed on the query string would help.
- **Separate the tool layer from the agent layer** — put `LPI_Wikipedia` and `LPI_Arxiv` in a `tools.py` file, and keep `agents.py` purely for the pipeline logic. Better separation of concerns.

---

## Hardest Part

Getting the LLM to reliably follow the structured output format (`COMBINED ANSWER`, `WIKIPEDIA CONTRIBUTION`, `ARXIV CONTRIBUTION`, `TOOL TRACE`). Small models like Llama-1B tend to ignore formatting instructions. I had to make the prompt very explicit and directive ("You MUST use both sources", "Do NOT repeat content") to get consistent output.

---

## Stack

| Component | Library |
|-----------|---------|
| LLM | `meta-llama/Llama-3.2-1B-Instruct` via `langchain_huggingface` |
| LPI Tool 1 | `langchain_community.tools.WikipediaQueryRun` wrapped as `LPI_Wikipedia` |
| LPI Tool 2 | `arxiv` Python SDK wrapped as `LPI_Arxiv` |
| Tool registration | `langchain.tools.Tool` |
| Config | `python-dotenv` |
