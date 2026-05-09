# How I Did It - Level 2 Submission

**What I did, step by step:**
1. I forked the repository and cloned it to my local machine.
2. I ran `npm install` and `npm run build` to set up the LPI sandbox.
3. I successfully ran `npm run test-client` and verified all 7 tools were passing.
4. I ran the local LLM using Ollama and the provided `agent.py` script to query the SMILE methodology.

**What problems I hit and how I solved them:**
Initially, when trying to submit my PR, I accidentally deleted another contributor's file because my local git history got messed up. The GitHub Actions bot immediately blocked my PR. To fix this, I completely deleted my fork on GitHub, made a fresh fork from the main repository, deleted my local folder, and started with a clean clone. This ensured I only uploaded my specific folder without touching anyone else's work.

**What I learned:**
I learned how strictly GitHub Actions can enforce repository rules, the importance of isolating your work into your own directories, and how to safely reset a Git workflow when things get tangled. I also learned how MCP tools connect with a local Ollama instance to provide grounded AI answers.

## Choices Made (Not in Instructions)
The most critical choice I made outside the standard instructions was implementing an "Auto-Discovery Path Hunter" for the LPI MCP server. Because I built the agent in a completely separate repository to maintain clean modularity, the standard relative pathing (`..`) broke. I wrote a custom `find_lpi_server()` function. It checks for an environment variable first, then intelligently scans adjacent parent directories to accommodate automated bot workspaces, and finally falls back to a local path. This guarantees the code won't break during automated evaluation or human review.

## What I Would Do Differently Next Time
Next time, to make deployment even more seamless, I would package the agent inside a Docker container using a docker-compose network to connect to the LPI server, eliminating file-path hunting altogether. I would also add an A2A Agent Card dynamically so the agent could integrate directly into the LifeAtlas mesh.

## Final Update (Post-CEO Feedback)
Following the feedback from Nicolas, I have pushed a final update to my agent repository (`smile-ai-agent`). I have now implemented:
1. **A2A Agent Card:** The agent dynamically broadcasts its discovery card to the mesh at runtime.
2. **Deeper Error Handling:** Added robust `try/except` blocks for process spawning, JSON decoding, and tool execution to ensure graceful failures.

* Note: Added agent.json (A2A Discovery Card) to my external smile-ai-agent repository.