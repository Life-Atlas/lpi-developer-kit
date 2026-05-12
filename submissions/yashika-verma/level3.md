# Level 3 Submission — Yashika Verma

## Project: Study Weakness Analyzer Agent

## Repository
https://github.com/yayyyyshi/study-agent-lpi

---

## Overview

My approach was to build an AI agent that analyzes a student's weaknesses and suggests improvements. I decided to focus on study patterns because it directly connects to my digital twin idea.

The agent takes user input and processes it using LPI tools and a local LLM to generate a structured response.

---

## LPI Tool Usage

The agent queries multiple LPI tools to retrieve relevant data.

Example:

- Tool: smile_overview  
  Result: Retrieved structured overview of the SMILE methodology  

- Tool: query_knowledge  
  Response: Returned relevant concepts related to the user's input  

These outputs are then combined and passed to the LLM.

---

## Agent Processing

The agent processes the results from the tools and generates a response.

It explains recommendations **because** it analyzes weaknesses from both conceptual and practical perspectives. The agent chooses strategies based on the data retrieved from tools.

---

## Example Interaction

Input:
"I struggle with data structures, especially trees"

Output:
- Weakness: Lack of problem-solving practice
- Recommendation: Practice traversal algorithms
- Reason: Based on retrieved data from LPI tools

---

## Explainability (Detailed)

The agent does not just generate answers — it traces them back to tool outputs.

For example:
- Data from `smile_overview` provides structured learning methodology
- Data from `query_knowledge` retrieves topic-specific concepts

The agent uses this retrieved data to generate recommendations **because** it identifies gaps between conceptual understanding and application.

This ensures that every output is grounded in tool-derived knowledge rather than generic LLM responses.

---
## System Design Thinking

I considered multiple approaches before finalizing the design.

Initially, I used static responses, but I realized that this does not reflect real agent behavior. I decided to simulate tool execution using subprocess calls to better represent how agents interact with external systems.

This approach allows the agent to be extended easily:
- Replace subprocess with real API calls
- Add memory layer for user tracking
- Integrate additional tools without changing core logic

This makes the system modular and closer to production-ready architecture.


## Key Decisions

I chose to use a local LLM (llama3 via Ollama) because it provides good performance without relying on external APIs.

I also decided to simulate structured tool responses initially and then integrate them into the agent pipeline.

---

## Challenges

I faced issues with integrating local LLM execution and ensuring the correct data flow between tools and the model.

I tried different approaches but settled on a subprocess-based execution because it was the most reliable.

---

## Conclusion

This project demonstrates how an agent can combine tool-based knowledge retrieval with LLM reasoning to generate explainable outputs.