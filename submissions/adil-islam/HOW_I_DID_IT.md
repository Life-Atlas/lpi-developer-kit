# HOW_I_DID_IT.md — Adil Islam (Track A, Level 3)

## What I did, step by step

1. Forked and cloned the repo, ran `npm install && npm run build`
2. Ran `npm run test-client` — confirmed all tools passed (8/7) passed
3. Read `examples/agent.py` fully to understand the MCP subprocess pattern
4. Installed Ollama, pulled qwen2.5:0.5b(1.5 was not-supported), confirmed it ran locally
5. Extended the agent to query 3 tools instead of 2, with better 
   prompt structuring for source citation
6. Tested with 5 different questions to verify consistent provenance output
7. Created a separate GitHub repo with README, requirements.txt, agent.py
8. Wrote level3.md linking the repo and documenting how to run it

## Problems I hit and how I solved them

- **Ollama timeout on first run** - the model was still loading. 
  Fixed by increasing timeout in query_ollama() to 120s and waiting 
  for the model to fully load before sending requests.

- **MCP subprocess not terminating cleanly** - proc.terminate() 
  wasn't enough on Windows. Added proc.wait(timeout=5) and wrapped 
  in try/finally so the process always closes even if the tool call fails.

- **LLM ignoring source citations** - when the context was too long, 
  the model dropped the citation instruction. Fixed by truncating each 
  tool output (overview[:2000], knowledge[:2000], cases[:1500]) and 
  making the citation instruction more explicit in the prompt.

## What I learned

- MCP is much simpler than I expected it's just JSON-RPC over stdio. 
  No HTTP, no auth, just structured messages on stdin/stdout.

- SMILE's structure (6 phases, 3 perspectives) maps directly to what 
  I already understand as a RAG pipeline: capture → model → validate → 
  optimize. The methodology is the same loop, just applied to life data 
  instead of text corpora.

- The way of explaining/understanding in agents is not just about the final answer, it's 
  about tracking which part of te data source caused which type of claim. This is exactly 
  what i found while working on my ISR research : lexical metrics and NLI metrics diverges 
  because they measure different causal chains. The Scource log in 
  this agent solves that at the output level.