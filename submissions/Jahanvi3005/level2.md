# Level 2 Submission - Jahanvi Gupta

## Tracks Selected
- **Track A:** Agent Builders
- **Track D:** 3D & Visualization

## Track A: S.M.I.L.E. Methodology Reflection & LLM Output
I **chose** to run the **llama** model locally via Ollama because it is efficient and fits perfectly within my available System **RAM** constraints.

**Model Output:** "A digital twin is a virtual representation of an object or system that spans its lifecycle, is updated from real-time data, and uses simulation, machine learning and reasoning to help decision-making."

**Reflection:**
What surprised me most about the S.M.I.L.E. methodology is its 'impact first, data last' principle, which fundamentally flips traditional data engineering approaches on their head. Rather than starting with sensor deployments and raw telemetry, it demands mapping out the sociotechnological boundaries using a 'Reality Canvas' before building systems. Furthermore, the concept of a Minimal Viable Twin (MVT) to validate hypotheses virtually before physical implementation represents a brilliant shift in how we can de-risk complex AI agent integrations.

## Track D: Reality Canvas Concept - Smart Building
A 3D 'Reality Canvas' for a smart building would act as a holistic spatial-temporal anchor, integrating BIM (Building Information Modeling) and real-time IoT sensors into a unified visual ecosystem. Instead of isolated floor plans, stakeholders would navigate a live 3D representation showing occupancy heatmaps, HVAC energy flows, and structural health metrics simultaneously. This shared digital environment creates a 'Virtual First' operating context where facility managers and automated agents can concurrently simulate and resolve bottleneck scenarios before physical disruptions occur.

## LPI Sandbox Execution
```
=== LPI Sandbox Test Client ===

[LPI Sandbox] Server started — 7 read-only tools available
Connected to LPI Sandbox

Available tools (7):
  - smile_overview: Get an overview of the S.M.I.L.E. methodology
  - smile_phase_detail: Deep dive into a specific SMILE phase.
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
```
