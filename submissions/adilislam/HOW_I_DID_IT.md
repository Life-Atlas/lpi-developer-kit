# HOW_I_DID_IT.md — Adil Islam (Track A, Level 3)

## What I did, step by step

1. Forked lpi-developer-kit, ran `npm install && npm run build`
2. Ran `npm run test-client` — confirmed all 7 tools passed
3. Installed Ollama, pulled qwen2.5:1.5b, ran `ollama serve`
4. Ran `examples/agent.py` unchanged to understand the MCP subprocess pattern
5. Hit GPU OOM error (934MB buffer failed on CUDA0) — switched to CPU mode
6. Hit CPU OOM error (980MB buffer failed) — switched to qwen2.5:0.5b
7. Confirmed 0.5b loads cleanly on CPU — tested with a direct curl request
8. Redesigned the agent concept: AI Learning Coach, not a generic advisor
9. Wrote teaching prompt with ANSWER / FOLLOW-UP / SOURCES structure
10. Added 1200-char trim, 300 num_predict cap, 120s timeout — fixed hangs
11. Tested with 5 question types, confirmed consistent provenance output
12. Created separate GitHub repo with README, requirements.txt, agent.py
13. Wrote level3.md and this file

---

## Problems I hit and how I solved them

**GPU OOM — 500 Internal Server Error**
First run: Ollama tried to load qwen2.5:1.5b onto the GPU but cudaMalloc
failed (934MB requested, GPU refused). Fixed by setting:
`$env:OLLAMA_NUM_GPU = "0"` before starting ollama serve.

**CPU OOM — model still failed to load**
Even with GPU disabled, CPU buffer allocation failed (~980MB).
The 1.5b model is too large for available RAM on my machine.
Fixed by switching to qwen2.5:0.5b (~400MB) which loads cleanly.

**Infinite hang on first query**
Before I fixed the model issue, requests would queue forever because the
model runner had crashed silently. Adding `timeout=120` and `num_predict: 300`
to the Ollama request means the hang is now impossible — it either responds
or raises a clean Timeout exception.

**Context too long for 0.5b model**
The example agent sends 5500+ chars to the LLM. The 0.5b model stalls
on this and outputs garbage. Fixed by trimming each tool output to
MAX_CHARS = 1200 — total context stays under 4000 chars.

**Teaching prompt format needed explicit structure**
Without a rigid output format, the 0.5b model rambled.
Adding "Respond exactly in this format: ANSWER: / FOLLOW-UP: / SOURCES:"
made outputs consistent across all question types.

---

## What I learned

**MCP is simpler than it looks**
It's JSON-RPC over stdio — one write to stdin, one readline from stdout.
The init handshake is 2 messages. After that, every tool call is trivial.

**Small models need aggressive constraints**
1.5b → 0.5b wasn't just a size change. It changed how I had to write the
prompt entirely — shorter context, explicit format, lower temperature.
Constraints that feel like limitations actually improve output quality.

**Explainability is an engineering choice, not an afterthought**
The provenance block is separate from the answer intentionally.
Mixing citations into prose makes them easy to skip. A clean PROVENANCE
section at the end means a reviewer can verify every claim in 10 seconds.
This directly connects to my ISR research finding: lexical and NLI metrics
diverge because they measure different causal chains. The provenance log
in this agent solves the same problem at the output level.

**Teaching > retrieving**
The FOLLOW-UP question is the most important part of the output.
SMILE's core insight — continuous feedback loops — applies to learning too.
An answer without a follow-up question ends the loop. A follow-up continues it.