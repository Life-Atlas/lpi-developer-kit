# Level 2 Submission — Varshit Pratap Singh Bhadauria

## What I Did

1. Ran npm install, npm run build, npm run test-client — all 8/8 LPI tools passed successfully.
2. Installed Ollama and pulled the qwen2.5:1.5b model locally.
3. Ran the local LLM with a SMILE-related query and compared its output with LPI tools.

## Problems I Hit

- Ollama was already running in background when I tried `ollama serve` — got a port conflict error.
- Solved it by directly running `ollama run` without `ollama serve`.

## What I Learned

1. The local LLM incorrectly expanded SMILE as "Simulation, Model, Input, Output, Execution" — showing that general-purpose models hallucinate domain-specific knowledge.
2. The actual SMILE methodology (Sustainable Methodology for Impact Lifecycle Enablement) focuses on 6 structured phases for building digital twins — which the LPI tools explained far more accurately.
3. This proved why grounding AI agents with domain-specific tools like LPI is critical — LLMs alone cannot be trusted for specialized knowledge without retrieval-augmented context.