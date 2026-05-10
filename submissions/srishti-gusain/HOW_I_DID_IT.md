# HOW_I_DID_IT — Track A Level 3

## Objective
To build a Smart Health Advisor Agent that uses LPI tools to generate structured, explainable health recommendations.

---

## Approach

Instead of modifying the core LPI agent, I created a wrapper agent (`health_agent.py`) that:

1. Accepts a user query
2. Calls the existing LPI agent system
3. Retrieves structured outputs from multiple tools
4. Formats them into a readable and explainable response

This allowed me to reuse the LPI ecosystem while focusing on reasoning and explainability.

---

## LPI Tools Used

### 1. smile_overview
- Provides structured understanding of the SMILE methodology
- Helps frame the reasoning process

### 2. query_knowledge
- Retrieves relevant health-related insights (sleep, fatigue, stress)

### 3. get_case_studies
- Adds contextual examples to strengthen recommendations

---

## How the Agent Works

1. User inputs a query  
   Example: "I feel tired and not sleeping well"

2. Agent sends query to LPI system

3. LPI tools return:
   - Knowledge insights
   - SMILE framework context
   - Case-based reasoning

4. Agent combines outputs and generates:
   - Recommendations
   - Structured explanation

---

## Explainability (IMPORTANT)

If a user asks:
> "Why did you recommend this?"

The agent explains:

- Poor sleep → linked to fatigue (from knowledge tool)
- Nutrition imbalance → contributes to low energy
- Stress → affects recovery and sleep

The agent clearly connects:
**symptoms → causes → recommendations**

This ensures the output is not a black box.

---

## Key Design Decisions

- Used a wrapper instead of modifying core agent → safer and modular
- Focused on health domain → practical and relatable
- Structured output into sections → improves readability
- Added explicit reasoning → improves trust

---

## Challenges Faced

- Understanding how LPI tools interact
- Structuring output clearly
- Making explanations meaningful instead of generic

---

## What I Would Improve

- Add real-time data (wearables, APIs)
- Personalize recommendations
- Show tool outputs more transparently
- Integrate UI (already explored in Track C)

---

## Conclusion

This agent demonstrates:
- Tool-based reasoning
- Explainability
- Structured output generation

Rather than just answering queries, it explains *why* the answer makes sense.
