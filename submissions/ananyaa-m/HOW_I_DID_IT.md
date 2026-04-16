**Level 2 Submission — Ananyaa M**

---

**Test Client Output: -**

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
You can now build agents that connect to this server.

---

**What I Did: -**

    1. After succesfully completing level-1 and pulling the latest changes, I ran the "npm install" and "npm run build" to ensure that the MCP server was ready.

    2. I ran "npm run test-client" to verify that all tools were working and active.

    3. I installed Ollama on Windows 10. This helps in running LLM models locally. Then I started the "qwen2.5:1.5b" model as it is light-weight enough for my laptop.

    4. I used the "query_knowledge" tool to pull data on the SMILE methodology.

---

**Problem I Faced and Solved: -**

    My terminal didn't recognize the ollama command immediately after installation. I had to restart my VS Code to refresh the system path.

---

**What I Learned: -**

    1. I learned that the MCP (Model Context Protocol) is like a bridge which gives the LLM model ability to fetch local data or run scripts.

    2. I learned that the SMILE framework is not just about 3D visual, but also about a 6 phase lifecycle that includes human and social impact. 

    3. I learned how to run local LLMs on my laptop using Ollama.

---
