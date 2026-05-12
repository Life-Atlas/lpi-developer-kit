# Level 3 Submission — Track A (AI Agent)

## Project Title
Smart Health Advisor Agent (SMILE Powered)

---

## Overview
This project implements an AI agent that provides structured and explainable health recommendations using LPI tools and the SMILE methodology.

The agent takes a user query, retrieves relevant knowledge using LPI tools, and generates actionable advice with clear reasoning.

---

## GitHub Repository
https://github.com/srishtigusainn/lpi-developer-kit

---

## Agent File
examples/health_agent.py

---

## How the Agent Works

1. User enters a health-related query  
2. The agent sends the query to the LPI system  
3. LPI tools return structured outputs  
4. The agent combines results  
5. A response is generated with reasoning  

---

## LPI Tool Usage (Explicit)

The agent uses the following LPI tools:

- **smile_overview**  
  → Returns structured explanation of the SMILE methodology, used to guide reasoning and system behavior.

- **query_knowledge**  
  → Returns relevant health insights such as sleep patterns, fatigue causes, and stress relationships.

- **get_case_studies**  
  → Provides contextual real-world examples that strengthen recommendations.

These tools are invoked through the LPI agent pipeline and combined to generate responses.

---

## Example Input
"I feel tired and not sleeping well"

---

## Example Output (Simplified)

Recommendations:
- Improve sleep duration (7–9 hours)
- Maintain consistent sleep schedule
- Increase hydration and nutrition
- Reduce stress triggers

---

## Explainability (Critical Requirement)

If a user asks:
> "Why did you recommend this?"

The agent explains:

- Poor sleep → leads to fatigue (from knowledge tool)
- Irregular routine → affects recovery
- Stress → impacts sleep quality

Each recommendation is directly linked to a cause derived from tool outputs.

The reasoning flow is:
**User Symptoms → Knowledge Retrieval → Cause Identification → Recommendations**

This ensures the agent is not a black box.

---

## Why This Is Useful

This agent provides:
- Structured reasoning instead of generic advice  
- Explainable recommendations  
- Practical real-world applicability  

---

## Key Design Decisions

- Built a wrapper agent instead of modifying core LPI system  
- Focused on health domain for clarity and relevance  
- Structured outputs into sections  
- Prioritized explainability over complexity  

---

## Future Improvements

- Integrate wearable data (real-time inputs)  
- Improve personalization  
- Display tool outputs more transparently  
- Connect with UI dashboard (Track C integration)  

---

Signed-off-by: Srishti Gusain
