# LPI Level 3 Agent

## Overview
This agent connects to LPI tools and generates explainable answers using multiple data sources and a local LLM.

## Tools Used
- smile_overview
- query_knowledge
- get_case_studies

## Example
python agent.py "What are digital twins in healthcare?"

## How it Works
- Takes user input
- Calls multiple LPI tools
- Combines results
- Uses LLM to generate final answer

## How to Run
pip install requests
python agent.py "your query"
