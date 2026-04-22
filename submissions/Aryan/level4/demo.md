# Demo — Level 4 Secure Multi-Agent System (LPI)

## Objective

Demonstrate a secure multi-agent system that:
- Uses LPI tools for grounded data retrieval
- Performs constrained reasoning
- Prevents prompt injection and data leakage
- Produces structured, explainable answers

---

## System Components

### 1. Orchestrator
- Accepts user query
- Applies security checks
- Coordinates agents

### 2. Agent B (Research Agent)
- Calls LPI tools:
  - `smile_overview`
  - `get_case_studies`
- Extracts relevant data (healthcare-focused)
- Returns structured grounding data

### 3. Agent A (Reasoning Agent)
- Uses ONLY grounded data
- Applies strict rules (no hallucination)
- Generates structured answer

### 4. Security Layer
- Input sanitization
- Prompt injection blocking
- Data leak prevention
- Input length validation

---
# Demo Flow

### Step 1 — User Input
```text
How are digital twins used in healthcare?
```

### Step 2 — Security Validation

Input is checked for:
- Prompt injection patterns
- Excessive length

If malicious → request is blocked.

### Step 3 — Agent B (Research)

Tools Selected:
- smile_overview
- get_case_studies

Output:
- SMILE methodology data
- Healthcare case study (Continuous Patient Twin)

### Step 4 — Agent A (Reasoning)

Agent A receives:
- SMILE framework
- Healthcare case study

Enforced Constraints:
- No external knowledge
- No invented phases
- Only grounded reasoning

### Step 5 — Final Output
**Understanding:**
Digital twins are implemented using the SMILE methodology, which focuses on impact-driven lifecycle modeling.

**SMILE Phases:**
- Reality Emulation 
- Concurrent Engineering 
- Collective Intelligence 
- Contextual Intelligence 

**Real-World Application:**
*(Healthcare case study output here)*

**Insight:**
Connection between SMILE phases and real-world implementation.

**Conclusion:**
Short, grounded summary based on provided data.
