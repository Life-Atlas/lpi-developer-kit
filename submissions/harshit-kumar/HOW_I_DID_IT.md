# HOW_I_DID_IT.md — Level 3 Track A: Agent Builders
## Harshit Kumar | GitHub: hrk0503

---

## What I Built

I built a Python-based AI agent called the **LPI FinTech Insight Agent** that connects to the LPI MCP server and answers questions about how the SMILE methodology applies to financial technology and trading systems. Given my interest in stock markets and coding performance correlation (from my `my_twin` entry), I focused on making an agent that could reason about personal digital twins in the fintech space.

The agent accepts a user question, queries at least 2 LPI tools to gather relevant knowledge, and produces an explainable answer that cites which tools provided which information.

---

## Step-by-Step: What I Did

### Step 1 — Set Up the LPI Sandbox
I forked the repo and cloned it locally:
```
git clone https://github.com/hrk0503/lpi-developer-kit.git
cd lpi-developer-kit
npm install
npm run build
npm run test-client
```
All 7 tools passed. This confirmed the sandbox was ready.

### Step 2 — Explored the LPI Tools
I ran the test client and read through the output of each tool:
- `smile_overview` — gave me the full 6-phase, 3-perspective view of SMILE
- - `query_knowledge` — let me search across 63 knowledge entries
  - - `get_case_studies` — showed me 10 real industry case studies
    - - `get_insights` — gave scenario-specific implementation advice
      - - `list_topics` — showed all 11 topic areas
       
        - I was especially drawn to how the `Collective Intelligence` phase applies to tracking personal behavioral patterns — exactly the kind of data a fintech personal twin would need.
       
        - ### Step 3 — Designed the Agent
        - I decided the agent would:
        - 1. Accept a user question (e.g., "How can SMILE help me build a personal finance twin?")
          2. 2. Call `smile_overview` to get the methodology framework
             3. 3. Call `query_knowledge` with a relevant query derived from the user's question
                4. 4. Optionally call `get_insights` for scenario-specific advice
                   5. 5. Combine all results and format an answer that explicitly cites which tool provided which insight
                     
                      6. ### Step 4 — Wrote the Agent Code
                      7. I used raw Python with subprocess to call the MCP server (same pattern as `examples/agent.py`). The main logic:
                      8. - Parse user input
                         - - Spawn the LPI server as a subprocess
                           - - Send MCP tool calls sequentially
                             - - Collect results and build a provenance-tracked response
                              
                               - The agent lives at: `agent/agent.py` in this repo.
                              
                               - ### Step 5 — Tested the Agent
                               - I tested with several questions:
                               - - "What is SMILE and how does it apply to fintech?"
                                 - - "How would I track trading behavior using digital twins?"
                                   - - "What case studies exist for financial digital twins?"
                                    
                                     - Each time the agent cited the tools it used, e.g.:
                                     - ```
                                       [smile_overview] → Phase overview: Reality Emulation captures current state...
                                       [query_knowledge: fintech] → 3 relevant entries found about financial modeling...
                                       Answer: Based on LPI knowledge, building a fintech digital twin would start with...
                                       ```

                                       ### Step 6 — Problems I Hit

                                       **Problem 1 — MCP subprocess communication:**
                                       The initial version didn't properly wait for the MCP server to initialize before sending tool calls. I fixed this by adding a small delay and reading the initialization handshake before proceeding.

                                       **Problem 2 — JSON parsing errors:**
                                       The LPI server sometimes returns multi-line JSON with embedded newlines. I had to handle partial reads carefully using buffered line reading.

                                       **Problem 3 — Tool result size:**
                                       `smile_overview` returns a lot of text. My first prompt to the LLM was too long. I solved this by extracting only the phase names and 1-sentence summaries before passing to the LLM context.

                                       ---

                                       ## What I Learned

                                       1. **MCP is simpler than I expected.** It's just JSON-RPC over stdio. Once I understood the handshake, tool calls were straightforward.
                                      
                                       2. 2. **Explainability requires discipline.** It's easy to just dump all LPI results into a prompt and get an answer. Making the agent explicitly say "this came from tool X" required structuring the output deliberately.
                                         
                                          3. 3. **SMILE is more practical than it sounds.** The `Collective Intelligence` and `Contextual Intelligence` phases directly map to what you'd need for any personal behavioral twin — real-time data collection + context-aware response. For my fintech use case, that means tracking trade decisions alongside mental state indicators.
                                            
                                             4. 4. **The `query_knowledge` tool is powerful.** With 63 entries across 11 topics, a well-crafted query returns highly relevant results. I initially used broad queries but got better results with specific terms like "behavioral patterns" and "decision tracking."
                                               
                                                5. ---
                                               
                                                6. ## Agent Repo
                                               
                                                7. The agent code is in `agent/agent.py` in this fork:
                                                8. https://github.com/hrk0503/lpi-developer-kit/blob/master/agent/agent.py
                                               
                                                9. ---
                                               
                                                10. ## Track & Level
                                               
                                                11. - **Track:** A — Agent Builders
                                                    - - **Level:** 3
                                                      - - **Submission type:** Retry v2
