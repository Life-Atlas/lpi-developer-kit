\# Level 3 Submission



\## Agent Name

LPI-Powered Research Agent



\## GitHub Repository

https://github.com/Na7neet/level3-agent



\## What it does

This agent performs structured research on a user-provided topic by combining foundational knowledge and recent academic research.



It queries two tools:

\- Wikipedia → for background knowledge

\- arXiv → for recent scientific papers



The results are then synthesised using an LLM to produce a structured research report with proper citations.



\## Tools used

\- query\_knowledge (implemented using Wikipedia API)

\- get\_insights (implemented using arXiv API)



\## How it works

1\. Takes a user topic as input

2\. Calls Wikipedia API for foundational understanding

3\. Calls arXiv API for recent research papers

4\. Displays explainability (why each tool was used)

5\. Sends structured data to an LLM

6\. Generates a cited research report



\## Explainability

The agent explicitly explains:

\- Why Wikipedia was used (baseline knowledge)

\- Why arXiv was used (recent research)

\- How both outputs are combined

\- What decision steps were taken



\## Example

Input: personal health digital twin  

Output:  

\- Wikipedia summary  

\- Research papers  

\- Structured report with citations  

\- Explanation of reasoning

