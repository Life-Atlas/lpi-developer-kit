# HOW_I_DID_IT.md

## Overview

For my Level 3 submission, I built a Digital Twin Advisor Agent that connects to the Life-Atlas LPI (Life Programmable Interface) using the MCP protocol. The goal of my agent is to help users understand and apply the SMILE methodology to real-world systems like offices, businesses, or personal use cases.

---

## Step-by-Step Process

### 1. Setting up the LPI sandbox

I started by forking and cloning the LPI Developer Kit repository. Then I installed dependencies using:

npm install
npm run build
npm run test-client

At first, I faced some issues with Node version compatibility, but after updating to Node 18+, all 7 tools passed successfully.

---

### 2. Understanding how MCP works

Initially, I didn’t fully understand how MCP (Model Context Protocol) works. After reading the documentation and exploring the example agent, I learned that:

* The agent communicates with the LPI server using JSON-RPC
* Tools are called using structured requests like `tools/call`
* The server returns structured responses that must be parsed

This helped me design my agent to interact properly with the LPI tools.

---

### 3. Building the agent (agent.py)

I created a Python-based agent that:

* Starts the LPI server using subprocess
* Initializes MCP communication (handshake + notifications)
* Calls multiple LPI tools dynamically

Initially, I was only using one tool, but later I improved it to use:

* `query_knowledge` → for general insights
* `smile_phase_detail` → for specific phase understanding
* `smile_overview` → for full methodology context

This made the agent much more complete and useful.

---

### 4. Adding intelligence to the agent

In my first version, the agent used a fixed SMILE phase. I realized this was not very smart.

So I added a simple logic to detect the relevant phase based on the user’s question. For example:

* Questions about data → Phase 2
* Questions about modeling → Phase 3
* Default → Phase 1

This made the agent more dynamic and closer to a real assistant.

---

### 5. Integrating LLM (Ollama)

I connected my agent to a local LLM using Ollama. The model I used was:

qwen2.5:1.5b

The LLM is responsible for:

* Combining outputs from multiple tools
* Generating a structured answer

I also added a fallback mode in case the LLM is not running, so the agent still works without breaking.

---

### 6. Ensuring explainability (important part)

One major improvement I made was enforcing explainability.

I modified the prompt so that:

* Every part of the answer includes a source
* The format clearly shows which tool provided which information

This ensures that the output is transparent and traceable, which is an important requirement of the project.

---

### 7. Building a Flask interface (app.py)

To make the agent more usable, I created a simple Flask web interface.

Features:

* Input field for user questions
* API endpoint `/api/query`
* Returns structured JSON responses
* Proper error handling

This made the project feel like a real application instead of just a script.

---

## Challenges I Faced

### 1. MCP communication errors

At first, I was getting no response from the server. This happened because:

* The initialization step was missing
* JSON-RPC format was slightly incorrect

I fixed it by carefully following the MCP protocol structure.

---

### 2. LLM not responding

Sometimes Ollama was not running, which caused failures.
To solve this, I added a fallback system so the agent still returns useful output.

---

### 3. Making the agent “smart”

Initially, my agent was too static. It didn’t adapt to the user’s question.

I improved this by:

* Adding phase detection logic
* Using multiple tools instead of one

---

## What I Learned

* How MCP works and how agents call tools
* How to integrate a local LLM (Ollama)
* Importance of explainable AI
* How to design a simple AI agent architecture
* How to handle failures and edge cases

---

## Final Thoughts

This project helped me understand how real-world AI agents are built. Instead of just generating text, the agent now:

* Retrieves structured knowledge
* Combines multiple sources
* Explains its reasoning

If I had more time, I would improve:

* Better phase detection using NLP
* UI improvements
* More advanced reasoning between tools

Overall, this was a great learning experience and gave me practical exposure to building AI agents.
