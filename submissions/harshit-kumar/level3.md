# Level 3 Submission — Track A: Agent Builders
## Harshit Kumar | GitHub: hrk0503

---

## Agent: LPI FinTech Insight Agent

A Python-based AI agent that connects to the Life Programmable Interface (LPI) MCP server and answers questions about applying the SMILE methodology to fintech and personal digital twin use cases — specifically around trading behavior and decision-making patterns.

### What the Agent Does

1. Accepts a user question as input (e.g., "How do I build a personal finance digital twin using SMILE?")
2. 2. Queries **at least 2 LPI tools** to gather relevant knowledge:
   3.    - `smile_overview` — retrieves the full 6-phase SMILE methodology
         -    - `query_knowledge` — searches the 63-entry knowledge base for relevant entries
              -    - Optionally: `get_insights` for scenario-specific implementation advice
                   - 3. Processes and combines the results
                     4. 4. Returns an explainable answer that **cites which LPI tool provided which information**
                       
                        5. ### Why Fintech / Personal Trading Twin
                       
                        6. From my contributor profile (`my_twin` field): I want to track the correlation between my deep-focus coding sessions and the quality of my stock market trade decisions. This agent is the first step — it queries the LPI to understand how SMILE phases map to building that kind of personal behavioral digital twin.
                       
                        7. ---
                       
                        8. ## Agent Repository / Code Location
                       
                        9. The agent code is in this fork at:
                        10. **`agent/agent.py`** → https://github.com/hrk0503/lpi-developer-kit/blob/master/agent/agent.py
                       
                        11. ### Key Design Decisions
                       
                        12. - **Raw Python + subprocess** — same pattern as `examples/agent.py`, no extra framework dependencies
                            - - **Provenance tracking** — every part of the output is labeled with which LPI tool produced it
                              - - **Minimum 2 tools queried** — `smile_overview` + `query_knowledge` are always called; `get_insights` is called conditionally
                                - - **No LLM required** — the agent produces a structured, explainable answer directly from LPI tool outputs (LLM integration is optional/additive)
                                 
                                  - ### How to Run
                                 
                                  - ```bash
                                    # Prerequisites: Node.js 18+, npm, Python 3.8+
                                    git clone https://github.com/hrk0503/lpi-developer-kit.git
                                    cd lpi-developer-kit
                                    npm install
                                    npm run build
                                    python agent/agent.py "How do I build a personal finance digital twin using SMILE?"
                                    ```

                                    ### Sample Output

                                    ```
                                    [Tool: smile_overview] SMILE has 6 phases: Reality Emulation, Concurrent Engineering,
                                    Collective Intelligence, Contextual Intelligence, Continuous Intelligence, Perpetual Wisdom.

                                    [Tool: query_knowledge (query: "fintech behavioral patterns")] Found 3 relevant entries:
                                      - Financial decision tracking under SMILE Collective Intelligence phase
                                      - Behavioral pattern modeling for personal digital twins
                                      - Real-time data streams for contextual adaptation

                                    Answer (citing sources above):
                                    To build a personal finance digital twin using SMILE, start with Reality Emulation
                                    (smile_overview Phase 1) to capture your current trading state — your portfolio,
                                    historical trades, session logs. Then apply Collective Intelligence (smile_overview Phase 3)
                                    to continuously gather data: trade timestamps, session duration, focus metrics.
                                    The query_knowledge results show that behavioral pattern modeling is key to correlating
                                    cognitive state with decision quality. Finally, Contextual Intelligence (Phase 4) allows
                                    the twin to adapt recommendations based on your current mental state indicators.
                                    ```

                                    ---

                                    ## LPI Tools Used

                                    | Tool | Purpose | Required |
                                    |------|---------|---------|
                                    | `smile_overview` | Get full SMILE methodology framework | Yes |
                                    | `query_knowledge` | Search knowledge base for domain-specific entries | Yes |
                                    | `get_insights` | Get scenario-specific implementation advice | Optional |

                                    ---

                                    ## HOW_I_DID_IT.md

                                    Full documentation of my process, problems hit, and what I learned:
                                    → [HOW_I_DID_IT.md](./HOW_I_DID_IT.md)

                                    ---

                                    ## Track & Level
                                    - **Track:** A — Agent Builders
                                    - - **Level:** 3 (Retry v2)
                                      - - **Submission PR title:** level-3: Harshit Kumar
