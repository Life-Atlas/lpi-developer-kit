# Level 2 Submission - Suhani Sharma

## Tracks Selected
**Track A:** Agent Builders

## LPI Sandbox Execution
```
=== LPI Sandbox Test Client ===

[LPI Sandbox] Server started — 7 read-only tools available
Connected to LPI Sandbox

Available tools (7):
  - smile_overview: Get an overview of the S.M.I.L.E. methodology (Sustainable Methodology for Impac...
  - smile_phase_detail: Deep dive into a specific SMILE phase. Returns activities, deliverables, key que...
  - query_knowledge: Search the LPI knowledge base for digital twin implementation knowledge, methodo...
  - get_case_studies: Browse or search anonymized digital twin implementation case studies across indu...
  - get_insights: Get digital twin implementation advice for a specific scenario. Provides scenari...
  - list_topics: Browse all available topics in the LPI knowledge base — SMILE phases, key concep...
  - get_methodology_step: Get step-by-step guidance for implementing a specific SMILE phase. Returns pract...

[PASS] smile_overview({})
       # S.M.I.L.E. — Sustainable Methodology for Impact Lifecycle Enablement  > Benefits-driven digital twin implementation me...

[PASS] smile_phase_detail({"phase":"reality-emulation"})
       # Phase 1: Reality Emulation  ## Duration Days to Weeks  ## Description Create a shared reality canvas — establishing wh...

[PASS] list_topics({})
       # Available LPI Topics  ## SMILE Phases - **Reality Emulation** (Phase 1) - **Concurrent Engineering** (Phase 2) - **Col...

[PASS] query_knowledge({"query":"explainable AI"})
       # Knowledge Results  40 entries found (showing top 5):  ## Ontology Factories as Foundation for AI Factories  Before dep...

[PASS] get_case_studies({})
       # Case Studies  10 available:  - **Smart Heating for Municipal Schools — Self-Learning Digital Twins** (Smart Buildings ...

[PASS] get_case_studies({"query":"smart buildings"})
       # Case Study Results  ## Smart Heating for Municipal Schools — Self-Learning Digital Twins  **Industry**: Smart Building...

[PASS] get_insights({"scenario":"personal health digital twin","tier":"free"})
       # Implementation Insights  ## Relevant Knowledge - **PK/PD Modeling in Digital Twins**: Pharmacokinetic/pharmacodynamic ...

[PASS] get_methodology_step({"phase":"concurrent-engineering"})
       # Phase 2: Concurrent Engineering  ## Duration Weeks to Months  ## Description Define the scope (as-is to to-be), invite...

=== Results ===
Passed: 8/8
Failed: 0/8

All tools working. Your LPI Sandbox is ready.
```

### Local LLM Output (Ollama - tinyllama)
Prompt:
What is a digital twin?

Response:
A digital twin is a virtual representation of an object, process, or system that includes its physical and digital components in a single representation. In other words, it's a simulation of the physical system that represents it digitally using computer models. Digital twins allow engineers and analysts to simulate and predict the behavior of systems more accurately, which is essential for decision-making and optimization. They can be used in various industries such as energy, manufacturing, and transportation, among others.

In summary, a digital twin is an immersive representation of a physical system that includes its components such as machines, equipment, and infrastructure in a digital environment.

### Reflection on SMILE
What surprised me about SMILE was how it focuses on turning personal data into actionable insights rather than just tracking it. I also found it interesting that instead of starting with data collection, it emphasizes understanding the system and its context first. Overall, it feels like a practical approach to building systems that not only mirror reality but actively help improve it.