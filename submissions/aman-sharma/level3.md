# Level 3 Submission

## Agent Repo
https://github.com/amansharmabrb-maker/lpi-mission-agent

## Description
Built a mission-style AI agent designed to simulate how real-world decision-support systems operate using the LPI toolkit. The agent takes a user query and transforms it into a structured “mission briefing” by combining knowledge retrieval, scenario-based insights, and actionable methodology steps.


## What the Agent Does
- Accepts a user-defined problem or scenario  
- Retrieves foundational knowledge using LPI tools  
- Generates contextual insights based on the scenario  
- Produces a step-by-step action plan using the SMILE methodology    

## Key Features
- **Multi-tool integration**: Combines multiple LPI tools in a single workflow  
- **Explainability**: Clearly shows which tools were used and why  
- **Structured output**: Presents results in sections (Objective, Intel, Insights, Action Plan)   
- **User-friendly interface**: Mission-style format for better readability  

## Tools Used
- `query_knowledge` – retrieves foundational information  
- `get_insights` – provides scenario-specific insights  
- `get_methodology_step` – generates implementation steps using SMILE  

## How to Run
python agent.py
