# Level 2 Submission - Abhishek Sharma

## Tracks Selected
- **Track A:** Agent Builders  

---

## Track A: S.M.I.L.E. Methodology Reflection & LLM Output

I ran a local LLM (llama via Ollama) as part of understanding how models can operate in constrained environments. This helped me see how agent-like systems can function even with limited system resources such as RAM.

**Model Output:**  
"A digital twin is a virtual representation of an object or system that spans its lifecycle, is updated from real-time data, and uses simulation, machine learning and reasoning to help decision-making."

---

## Reflection (SMILE Methodology)

The S.M.I.L.E. methodology helped me understand how agent-based systems are designed in a structured way.

- It starts with understanding the system goal (Strategy)
- Then selecting the right model or method (Model)
- Generating outputs and insights (Insight)
- Learning from results (Learning)
- And finally executing in a controlled environment (Execution)

What I found most important is the Execution phase, where the LPI sandbox allows real tool-based testing. This shows how agents interact with tools and systems in a safe environment before real-world use.

---

## LPI Sandbox Execution
=== LPI Sandbox Test Client ===
[LPI Sandbox] Server started — 7 read-only tools available Connected to LPI Sandbox
Available tools (7):
smile_overview
smile_phase_detail
query_knowledge
get_case_studies
get_insights
list_topics
get_methodology_step
[PASS] smile_overview({}) [PASS] smile_phase_detail({"phase":"reality-emulation"}) [PASS] list_topics({}) [PASS] query_knowledge({"query":"explainable AI"}) [PASS] get_case_studies({}) [PASS] get_case_studies({"query":"smart buildings"}) [PASS] get_insights({"scenario":"personal health digital twin","tier":"free"}) [PASS] get_methodology_step({"phase":"concurrent-engineering"})
=== Results === Passed: 8/8
Failed: 0/8
All tools working. LPI Sandbox is ready.