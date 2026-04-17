# How I Did It - Track A (Level 2 & Level 3)

### What I did, step by step
1. Verified the LPI MCP Server was working correctly by running `npm run test-client`.
2. Created a separate directory for my agent (`lpi-level3-agent`) and initialized my agent code.
3. Examined the `lpi-developer-kit` knowledge base and the example MCP communication script.
4. Built a python AI agent script that forks the `node src/index.js` server directly underneath to maintain full local connection.
5. In my agent code, I defined tool calls to `query_knowledge` and `smile_phase_detail` to dynamically pull information based on a user’s keyword request.
6. The results are formatted exactly with citations from the MCP server, and fed into Ollama (with a graceful fallback if Ollama isn't active).
7. Wrote an `agent.json` card mapping my new agent capabilities.
8. Packaged it all together for submission!

### What problems I hit and how I solved them
- **Problem**: Connecting to Ollama reliably if the environment changes or if I switch machines.
- **Solution**: I implemented a try-catch HTTP fallback so the script doesn't crash but instead yields the raw processed synthesized insights if the LLM backend is offline.
- **Problem**: Maintaining track of which tool fed what information to ensure explainable AI.
- **Solution**: I logged every tool payload directly into a `tools_used` array and explicitly provided this in the `PROVENANCE` footer.

### What I learned that I didn't know before
- How exactly the MCP protocol defines JSON-RPC communication through stdio.
- That AI explanation doesn't just mean a good summary; it means hard provenance paths matching the exact arguments fed to the API. Using `agent.json` for A2A discovery was also a conceptually powerful technique for scaling agent ecosystems without central bottlenecks.
- **Bonus Initiative**: I successfully wrapped my terminal-based agent inside a modern Python Flask web server. Using a custom glassmorphism design system in vanilla HTML/CSS, the agent's logic endpoints expose an API that visually and cleanly outputs its reasoning directly to the user's browser!
