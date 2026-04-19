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