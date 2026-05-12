# Level 3 Submission

## Track
Agent Builders

## Agent Repository
https://github.com/devikahooda775/lpi-agent-devika

## What My Agent Does
My agent accepts a user query related to SMILE methodology or digital twins, queries multiple LPI tools to gather relevant information, and generates a structured, explainable answer using a local LLM (Ollama).

## LPI Tools Used
- smile_overview — to understand the overall SMILE framework
- query_knowledge — to retrieve detailed concepts and explanations
- get_case_studies — to provide real-world context and applications

## Explainability
The agent ensures explainability by explicitly including provenance in the output. It clearly lists which LPI tools were used and how each contributed to the final response, allowing the user to trace the reasoning process step by step.

## Example Run
Command:
python examples/agent.py "What is SMILE methodology?"

Output Summary:
The agent combined information from multiple LPI tools to explain the SMILE methodology, its phases, and real-world applications, while also citing the sources (tools) used to generate the answer.

## Key Design Choice
Instead of returning a simple response, I focused on making the agent explainable by integrating outputs from multiple tools and explicitly showing their contribution. This ensures transparency and aligns with the idea of explainable AI.