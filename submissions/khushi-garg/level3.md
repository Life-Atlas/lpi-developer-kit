# Level 3 — AI Agent Submission

## GitHub Repo

https://github.com/g-khushi/lpi-agent-smile-advisor

## Objective

Built an AI agent that connects to the LPI sandbox and generates explainable responses using multiple tools and a local LLM.

## LPI Tools Used

1. smile_overview  
Returned an overview of SMILE methodology including its phases and principles.

2. query_knowledge  
Returned detailed knowledge about digital twins in healthcare including their purpose and benefits.

3. get_case_studies  
Returned real-world case studies demonstrating how SMILE is applied in different domains.

## Example Execution

Input:
"What are digital twins in healthcare?"

Output:
The agent retrieved:
- SMILE overview  
- Knowledge base results  
- Case studies  

Then passed the combined data to the LLM (Ollama), which generated a structured and explainable answer.

## Explanation

The agent first queries multiple LPI tools to gather structured data.  
This data is then sent to the LLM, which synthesizes the information into a final response with sources.  

This ensures both factual grounding and explainability.

## Conclusion

The agent successfully integrates multiple LPI tools and produces meaningful, explainable responses using an LLM.
