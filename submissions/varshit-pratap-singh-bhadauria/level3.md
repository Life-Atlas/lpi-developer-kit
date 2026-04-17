# Level 3 Submission — Digital Twin Advisor Agent

## GitHub Repository

https://github.com/temporalzone/lpi-level3-agent

---

## Overview

For Level 3, I built a Digital Twin Advisor Agent that connects to the Life-Atlas LPI using the MCP protocol. The agent helps users understand and apply the SMILE methodology to real-world systems such as businesses, offices, and personal use cases.

---

## What the Agent Does

The agent takes a user query and:

1. Connects to the LPI MCP server
2. Calls multiple LPI tools to gather relevant knowledge
3. Processes and combines the information
4. Generates a structured and explainable response

---

## LPI Tools Used

* **query_knowledge**
  Used to retrieve general insights related to the user’s question

* **smile_phase_detail**
  Used to extract detailed information about a specific SMILE phase

* **smile_overview**
  Used to provide a complete understanding of the SMILE methodology

---

## Key Features

* Multi-tool integration (uses 3 LPI tools)
* Dynamic phase detection based on user query
* Explainable AI with clear source attribution
* Local LLM integration using Ollama
* Fallback mode if LLM is not available
* Optional Flask-based web interface

---

## How It Works

1. The user inputs a question
2. The agent queries multiple LPI tools via MCP
3. The results are combined into a structured prompt
4. The LLM generates a final answer with proper citations
5. The output includes both the answer and source traceability

---

## Explainability

The agent ensures that every response includes clear references to the tools used. This allows the user to trace where each piece of information came from, making the system transparent and trustworthy.

---

## What I Learned

* How MCP protocol works for tool-based AI agents
* How to integrate multiple tools into a single workflow
* Importance of explainable AI
* How to use local LLMs (Ollama) in real projects
* How to design a structured agent pipeline

---

## Notes

This submission is an improved version with:

* Better structure
* Dynamic logic
* Enhanced explainability

The agent is designed to be practical, modular, and aligned with real-world AI system design.
