# How I Did It - Deployment Strategy Agent (Level 3)

## Approach

After Level 2, I decided to build a **decision-oriented agent** instead of a descriptive one.

The goal was simple:

```Given a use case and constraints, generate a realistic deployment strategy.```

I kept the implementation minimal and focused on:
- multi-tool reasoning
- constraint-aware output
- structured decision-making

---

## Key Decisions

### 1. Moving from explanation → decision agent

Instead of answering:
> “What are digital twins?”

I designed the agent to answer:
> “How should we build this under constraints?”

This required:
- structured outputs (architecture, risks, actions)
- justification of decisions

---

### 2. Expanding tool usage

Initial setup with 2 tools was not enough.

I moved to 4 tools:
- SMILE overview (methodology)
- Insights (scenario reasoning)
- Case studies (real grounding)
- Knowledge (context)

Decision:
> prioritize **multi-source grounding over simplicity**
---

### 3. Enforcing constraints as a core signal
Most LLM outputs ignore real-world limits.

I explicitly designed the agent to reason with:
- team size
- timeline
- infrastructure

Decision:
> treat constraints as **primary drivers**, not optional context"
---

### 4. Choosing structured output format
I forced the agent to always return:
- Architecture 
- SMILE phases 
- Risks 
- What to avoid 
- First actions 
- Decision reasoning 
Decision:
> structure improves both **quality and evaluation**
---
# Challenges Faced

### 1. MCP process failures
**Problem:**
- default: ValueError: I/O operation on closed file 
- description: Reusing subprocess after `.communicate()`
- decision: spawn a new process per tool call
- outcome: Stable multi-tool execution

---

### 2. Weak reasoning from small model
**Problem:**
t-shallow outputs, generic answers
**Decision:** upgrade from `qwen2.5:1.5b` to `qwen2.5:7b`
**Outcome:**
- better structure 
- improved reasoning 
- fewer errors

---

### 3. Hallucinated technologies
**Problem:**
tool introduced tools/tech not in data; outputs looked impressive but incorrect.
**Decision:**
- explicitly block:
  - invented technologies 
  - invented tools 
enforce “use only provided data”
**Outcome:** More reliable outputs.

---

### 4. Irrelevant case study usage
**Problem:**
e.g., model used unrelated domains (e.g., heating systems for healthcare).
**Decision:**
- add relevance filtering:
  - ignore cross-domain examples 
  - only use context-matching data.
**Outcome:** Improved correctness and credibility.

---

### 5. Over-engineered solutions
**Problem:**
del suggested complex systems despite tight constraints.
**Decision:**
- enforce:
  - minimal viable twin (MVT)
  - “simplest possible architecture”.
**Outcome:** Realistic, implementable strategies.

---

### 6. Prompt instability
**Problem:**
e.g., too strict → empty/generic output; too loose → hallucinations.
**Decision:**
balance:
- strict grounding rules 
and flexible reasoning.
**Outcome:** Consistent, high-quality outputs.

## What I Learned
### 1. Prompt design > code
Most improvements came from:

highlighting:- refining instructions, enforcing constraints, guiding structure.
---
### 2. Constraints improve intelligence

Without constraints:
general answers.

With constraints:
appropriate, practical answers.
---
day-to-day learning about the importance of grounding and relevance in AI systems is crucial for reliable performance and trustworthy outputs.
