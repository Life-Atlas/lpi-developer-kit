## Level 3 Submission

Agent Repo:
https://github.com/abhishekverma2323/lpi-smile-agent

Description:
Built an explainable AI agent that queries multiple LPI tools (smile_overview, query_knowledge, get_insights) and generates answers using a local LLM.

## Setup Instructions

1. Clone the LPI developer kit:
git clone https://github.com/Life-Atlas/lpi-developer-kit.git

2. Install dependencies:
cd lpi-developer-kit
npm install
npm run build

3. Install Python dependency:
pip install requests

4. Start Ollama:
ollama serve

5. Pull model:
ollama pull qwen2.5:0.5b

6. Run the agent:
python my-agent.py "What is SMILE methodology?"

## Explainability

The agent lists which tools were used (smile_overview, query_knowledge, get_insights) to ensure transparency and reduce hallucination.

## Error Handling

The agent includes basic error handling:

- Handles missing or invalid inputs by defaulting to general SMILE queries
- Detects connection issues with Ollama and returns an error message
- Prevents hallucination by restricting responses to tool-based data
- Uses timeout handling to avoid infinite waits from the local LLM