# Level 2 Submission — Track B

## LPI Sandbox Output
All 7 tools ran successfully using npm run test-client.
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
       # Available LPI Topics  ## SMILE Phases - *Reality Emulation* (Phase 1) - *Concurrent Engineering* (Phase 2) - **Col...

[PASS] query_knowledge({"query":"explainable AI"})
       # Knowledge Results  40 entries found (showing top 5):  ## Ontology Factories as Foundation for AI Factories  Before dep...

[PASS] get_case_studies({})
       # Case Studies  10 available:  - *Smart Heating for Municipal Schools — Self-Learning Digital Twins* (Smart Buildings ...

[PASS] get_case_studies({"query":"smart buildings"})
       # Case Study Results  ## Smart Heating for Municipal Schools — Self-Learning Digital Twins  *Industry*: Smart Building...

[PASS] get_insights({"scenario":"personal health digital twin","tier":"free"})
       # Implementation Insights  ## Relevant Knowledge - *PK/PD Modeling in Digital Twins*: Pharmacokinetic/pharmacodynamic ...

[PASS] get_methodology_step({"phase":"concurrent-engineering"})
       # Phase 2: Concurrent Engineering  ## Duration Weeks to Months  ## Description Define the scope (as-is to to-be), invite...

=== Results ===
Passed: 8/8
Failed: 0/8

All tools working. Your LPI Sandbox is ready.
You can now build agents that connect to this server.

## Industry Chosen
Sustainable Artificial Intelligence

## Summary
Artificial Intelligence is transforming industries ranging from sports to agriculture to smart cities but it also consumes significant computational power and energy thus creating a negative environmental impact and raises a huge concern for sustainability. Therefore, making AI systems efficient and eco-friendly has become increasingly important. Therefore we need to make AI sustainable.
SMILE is a smart framework. Instead of collecting tons of data then figuring out what to prune we need to figure out what’s the minimum data and effort for a defined goal. It uses digital twins, simulations, and continuous intelligence to build systems that are efficient, adaptive, and sustainable. This outcome driven framework can be used to make sustainable AI systems. 
Phase 1: Reality Emulation
A digital twin of the AI system is created, including datasets, models, and computational resources. Main goal is to help understand energy usage and system behaviour without actual heavy computation.

Phase 2: Concurrent Engineering
Different AI models, dataset sizes, and training strategies are tested in a simulated environment. Main goal is to help identify the most efficient approach without wasting resources.

Phase 3: Collective Intelligence
Real-time data from systems (like servers, GPUs, and user interactions) is collected. Main goal is to enable monitoring of performance and energy consumption while ensuring shared understanding across teams.

Phase 4: Contextual Intelligence
AI systems make real-time decisions to optimise performance and reduce energy use. For example, workloads can be balanced or shifted to low-power modes when demand is low.

Phase 5: Continuous Intelligence
The system becomes predictive, suggesting improvements like model compression, pruning, or efficient retraining schedules to minimise resource usage.

Phase 6: Perpetual Wisdom
Knowledge about sustainable AI practices is shared across organisations, enabling global adoption of energy-efficient AI solutions.

Benefits of this approach include better decision making as simulation based testing reduces trial and error. Optimised models use less data, energy, and computational power. AI can forecast system needs and prevent unnecessary resource usage. There is reduced carbon footprint and environmentally responsible AI development. 

SMILE provides a structured approach to making AI systems sustainable by focusing on simulation, and continuous optimisation. By applying its phases, AI can not only become powerful but also energy efficient and environmentally responsible, reducing carbon footprints.