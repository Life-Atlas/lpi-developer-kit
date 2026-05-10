# Level 3 Submission

## Name
Abhinav Chaudhary

## Agent Repository
https://github.com/abhichaudhary256-sudo/lpi-agent-abhinav.git

---

## Overview

I built an AI agent that connects to the LPI MCP server and answers user questions using real LPI tools.

The agent:
- Accepts a user question
- Selects tools using simple keyword-based logic
- Calls LPI tools via MCP (JSON-RPC over stdio)
- Combines tool outputs
- Produces a structured and explainable response

---

## LPI Tools Used

The agent queries real LPI tools:

- **smile_overview**  
  → Provides high-level SMILE methodology understanding  

- **query_knowledge**  
  → Retrieves detailed explanations based on the question  

- **get_case_studies** *(conditional)*  
  → Provides real-world examples when relevant  

These tools return structured text, which is combined into a final response.

---

## How the Agent Works

User Question  
→ Tool Selection (keyword logic)  
→ MCP Tool Calls (JSON-RPC)  
→ Extract tool responses  
→ Combine outputs  
→ Structured answer  

---

## Explainability

The agent ensures explainability by:

- Clearly listing which tools were used  
- Displaying outputs grouped by tool  
- Providing a combined summary  
- Avoiding hidden reasoning  

Each response includes:
- Reasoning (how many tools used)
- Combined Answer
- Sources (tool names)

---

## Design Choices

- Used **rule-based tool selection** instead of LLM planning  
  → keeps behavior predictable and easy to debug  

- Avoided external frameworks  
  → focused on understanding MCP and tool interaction  

- Built as a **single-file implementation**  
  → simpler and easier to maintain  

- Prioritized clarity over complexity  

---

## Error Handling

The agent handles:

- Empty user input  
- MCP server not found  
- Invalid or malformed tool responses  
- Missing data from tools  
- Unexpected runtime errors  

---

## What I Learned

- How MCP enables tool-based AI systems  
- How to combine outputs from multiple tools  
- Importance of explainability in agent design  
- How to build a simple but effective AI agent  

---

## Improvements

- Smarter tool selection logic  
- Better summarization of outputs  
- Add logging or visualization  

---

## ✅ Checklist

* [x] Built custom agent
* [x] Uses multiple tools
* [x] Structured output
* [x] Explainability included
* [x] Error handling added
* [x] Separate repo created

---
Signed-off-by: Abhinav Chaudhary
