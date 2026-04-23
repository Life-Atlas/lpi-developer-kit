# Level 3 Submission — Praveen Singh
**Track A: Agent Builders**

## Agent: Deployment Strategy Agent (Digital Twin)

**Repo:** https://github.com/praveen-singh-007/lpi-life-agent

**Code:** https://github.com/praveen-singh-007/lpi-life-agent/agent.py

**A2A Card:** https://github.com/praveen-singh-007/lpi-life-agent/agent.json

---

## What It Does

I built a **constraint-aware deployment strategy agent** — not a generic digital twin explainer, but a system that generates **realistic implementation plans** based on the user’s constraints.

Instead of explaining what digital twins are, the agent answers:
> *“Given this use case and these constraints, what should we actually build?”*

The output changes significantly depending on the scenario.  
For example, a hospital with 2 developers and no cloud budget receives a minimal, phased deployment plan, while a larger organization would get a more scalable architecture.

---

### Inputs

- Use case (e.g. ICU patient monitoring)
- Constraints (e.g. 2 developers, 3 months, no cloud)

---

### Output (Structured Deployment Strategy)

1. **Recommended Architecture** — realistic, minimal solution based on constraints  
2. **SMILE Phases to Prioritize** — selected and justified per scenario  
3. **Key Risks** — grounded in insights and case context  
4. **What to Avoid** — what should NOT be done early  
5. **First 3 Actions** — concrete, actionable steps  
6. **Decision Reasoning** — clear data → reasoning → decision chain  

The agent is designed to behave like a **deployment consultant**, not a summarizer.

---

## Design Decisions

### Constraint-first design

Most digital twin discussions focus on what’s possible.  
I designed this agent to focus on:

> *What is feasible under constraints?*

This led to making **minimal viable twin (MVT)** a core concept in the output.

---

### Structured output over free-form text

Early versions produced generic answers.  
I enforced a fixed structure:

- Architecture  
- Phases  
- Risks  
- Avoid  
- Actions  
- Reasoning  

This significantly improved clarity and evaluation.

---

### Multi-tool reasoning

I used four tools to ensure grounding:

- `smile_overview` → methodology baseline  
- `get_insights` → scenario-specific reasoning  
- `get_case_studies` → real-world grounding  
- `query_knowledge` → supporting context  

Using fewer tools led to weaker reasoning and phase confusion.

---

### Hallucination control

Initial outputs included:
- invented technologies  
- irrelevant case studies  
- over-engineered systems  

To fix this, I enforced:

- use ONLY provided data  
- do NOT invent technologies or tools  
- ignore cross-domain examples  
- prefer minimal, realistic solutions  

---

### Relevance filtering

One key issue was the model applying unrelated case studies (e.g. energy systems in healthcare).

I added rules to:
- ignore mismatched domains  
- use only context-relevant data  

---

## LPI Tools Used

| Tool | Arguments | Purpose |
|------|-----------|---------|
| `smile_overview` | *(no args)* | Provides full SMILE methodology context |
| `get_insights` | `scenario: "{usecase}"` | Scenario-specific recommendations |
| `get_case_studies` | `query: "healthcare digital twin"` | Real-world grounding |
| `query_knowledge` | `query: "{usecase}"` | Supporting technical context |

---

## Sample Behavior (Real)

Input:
```
Use case: real-time patient monitoring digital twin in ICU

Constraints: 2 developers, 3 months, no cloud
```


Output highlights:

- Recommends **minimal viable twin (MVT)** instead of full system  
- Prioritizes **Reality Emulation + Concurrent Engineering**  
- Avoids complex integrations  
- Suggests phased rollout  

This shows the agent is reasoning against constraints, not just summarizing tools.

---

## Tech Stack

- Python 3.10+
- Ollama (local LLM — Qwen2.5)
- LPI MCP server (Node.js)
- JSON-RPC over subprocess
- Standard library + `requests`

---

## Run It

```bash
python agent.py
```

## Example Input
```
Real-Time Patient Monitoring Digital Twin in ICU

Project Details Developers: 2 Duration: 3 months Cloud Usage: No
```
## Design Decisions & Independent Thinking

**My Approach & Tool Selection Trade-offs:**

Instead of building a simple explanation agent, I designed a **constraint-aware decision agent**. The key issue I observed was that LLMs tend to generate generic or over-ideal solutions.

- *Trade-off:* I sacrificed flexibility in free-form outputs by enforcing a **strict structured response + grounding rules**. This ensured the agent produces **realistic, constraint-driven deployment strategies** instead of vague answers.

---

**Choices Made That Weren't In The Instructions:**

1. **Constraint-first reasoning design**  
   I made constraints (team size, timeline, infrastructure) the primary driver of decisions. This forces the agent to recommend **minimal viable solutions** rather than ideal architectures.

2. **Relevance filtering for tool outputs**  
   I added logic (via prompt rules) to ignore **cross-domain case studies**, preventing incorrect reasoning (e.g., energy systems applied to healthcare).

3. **Hallucination control rules**  
   I explicitly blocked:
   - invented technologies  
   - unsupported assumptions  
   This improves reliability and keeps outputs grounded in tool data.

4. **Expanded multi-tool reasoning (2 → 4 tools)**  
   I included:
   - `get_insights` for scenario reasoning  
   - `query_knowledge` for context  
   This improved decision quality compared to using only overview + case studies.

---





## What I'd Do Differently

The current system calls each tool using a new subprocess, which is simple but inefficient. A better design would:
- Maintain a persistent MCP connection
- Cache tool outputs (especially case studies)
- Reduce repeated calls

I would also add:
- Structured output validation (to detect hallucination)
- Automatic relevance filtering before passing data to the LLM
