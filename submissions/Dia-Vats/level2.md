# Level 2 submission - Dia Vats


## Test Client Output

=== LPI Sandbox Test Client ===

[LPI Sandbox] Server started — 7 read-only tools available
Connected to LPI Sandbox

Available tools (7):
- smile_overview: Get an overview of the S.M.I.L.E. methodology
- smile_phase_detail: Deep dive into a specific SMILE phase
- query_knowledge: Search the LPI knowledge base
- get_case_studies: Browse or search anonymized case studies
- get_insights: Get digital twin implementation advice
- list_topics: Browse all available topics
- get_methodology_step: Get step-by-step guidance

[PASS] smile_overview({})
[PASS] smile_phase_detail({"phase":"reality-emulation"})
[PASS] list_topics({})
[PASS] query_knowledge({"query":"explainable AI"})
[PASS] get_case_studies({})
[PASS] get_case_studies({"query":"smart buildings"})
[PASS] get_insights({"scenario":"personal health digital twin","tier":"free"})
[PASS] get_methodology_step({"phase":"concurrent-engineering"})

=== Results ===
Passed: 8/8
Failed: 0/8

All tools working. Your LPI Sandbox is ready.

---

## Track A: S.M.I.L.E. Methodology Reflection & LLM Output

I chose to run the mistral model locally via Ollama because it provided a good balance of speed and performance on my system.
Initially, I tried gemma4:e2b, but it was too slow, so I switched to a lighter model.
The mistral model handled the SMILE prompt well without needing any cloud-based setup.

### Model Output:

1. Modeling  
We create digital models of physical assets like machines or buildings. This helps us understand and predict behavior.
2. Simulation  
We run simulations on these models to test behavior under different conditions and predict issues.
3. Integration  
We connect models with real-world sensor data so the digital twin reflects the actual system state.
4. Leverage  
We use the digital twin to optimize operations, predict maintenance, train staff, and improve design.
We use the digital twin to optimize operations, predict maintenance, train staff, and improve design.

---

### SMILE Reflection:

1. What surprised me most is that SMILE starts with understanding the real-world problem first instead of jumping into data or models.  
2. I realized that the methodology is structured in clear phases where each step builds logically on the previous one.  
3. I learned that the focus is less on technical complexity and more on defining and connecting the problem correctly before building anything.

---

