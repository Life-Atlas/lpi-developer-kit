# Level 3 Submission - Aman Gupta

## Project Name
SMILE Career Agent

## GitHub Repository
https://github.com/AmanGupta3995377/smile-career-agent

## Project Overview
I built a real AI agent that accepts a user question, connects to the LPI MCP server, queries multiple LPI tools, and generates a helpful explainable response using a local LLM through Ollama.

This project was created to demonstrate practical use of tool-calling, local AI models, and explainable outputs.

## What the Agent Does
- Accepts user input
- Connects to the LPI server
- Calls multiple LPI tools
- Uses returned knowledge to generate answers
- Shows which tools were used
- Gives explainable responses

## LPI Tools Used
1. smile_overview
2. query_knowledge
3. get_insights

## Technologies Used
- Python
- Node.js
- Ollama
- Requests library

## How to Run

```bash
python agent.py
```

## Example Question

How can I start using SMILE?

## Explainability

The final answer is generated using responses from LPI tools. The program clearly lists which tools were used so the user can trace where the information came from.

The linked repository has also been updated with stronger error handling and clearer source tracing based on reviewer feedback.

## What I Learned

I learned how real AI agents connect with tools, how subprocess communication works, how to use Ollama with Python, and how to build explainable AI systems.

## Future Improvements
- Better UI
- More tool integrations
- Save chat history
- Better personalization
