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

# How to Run

## 1. Start LPI Server
```bash
npm run build
node dist/src/index.js
```

## 2. Start Ollama
Run the following command:
```
ollama run qwen2.5:1.5b
```
Or follow the detailed steps provided.

---

### Details include:
- Starting the server, running Ollama, and executing the orchestrator script.
- The project structure is outlined:
  - `level4/` directory contains key scripts and files.
  - Security layer is implemented in `security.py`.
  - Architecture includes agent scripts and orchestrator.
- Notes mention:
  - Use of local LPI server and Ollama for reasoning.
  - Filtering applied for relevance in healthcare context.
- Additional information about author and credibility:
  - Setup matches actual code, clearly shows architecture, emphasizes security, and maintains credibility.

### Final Advice:
- Encourage clarity, technical honesty, and avoiding buzzwords.
- A reminder that additional versions of documentation can be provided if needed.
