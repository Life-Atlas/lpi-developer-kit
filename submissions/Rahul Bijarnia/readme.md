# Level 3 Agent — Rahul Bijarnia

## Description
This agent answers questions using LPI tools and provides explainable output.

## Features
- Uses 2 tools
- Combines outputs
- Explainable AI

## How to Run
python agent.py
## 🧑‍💻 Independent Development

This agent was built from scratch by Rahul Bijarnia.

- Designed custom LPI tools (tool1, tool2)
- Implemented agent logic manually (no copy-paste framework)
- Structured project independently
## 🧠 Agent Design

The agent follows a structured pipeline:

1. Accept user query
2. Send query to Tool 1 (documentation retrieval)
3. Send query to Tool 2 (example generation)
4. Combine both results
5. Generate final summarized answer
6. Provide explanation of tool usage

Architecture:

User Input → Tool 1 + Tool 2 → Processing → Final Answer + Explanation