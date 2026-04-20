# Level 3 Submission — Vusala Akanksha

## Agent Repository
https://github.com/Chutki319239/lpi-smile-agent

## What my agent does
I developed an AI agent in Python that uses the Model Context Protocol (MCP) to connect to the LifeAtlas Platform Interface (LPI). After receiving a user query, the agent contacts two LPI tools, analyzes the answers, and outputs structured data with obvious source attribution.
The agent's objective is to deliver real-world examples and knowledge insights in a traceable and comprehensible manner.

## Tools used
1. `query_knowledge`
   - Utilized to obtain organized information pertaining to the user's inquiry.
   - Provides pertinent information from the LPI knowledge base.
2. `get_case_studies`  
   - Used to retrieve practical examples and real-world applications.
   - Provides relevant case study data.
In order to deliver a more comprehensive and relevant response, the agent integrates the outcomes from both technologies.

## How it works
After getting the user input : 
From each tool's JSON answer, the agent retrieves the appropriate text.
It divides the output into:
 - Knowledge-Based Insights
 - Case Studies
 - Sources Consulted
The response is formatted in a legible and organized manner.
There was no use of external LLM frameworks. To gain a deeper understanding of MCP-based integration, response handling and tool orchestration were manually created.

## Explainability
Explainability is put into practice by:
A detailed list of the LPI tools utilized.
Including organized sections that distinguish between case studies and knowledge.
Each insight's source (the tool that produced it) should be displayed.

If a user queries:  
"What made you suggest this?"
The agent is able to demonstrate:Which instrument produced the data?
The particular text that the LPI tool returned.
How the final structured output was produced using the text.

This guarantees transparency and traceability in the response's construction.

## Architecture Decisions
Python was utilized for processing and orchestration.
MCP tool calls were handled by a Node.js wrapper.
Higher-level frameworks were replaced with subprocess communication.
In order to concentrate on direct MCP interaction, the system was purposefully constructed without external LLM abstractions.

