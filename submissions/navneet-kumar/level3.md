\# Level 3 Submission (v2)



\## Agent Name

LPI-Powered Research Agent



\## GitHub Repository

https://github.com/Na7neet/level3-agent



\## What it does

This agent performs structured research on a user-provided topic by combining knowledge, insights, and real-world examples using LPI tools.



\## LPI Tools Used



The agent directly queries the following LPI MCP tools:



\- smile\_overview → provides foundational SMILE methodology context  

\- query\_knowledge → retrieves topic-specific knowledge from the LPI knowledge base  

\- get\_case\_studies → provides real-world examples and supporting evidence  



These tools are accessed via the LPI MCP server using JSON-RPC and their outputs are combined for final reasoning.



\## How it works

1\. Takes a user question as input  

2\. Queries multiple LPI tools (smile\_overview, query\_knowledge, get\_case\_studies)  

3\. Collects structured outputs from each tool  

4\. Displays explainability (why each tool was used)  

5\. Sends combined context to a local LLM (Ollama)  

6\. Generates a structured, cited response  



\## Explainability

The agent explicitly explains:

\- Why each LPI tool was used  

\- What data was retrieved from each tool  

\- How the outputs were combined  

\- How the final answer was generated  



\## Example

Input: personal health digital twin  



Output:

\- SMILE methodology context  

\- Knowledge base results  

\- Case studies  

\- Structured answer with explanation and sources  

