# Level 3 Submission — Adil Islam (Track A)

## Agent: AI Learning Coach

**Repo:** https://github.com/Adilislam0/ai-learning-coach-agent

---

## Concept

Most query agents retrieve and summarize. This agent teaches.

It takes a learning question about SMILE methodology, retrieves grounded
knowledge from 3 LPI tools, and responds in a structured coaching format:
Answer → Follow-Up Question → Sources. The follow-up question is the core
differentiator — it applies SMILE's own feedback-loop principle to the
act of learning SMILE itself.

---

## LPI Tools Used

| # | Tool | Why chosen |
|---|------|-----------|
| 1 | `smile_overview` | Every session starts with full methodology context — grounds the LLM |
| 2 | `query_knowledge` | Finds the most relevant of 63 knowledge entries for the question |
| 3 | `get_insights` | Adds scenario-specific advice that query_knowledge alone misses |

---

## How to Run

```bash
pip install requests
ollama pull qwen2.5:0.5b
ollama serve                    # keep running in background
cd lpi-developer-kit && npm run build
python agent.py "What is Reality Emulation in SMILE?"
```

---

## Design Decisions

- **0.5b model** — 1.5b caused GPU then CPU OOM on my hardware. 0.5b
  loads reliably on CPU, still produces structured output with a tight prompt
- **1200-char context trim** — prevents small model stalling on long input
- **300 token output cap** — keeps responses focused, no runaway generation
- **120s timeout** — hard guarantee: no infinite hang regardless of load
- **Teaching prompt format** — explicit ANSWER/FOLLOW-UP/SOURCES structure
  forces consistent output from a small model