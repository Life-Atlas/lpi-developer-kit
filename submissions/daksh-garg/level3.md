# Level 3 Submission - Daksh Garg

## Project: Life Optimization Agent (LPI)

**Repository:** https://github.com/thedgarg31/lpi-life-agent

### Description
An explainable AI system that helps users analyze personal productivity, stress, and focus issues using SMILE methodology and LPI tools. This agent focuses on applying SMILE methodology to real-world human problems like productivity and mental clarity, instead of generic queries.

### Key Features
- **Real-World Application**: Analyzes personal challenges like "I feel stressed and distracted"
- **Explainable AI**: Every analysis cites exactly which LPI tools provided which insights
- **Structured Output**: Consistent Problem/Analysis/Suggestions format
- **Robust Error Handling**: Graceful fallbacks when MCP server or Ollama fail
- **Intelligent Processing**: Extracts and summarizes insights from raw tool outputs

### LPI Tools Used
1. **query_knowledge** - Searches for relevant patterns and research
2. **get_insights** - Provides scenario-specific implementation advice

### Technical Architecture
- **Language**: Python 3.10+
- **LLM**: Local Ollama with qwen2.5:1.5b model
- **Protocol**: MCP (Model Context Protocol) for LPI server communication
- **Error Handling**: Comprehensive error handling for all system components

### Example Usage
```bash
python agent.py "I feel unproductive and distracted"
```

### Sample Output
```
============================================================
  LIFE OPTIMIZATION ANALYSIS
============================================================

Problem:
You're experiencing productivity challenges and difficulty maintaining focus...

Analysis:
Applying SMILE methodology to your productivity challenge reveals several systemic patterns...

Suggestions:
1. Implement a 2-hour focus block system...
2. Track your distraction sources for one week...
3. Design your environment for success...
4. Establish a morning routine...

Sources:
[Tool 1: query_knowledge] -> productivity_and_focus_patterns
[Tool 2: get_insights] -> systemic_patterns
```

### What Makes This Unique
- Applies SMILE methodology to human problems, not just technical systems
- Uses real LPI tools instead of static knowledge bases
- Provides explainable AI with clear source attribution
- Focuses on actionable, practical advice for personal optimization

### Files in Repository
- `agent.py` - Main agent implementation
- `README.md` - Complete documentation and usage guide
- `HOW_I_DID_IT.md` - Development story and lessons learned
- `requirements.txt` - Python dependencies

### Testing Results
Successfully tested with input: "I feel stressed and distracted"
- Agent initialized properly
- LPI tools queried successfully
- Error handling worked (Ollama connection issue handled gracefully)
- Structured output maintained even in fallback mode

This agent demonstrates practical application of SMILE methodology to real human challenges, with robust engineering and explainable AI principles.
