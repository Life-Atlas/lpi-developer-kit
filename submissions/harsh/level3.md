# Level 3 Submission - Harsh Srivastava

## Project: Life Twin AI Agent

### What it does:
This agent takes user input and analyzes it using SMILE methodology to provide meaningful insights.

### Features:
- Accepts user question
- Uses SMILE methodology data
- Uses case study data
- Generates AI response using local LLM (Ollama)
- Shows sources used

### LPI Tools Used:
- smile_overview
- get_case_studies
- get_insights

### GitHub Repo:
https://github.com/Harshgithub321/lpi-life-twin-agents

### Setup Instructions:
1. Install dependencies using `pip install -r requirements.txt`
2. Run `ollama serve`
3. Run `python agent.py`

### Explainability:
The agent explains outputs by combining SMILE methodology and case studies, making responses transparent and understandable.

### Error Handling:
- Checks for empty input
- Handles invalid queries
- Uses try-except blocks to prevent crashes
- Returns meaningful error messages
