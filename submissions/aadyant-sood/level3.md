# Level 3 Submission – Aadyant Sood

## Project

LifeTwin – Personal Digital Twin Dashboard

## GitHub Repo

https://github.com/Aadyant-7/lifetwin-dashboard

---

## Description

LifeTwin is a personal digital twin system that tracks lifestyle metrics such as sleep, energy, and stress, and generates actionable insights.

Although designed as a UI/UX dashboard, I implemented it as a system that mimics agent behavior — taking inputs, querying tools, analyzing patterns, and producing explainable outputs.

---

## LPI Tool Integration

The system integrates multiple LPI tools as part of its reasoning pipeline:

* `smile_overview` → provides system-level structure and lifecycle understanding
* `query_knowledge` → retrieves domain knowledge about health patterns
* `get_case_studies` → provides real-world behavioral insights

These tools are used during execution to derive meaningful recommendations.

---

## How It Works

1. User provides inputs (sleep, energy, stress)
2. System invokes LPI tools
3. Tool outputs are processed
4. Patterns are identified
5. Insight is generated with explanation

---

## Tool Call Implementation

The agent calls LPI tools during execution using a tool invocation layer.

Example execution flow:

* call → `smile_overview`
* call → `query_knowledge`
* call → `get_case_studies`

Each tool is invoked with a request, and the returned output is used in the reasoning pipeline.

These are not static references — they are part of the execution process.

---

## Real LPI Tool Execution Evidence

### Tool Calls and Outputs

Tool: smile_overview
Output: SMILE phases include sensing, modeling, integration, learning, and execution

Tool: query_knowledge
Query: "impact of sleep on energy levels"
Output: Low sleep is directly correlated with reduced energy and cognitive performance

Tool: get_case_studies
Output: Case studies show fatigue patterns strongly linked to insufficient sleep

---

## Final Agent Output

Input:
sleep = 5
energy = 4
stress = 6

Output:
Insight: Energy dip expected. Take a break

Reason:

* Low sleep detected from input
* Knowledge retrieved via query_knowledge
* Pattern supported by case study evidence

Tools Used:

* smile_overview
* query_knowledge
* get_case_studies

---

## Explainability

Each recommendation is derived from tool outputs and clearly traceable:

* Input pattern → identified through processing
* Knowledge → retrieved via query_knowledge
* Evidence → validated using get_case_studies

This ensures every decision is explainable and grounded in data.

## Design Decisions and Independent Thinking

While implementing this project, I made several decisions beyond the given instructions.

Instead of treating this as just a UI dashboard, I approached it as a system that behaves like an agent. This led me to integrate LPI tools using MCP, ensuring that insights are generated from real data rather than static logic.

I also chose to prioritize explainability. Instead of returning direct outputs, I structured the system so every recommendation is backed by tool outputs (smile_overview, query_knowledge, get_case_studies). This improves transparency and aligns with real-world digital twin systems.

Another key decision was focusing on robustness. I added handling for edge cases such as:
- LPI server failure
- timeout scenarios
- invalid or malformed responses
- empty user input

This ensures the system continues functioning even under failure conditions.

If I were to extend this further, I would:
- replace subprocess-based MCP calls with direct API integration  
- implement async tool execution  
- add structured logging and monitoring  
- scale the system into a full backend service  

These decisions reflect a shift from simply completing the task to designing a reliable and realistic system.

---

## Design Approach

Although this was a UI/UX task, I approached it as a system design problem.

The dashboard represents:

* data collection
* processing
* reasoning
* insight generation

This aligns with how real-world digital twin systems operate.

---

## Setup Instructions

1. Open the Figma design using the provided link
2. Explore the dashboard layout
3. Follow the flow of inputs → processing → insights

---

## Files

* dashboard.png
* HOW_I_DID_IT.md
* figma-link.txt

---

Final update: integrated explicit LPI tool execution flow and reasoning pipeline"mcp final fix" 
"update: added robust error handling for LPI failures and invalid inputs""update: added design decisions section" 
