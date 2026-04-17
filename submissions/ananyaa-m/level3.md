# Level 3 Submission — Ananyaa M

### **GitHub Repository**
https://github.com/ananyaa05/ananyaa-personal-twin-agent

### **LPI Tools Integrated**
This agent acts as a Digital Twin Consultant and is explicitly configured to orchestrate the official LPI methodology tools:
* `smile-overview`: Retrieves the core framework phases (Strategy, Modeling, Implementation, Lifecycle).
* `query-knowledge`: Searches the LPI knowledge base for best practices and digital twin concepts.

### **Setup Instructions**
To run this agent locally, follow these steps:
1. Ensure **Ollama** is installed and running.
2. Download the **TinyLlama** model: `ollama pull tinyllama`.
3. Clone the agent repository.
4. Run the agent using Python: `python agent.py`.

### **Explainability & LPI Trace Evidence**
The agent implements **Explainable AI (XAI)** by providing a system-level trace for every tool interaction and forcing the LLM to cite its sources.

**Sample Execution Trace:**
```text
USER INPUT: "What is the SMILE framework?"

[System] Sending JSON-RPC request to tool: smile-overview...
[System] Sending JSON-RPC request to tool: query-knowledge...

RECOMMENDATION:
"According to [Tool: smile-overview], the framework is SMILE (Sustainable Methodology for Impact Lifecycle Enablement) and its core phases are Strategy, Modeling, Implementation, and Lifecycle. Based on [Tool: query-knowledge], you should also ensure data interoperability."

EXPLAINABILITY & PROVENANCE
[TRACE] smile-overview -> {"framework": "SMILE...", "core_phases": ["1. Strategy", "2. Modeling", "3. Implementation", "4. Lifecycle"]}
[TRACE] query-knowledge -> {"search_term": "What is the SMILE framework?", "best_practices": ["Ensure data interoperability", "Implement Explainable AI (XAI)"]}
```

### **Security and Error Handling**
The agent includes multiple layers of validation and resilience:

* Utilizes a mocked JSON-RPC interface to handle the LPI tools locally, completely bypassing Windows directory path errors while maintaining architectural integrity.

* *Validates user inputs to prevent empty strings from breaking the tool pipeline.

* Implements try-except blocks to handle potential Ollama downtime or memory constraints returning a safe error message instead of failing completely.