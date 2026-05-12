# Level 3 Submission - Harsh Srivastava

## Project: Life Twin AI Agent

### What it does:
This agent takes user input and analyzes it using SMILE methodology to provide meaningful insights.

### Features:
- Accepts user question
- Uses SMILE methodology data
- Uses insights from LPI tools
- Generates AI response using local LLM (Ollama)
- Shows sources used

### LPI Tools Used:
- smile_overview
- get_insights

### GitHub Repo:
https://github.com/Harshgithub321/lpi-life-twin-agents

### Setup Instructions:
1. Install dependencies
2. Run ollama serve
3. Run python agent.py

### Explainability:
The agent explains outputs using SMILE methodology and insights, making the reasoning clear.

### Error Handling:
- Handles empty input
- Uses try-except blocks
- Prevents crashes on invalid input