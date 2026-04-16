# Level 3 Submission — Ananyaa M

### **GitHub Repository**
https://github.com/ananyaa05/ananyaa-personal-twin-agent

### **LPI Tools Called**
The agent is hardcoded to orchestrate the following LPI tools:
* `log_energy_level`
* `log_mood_state`
* `get_pending_tasks`
* `get_creative_log`
* `get_exercise_log`

### **Setup Instructions**
To run this agent locally, follow these steps:
1. Ensure **Ollama** is installed and running.
2. Download the **TinyLlama** model: `ollama pull tinyllama`.
3. Clone the agent repository.
4. Run the agent using Python: `python agent.py`.

### **Explainability (Sample Trace)**
```text
USER INPUT: "I'm feeling drained after the Amity lab."

[TOOL CALLED] log_energy_level → {"value": 3, "unit": "score /10"}
[TOOL CALLED] log_mood_state → {"value": "exhausted"}

RECOMMENDATION:
"I recommend Rest. Because your log_energy_level is only 3, you need to recharge before tackling C++ homework."
```

### **Summary of the "Check"**
* **Logic:** 10/10 (Your tool registry and selection logic are perfect).
* **Explainability:** 5/10 (The AI needs to *cite* the tools in the final text).
* **Bot Visibility:** 4/10 (The bot is missing the tool names because they are inside a dictionary).

### **Explainability & Security**
The agent provides a full JSON trace for every recommendation to ensure explainability. It also includes input validation to prevent hallucination if LPI data is missing.