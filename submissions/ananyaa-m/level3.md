**Level 3 Submission — Ananyaa M**

GitHub Repository: https://github.com/ananyaa05/ananyaa-personal-twin-agent

**Project Overview**
I have developed a Personal Twin Agent designed to balance my life as a 3rd-year CSE student at Amity. The agent uses a local LLM (TinyLlama via Ollama) to act as a lifestyle task helper, deciding between technical tasks (C++, AWS, ML) and creative skills (baking, poetry) based on real-time data.

**LPI Tools Integrated**
The agent explicitly calls and orchestrates the following LPI tools to gather context:

`log_energy_level`

`log_mood_state`

`get_pending_tasks`

`get_creative_log`

`get_exercise_log`

**Implementation & Error Handling**
Local LLM: I shifted from Llama 3 to TinyLlama to optimize for local system memory constraints (2.3GB available RAM), ensuring low-latency reasoning on local hardware.

Error Handling: The agent includes input validation to handle "bad" or missing tool data. If a tool returns an error or empty JSON, the agent defaults to a safety-first recommendation (e.g., advising a break) to prevent AI hallucination.

**Explainable AI (XAI)**
The agent prioritizes transparency. Every recommendation is showing the raw JSON data and timestamps retrieved from the LPI tools. This ensures the user can audit the logic behind every AI suggestion.