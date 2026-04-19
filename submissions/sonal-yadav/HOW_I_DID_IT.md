# How I Did It — Level 3

## What I did, step by step

1. **Set up the dev environment**: I cloned the forked lpi-developer-kit repository and ran `npm install` followed by `npm run build` and then `npm run test-client` — all 7 tools passed successfully. I also ran `pip install requests` for the Python HTTP dependency.

2. **Studied the LPI source code**: Before writing anything, I went through the MCP server source — `src/index.ts` for the tool definitions, `src/tools/smile.ts` for how phase details are returned, `src/tools/knowledge.ts` for how the knowledge search works, and `src/tools/cases.ts` for the case study format. I also looked at the data files to understand what content the tools actually return.

3. **Analyzed the example agent**: I read through `examples/agent.py` to understand the basic MCP communication pattern — subprocess, JSON-RPC handshake, tool calls. The example always calls the same 3 tools regardless of the question, which felt limiting.

4. **Designed a multi-mode architecture**: I wanted my agent to think differently based on what the user is asking. So I came up with 4 modes:
   - **Smart Q&A** for regular questions — routes to 2-4 tools based on keywords
   - **Compare** for side-by-side analysis — gathers data from multiple industries or phases
   - **Maturity Scan** for assessing where someone is on the SMILE journey
   - **Deep Dive** for comprehensive analysis — calls 4-6+ tools

5. **Built the tool planner**: Each mode has its own strategy for selecting which LPI tools to call and why. The "why" (reason) is important — it gets passed into the LLM prompt so the model knows the context for each source, and it shows up in the provenance table so the user can understand the agent's reasoning.

6. **Implemented conversation memory**: The agent tracks what you've asked before in the session and passes a context hint to the LLM. This way follow-up questions have context.

7. **Added the Provenance Engine**: Every tool call gets recorded with source ID, tool name, arguments, reason for querying, result text, and character count. After every answer, a provenance table is printed showing exactly what was queried and how much data came back.

8. **Tested the agent across different scenarios**: I tested with various question types to make sure each mode activates correctly and selects relevant tools.

---

## Problems I hit and how I solved them

- **MCP initialization handshake**: The server needs both an `initialize` request AND a `notifications/initialized` notification before it accepts tool calls. I initially forgot the notification step and the server just hung silently. Reading the MCP spec more carefully fixed this.

- **Context window overflow**: The qwen2.5:1.5b model has limited context. In Deep Dive mode I was calling 5-6 tools and sending all the output to the LLM, which caused timeouts. I solved this by truncating each source to 1800 characters and limiting output to 1024 tokens.

- **Mode detection false positives**: Words like "canvas" contain "vs" which was triggering Compare mode. I had to be more careful with the trigger word matching — checking for word boundaries and more specific phrases.

- **Process cleanup**: If the Python script crashed while the MCP server subprocess was running, the node process would be left orphaned. I wrapped everything in try/finally to make sure `mcp.stop()` always runs.

---

## What I learned

- **SMILE puts impact first, data last**: The core principle is Outcome -> Action -> Insight -> Information -> Data. This is backwards from how most engineering projects work (collect data first, figure out what to do with it later). Once I understood this, the 6-phase structure clicked.

- **MCP is simpler than I expected**: It's just JSON-RPC over stdin/stdout. No HTTP, no WebSocket. The hardest part is the init handshake — after that it's straightforward request-response.

- **Different questions need different tool strategies**: A comparison question needs data from multiple sources to put side by side. A maturity assessment needs phase details and implementation steps. A simple "what is" question just needs the overview. Building the mode system taught me that the routing logic matters as much as the LLM synthesis.

- **Provenance tracking changes how you prompt the LLM**: When each source has an ID and a reason, you can tell the LLM to cite [Source N] and it actually works. You can then verify whether the LLM made something up by checking against the source table.

- **Ontology Factories before AI Factories**: One of the key insights from the knowledge base — you need to build your information models (ontologies) before you can build AI that reasons about them. This maps to Phase 3 (Collective Intelligence) in SMILE.
