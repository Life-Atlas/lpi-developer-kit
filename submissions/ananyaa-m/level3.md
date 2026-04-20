**Level 3 Submission — Ananyaa M**

---

GitHub Repository: https://github.com/ananyaa05/ananyaa-personal-twin-agent

---

**Project Overview**

    I have developed a Personal Twin Agent designed to balance my life as a 3rd-year CSE student. The agent uses a local LLM namely TinyLlama of Ollama, to act as a lifestyle task helper, helping me decide between technical tasks (C++, AWS, ML) and creative skills (baking, poetry) based on my current energy and mood.

---

**Implementation Details**

    1. Model: TinyLlama (Running locally via Ollama).
    I shifted from Llama 3 to TinyLlama to optimize for local system memory constraints.

    2. LPI Tools Integrated: -
    log_energy_level
    log_mood_state
    get_pending_tasks
    get_creative_log
    get_exercise_log

    3. Explainable AI (XAI): -
    The agent is designed for transparency. Every recommendation is preceded by raw JSON data and timestamps retrieved from the LPI tools before the LLM generates a response.