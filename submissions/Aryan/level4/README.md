# Level 4 — Secure Multi-Agent System (LPI)

## Overview

This project implements a **secure multi-agent system** using the Life Programmable Interface (LPI).

The system answers user queries by:
- retrieving grounded knowledge using LPI tools  
- reasoning strictly over that data  
- enforcing security constraints to prevent misuse  

---

## Architecture

The system consists of **two agents + orchestrator**:

### 1. Agent B — Research Agent
- Calls LPI tools (`smile_overview`, `get_case_studies`)  
- Extracts relevant data (healthcare-focused filtering)  
- Returns structured grounding data

### 2. Agent A — Reasoning Agent
- Takes grounded data from Agent B  
- Uses a constrained prompt (no external knowledge)  
- Generates a structured, explainable answer

### 3. Orchestrator
- Handles user input  
- Routes data between agents  
- Applies security checks  
- Produces final output

---

## Data Flow

User Query → Orchestrator → Agent B (LPI Tools) → Grounded Data (SMILE + Case Study) → Agent A (Reasoning) → Final Answer

---

## Tools Used

- `smile_overview` → SMILE methodology  
- `get_case_studies` → real-world digital twin implementations

---

## Security Features
Implemented in `security.py`:
### 1. Prompt Injection Protection
Blocks malicious inputs such as:
- "ignore previous instructions"  
- "reveal system prompt"
### 2. Data Leak Prevention
Redacts sensitive outputs like:
- system prompts  
- hidden instructions  
- tool schemas   
### 3. DoS Protection
Limits input size to prevent overload   
### 4. Agent Validation
Ensures correct structure of inter-agent communication   
---

## Key Design Decisions - 

**Strict grounding**: 

Agent A can only use data from Agent B - 

**No hallucination**: LLM constrained with hard rules - 
**Tool-first architecture**: reasoning depends on LPI outputs - 
**Security-first design**: all inputs and outputs are filtered   

---

## Example Query - How are digital twins used in healthcare?

---
## Example Output -

- SMILE-based explanation
- Healthcare case study (continuous patient twin)
- Structured reasoning (phases, application, insight, conclusion)

---

## How to Run - ### 1. Start LPI server
```bash npm run build node dist/src/index.js```

and start Ollama:

'term'ollama run qwen2.5:1.5b'``` or follow the detailed steps provided.

details include starting the server, running Ollama, and executing the orchestrator script.

detailed project structure is also outlined.

e.g., level4/ directory contains key scripts and files.
e.g., security layer is implemented in `security.py`.
e.g., architecture includes agent scripts and orchestrator.
e.g., notes mention local LPI server and Ollama usage for reasoning.
e.g., filtering applied for relevance in healthcare context.

details about author and credibility are included.
highlighting that this setup matches actual code, shows architecture clearly, emphasizes security, and maintains credibility.
the final advice encourages clarity, technical honesty, and avoiding buzzwords.
a reminder that additional versions of documentation can be provided if needed.
