# Level 3 — Rahul Bijarnia

## Repository Link
https://github.com/RahulBijarnia1/lpi-level3-agent

## Overview
I built an AI agent that connects to the LPI sandbox and generates useful, explainable answers by combining multiple tools with a local LLM.

## What I Built
The agent takes a user query and processes it by calling multiple LPI tools. Instead of relying on a single response, it gathers structured data from different sources and combines them to generate a final answer.

## Tools Used and Their Role
- **smile_overview**  
  Provides the SMILE methodology, which gives structured context for understanding the problem.

- **query_knowledge**  
  Returns domain-specific knowledge related to the user query.

- **get_case_studies**  
  Provides real-world examples showing how the concept is applied.

## How the Agent Works (Step-by-Step)
1. The user enters a query through the command line  
2. The agent calls multiple LPI tools:
   - smile_overview  
   - query_knowledge  
   - get_case_studies  
3. Each tool returns structured information  
4. The agent combines all responses into a single prompt  
5. The combined data is sent to a local LLM (Ollama)  
6. The LLM generates a clear and summarized final answer  

## Explainability (How the Answer is Generated)

The agent ensures explainability by clearly separating outputs from each LPI tool and showing how they contribute to the final answer.

### Step-by-step explanation:

1. **SMILE Overview (smile_overview)**
   - Provides the conceptual framework and methodology  
   - Helps understand the structure of the problem  

2. **Knowledge (query_knowledge)**
   - Provides factual and domain-specific information related to the query  

3. **Case Studies (get_case_studies)**
   - Provides real-world examples where the concept is applied  

4. **Final Answer Generation**
   - All the above outputs are combined  
   - Sent to the LLM (Ollama)  
   - The LLM generates a final explanation using ALL sources  

## Example Flow
Input:
python agent.py "What are digital twins in healthcare?"

This makes the system fully explainable because the user can clearly see:
- Which tool contributed what  
- How the final answer was constructed  
- That the response is not generated blindly by the LLM

Output:
- SMILE overview  
- Knowledge explanation  
- Case studies  
- Final combined answer  

## How to Run
pip install -r requirements.txt  
python agent.py "your query"

## Notes
- Uses at least 2 LPI tools (actually 3)  
- Combines structured tool data with LLM output  
- Focuses on explainable AI rather than just generating answers  
