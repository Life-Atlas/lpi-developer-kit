How I Did It

Steps
1. Cloned my forked repo using Git Bash
2. npm wasn't found — fixed by installing Node.js LTS from nodejs.org
3. Reopened Git Bash, ran npm install → 94 packages installed
4. Ran npm run build → TypeScript compiled cleanly
5. Ran npm run test-client → 8/8 tools passed
6. Installed Ollama from ollama.com on Windows
7. Ollama wasn't found in Git Bash — switched to Windows CMD
8. Ran: ollama pull qwen2.5:1.5b (downloaded ~1GB model)
9. Ran: ollama run qwen2.5:1.5b and asked about digital twins

Problems I Hit
- npm not found in Git Bash initially — solved by installing Node.js
- ollama not found in Git Bash — solved by using Windows CMD instead

What I Learned
- MCP is a standard protocol for AI agents to call tools, like a USB standard
  but for AI — it handles input, output and streaming between agent and server
- SMILE is a 6-phase methodology for digital twins that applies to ANY system,
  not just machines — including people and organizations
- You can run a powerful AI model fully offline on a laptop using Ollama —
  no API key, no cost, completely private
