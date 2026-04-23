# Level 2 Submission — Praveen Singh

## LPI Sandbox Setup

All 7 tools executed successfully, confirming that the LPI sandbox is functioning correctly. Using the test client felt like interacting with a modular system where each tool represents a specific capability of the agent. Instead of producing a single combined output, the system exposes well-defined functions, which clearly demonstrates how agents can operate through structured tool calls rather than relying entirely on raw LLM responses.

---

## Test Client Output

=== LPI Sandbox Test Client ===

[LPI Sandbox] Server started — 7 read-only tools available
Connected to LPI Sandbox

Available tools (7):

* smile_overview
* smile_phase_detail
* query_knowledge
* get_case_studies
* get_insights
* list_topics
* get_methodology_step

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
You can now build agents that connect to this server.

---

## Local LLM Setup (Ollama)

**Model used:**
qwen2.5:1.5b

**Prompt:**
What is SMILE methodology?

**Response (summary):**
The model explained SMILE as a structured approach focused on managing the full lifecycle of information. It highlighted how processes like data creation, storage, access control, and deletion can be systematized, leading to better compliance, lower risk, and improved efficiency.

**Observation:**
Running the model locally felt noticeably different from using cloud APIs. Having direct control over execution made the process more transparent and gave it a system-level feel, rather than just sending queries to an external service.

---

## Reflection on SMILE Methodology

SMILE comes across more as a systems engineering approach than just a standard methodology. A key takeaway for me was its focus on designing systems that enforce correct behavior by default, instead of depending on manual rules or user discipline. This aligns closely with how scalable AI systems should be built, where reliability is embedded into the architecture itself. It also connects naturally with digital twins, where continuous data flow and lifecycle awareness are essential for generating meaningful insights. Overall, it shifts the perspective from simply building models to understanding and designing how systems evolve and operate over time.
