# Level 3 Submission — Touqeer Hamdani

## Agent Repository

https://github.com/TouqeerHamdani/lpi-smile-agent

## What My Agent Does

The LPI SMILE Agent is a digital twin methodology advisor that connects to the LPI MCP server, queries multiple tools to gather context, and uses a local LLM via Ollama to produce explainable answers with full source provenance. My approach was to build something that not only retrieves data but explains where every piece of information came from — because explainability is a core requirement, not just a feature.

The agent works in a 3-phase pipeline:

1. **Connect** — Starts the LPI MCP server as a subprocess and performs the JSON-RPC initialization handshake
2. **Gather** — Queries 4 LPI tools to build a comprehensive context:
   - `smile_overview` — retrieves the full SMILE methodology overview
   - `query_knowledge` — searches the knowledge base with the user's question, returning relevant entries
   - `get_case_studies` — fetches real-world digital twin case studies across industries
   - `get_insights` — gets scenario-specific implementation advice based on the user's question
3. **Reason** — Builds a provenance-aware prompt with all retrieved data and sends it to a local LLM (Ollama). The prompt instructs the model to cite which tool (Tool 1-4) each part of the answer came from.

## How It Works Technically

The agent uses `subprocess.Popen` to start the LPI MCP server (`node dist/src/index.js`) and communicates via stdin/stdout using the JSON-RPC protocol. Each tool call sends a `tools/call` request and parses the JSON response to extract the text result. After gathering context from all 4 tools, the agent constructs a prompt that includes the raw output from each tool, then sends it to Ollama's `/api/generate` endpoint via HTTP POST.

The agent chose to use 4 tools (not just the minimum 2) because richer context produces better answers. The decision to include `get_insights` alongside `query_knowledge` was deliberate — `query_knowledge` returns general knowledge base entries, while `get_insights` provides scenario-specific advice, giving the LLM both breadth and depth to reason over.

## Output

```
python agent.py "what is the SMILE methodology and how do digital twins work?"
 SMILE methodology and how do digital twins work?"                                        
============================================================
  LPI SMILE Agent
  Question: what is the SMILE methodology and how do digital twins work?
============================================================

[Phase 1] Connecting to LPI MCP server...
  ✓ Connected

[Phase 2] Gathering context from LPI tools...
  [1/4] Querying SMILE overview...
  [2/4] Searching knowledge base...
  [3/4] Fetching case studies...
  [4/4] Getting implementation insights...
  ✓ Context gathered from 4 tools

[Phase 3] Reasoning with LLM (qwen2.5:1.5b)...
  ✓ Response received

============================================================
  ANSWER
============================================================

The SMILE methodology is a benefits-driven digital twin implementation method focused on i
mpact first and data last. It comprises six phases that start with defining the desired outcome (Outcome/Impact) before proceeding through actions, insights, information, and finally data.                                                                                  
1. **Start with Impact**: What specific outcome do you want? Define measurable KPIs before
 touching data.                                                                           2. **Define Scope**: As-is to to-be scope definition.
3. **Simulate Future Actions**: Involve stakeholders in innovation sessions.
4. **Collect Data for Insights**: Gather insights from actions and simulations.
5. **Create Information Flow Ontologies**: Establish shared understanding through ontologi
es.                                                                                       6. **Iterate and Adapt**: Continuously refine, test, and improve the twin.

Digital twins work by creating a digital representation of physical assets or processes to
 simulate their performance under various scenarios. This helps in making informed decisions about maintenance, operations, and improvements before investing in real-world changes. The SMILE methodology ensures that digital twins are aligned with organizational goals from an early stage, leading to more effective and efficient implementation.                
Sources:
- [Tool 1: smile_overview] - provides the overview of the SMILE methodology.
- [Tool 2: query_knowledge("what is the SMILE methodology and how do digital twins work?")
] - explains what the SMILE methodology includes and how it relates to digital twin concepts.                                                                                       - [Tool 4: get_insights("what is the SMILE methodology and how do digital twins work?")] -
 further clarifies the impact-first approach of the SMILE methodology.                    
============================================================
  PROVENANCE (tools used)
============================================================
  [1] smile_overview (no args)
      Preview: # S.M.I.L.E. â€” Sustainable Methodology for Impact Lifecycle Enablement   
                                                                                          
> Benefits-driven digital ...
  [2] query_knowledge {"query": "what is the SMILE methodology and how do digital twins wo
rk?"}                                                                                           Preview: # Knowledge Results

64 entries found (showing top 5):

## Impact First, Data Last

The most common ...
  [3] get_case_studies (no args)
      Preview: # Case Studies

10 available:

- **Smart Heating for Municipal Schools â€” Self-Learning Digital Twi...
  [4] get_insights {"scenario": "what is the SMILE methodology and how do digital twins wo
rk?", "tier": "free"}                                                                           Preview: # Implementation Insights

## Relevant Knowledge
- **Impact First, Data Last**: The most common mist...


```

Every response traces back to the specific LPI tools that provided the data. The user can verify each cited source independently.

## Design Decisions

I decided to build the agent with a class-based architecture (`LPIConnection`) rather than using loose functions, because it makes the MCP connection lifecycle explicit — connect, call tools, disconnect — and keeps provenance tracking centralized. I tried using the raw `examples/agent.py` pattern initially, but chose to restructure it because separating the connection logic from the reasoning logic made the code more testable and extensible.

The trade-off of using `qwen2.5:1.5b` as the default model is that it's lightweight and fast but less capable than larger models. I chose this because it runs on any laptop without GPU requirements, making the agent accessible to all contributors.

I also included an A2A Agent Card (`agent.json`) to demonstrate how agents discover each other's capabilities — different from most submissions that focus only on MCP execution without considering the discovery layer.

## Error Handling & Security

The agent validates all inputs with a `sanitize_input` function that strips control characters and limits input length to prevent injection attacks. Every MCP tool call is wrapped in try/except blocks handling `json.JSONDecodeError`, `BrokenPipeError`, and general exceptions. The Ollama integration handles `ConnectionError`, `Timeout`, and `HTTPError` separately with descriptive messages. The MCP server subprocess is always cleaned up in a `finally` block to prevent zombie processes.

## Setup Instructions

```bash
git clone https://github.com/TouqeerHamdani/lpi-smile-agent.git
cd lpi-smile-agent
pip install requests
python agent.py --lpi-path ../lpi-developer-kit "What is SMILE?"
```

Requires: Python 3.10+, Node.js 18+, Ollama running locally with `qwen2.5:1.5b` pulled.
