# Level 3 Submission - Suhani Sharma

## Tracks Selected
**Track A:** Agent Builders

**GitHub Repository:** https://github.com/SuhaniSharma1309/lpi-focus-agent 

## Project Name
Focus & Productivity Advisor (SMILE Agent)

## What the Agent Does
This agent helps users improve their focus and productivity based on their study habits and distractions.  
It takes user input (study time and main distraction) and generates a personalized, structured plan using the SMILE methodology.

## Tools Used
- `query_knowledge` — to retrieve relevant information about focus and distraction  
- `get_insights` — to generate practical productivity strategies  

## How It Works (Brief)
1. Takes user input (study time + distraction)  
2. Connects to the LPI MCP server  
3. Queries multiple LPI tools (`query_knowledge`, `get_insights`)  
4. Processes and combines the results  
5. Outputs:
   - Advice  
   - 3 actionable suggestions  
   - Sources (for explainability)  

