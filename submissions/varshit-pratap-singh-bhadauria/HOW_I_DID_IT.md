# Level 2 Submission — Varshit Pratap Singh Bhadauria

## What I Did

### Step 1: Ran LPI Sandbox
Command: npm run test-client

Output:
=== LPI Sandbox Test Client ===
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

### Step 2: Installed Ollama and ran local LLM
Model used: qwen2.5:1.5b

Command: ollama run qwen2.5:1.5b "What is the SMILE methodology in digital twins?"

LLM Output:
The SMILE methodology stands for Simulation, Model, Input, Output, 
Execution — used in digital twin development to help organizations 
gain insight into their systems. It involves simulation, modeling, 
input identification, output generation, and execution of real-world 
scenarios.

### Step 3: What I Learned

1. The local LLM incorrectly expanded SMILE as "Simulation, Model, 
Input, Output, Execution" — showing that general-purpose models 
hallucinate domain-specific knowledge about digital twins.

2. The actual SMILE methodology (Sustainable Methodology for Impact 
Lifecycle Enablement) focuses on 6 structured phases for building 
digital twins — which the LPI tools explained far more accurately.

3. This proved why grounding AI agents with domain-specific tools 
like LPI is critical — LLMs alone cannot be trusted for specialized 
digital twin knowledge without retrieval-augmented context.

## Problems I Hit
- Ollama was already running in background when I tried ollama serve 
  — got a port conflict error. Solved by directly running ollama run.

## Model Choice
Used qwen2.5:1.5b — lightweight model that runs locally without GPU.