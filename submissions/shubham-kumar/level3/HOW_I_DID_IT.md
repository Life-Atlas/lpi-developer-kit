# How I Did It - Level 3

### What I did, step by step

After completing level 2 I decided to go with Track A and build an actual agent. The idea I had was something useful — not just a wrapper around the tools but something that takes real user inputs like industry, use case, constraints and gives back a structured plan.

I started by reading the example agent in `examples/agent.py` to understand how the MCP subprocess works and how JSON-RPC calls are made to the LPI server. That gave me the base structure.

Then I designed the agent around three inputs — industry, use case, and resource constraints. I picked three LPI tools that made sense together: `get_insights` for scenario advice, `get_case_studies` to ground the output in real examples, and `query_knowledge` for technical context.

I wrote the MCP connection code first, tested each tool call one by one to make sure responses were coming back correctly. Then I built the prompt around those three sources and passed it to Ollama.

The output I wanted was structured — scope, expected outcomes, SMILE phases to prioritize, what to defer, and first actions. So I designed the prompt to produce exactly those sections.

I also added the A2A agent card since the README mentioned it as a bonus and it only took a few minutes once the agent was working.

---

### What problems I hit and how I solved them

First issue was a `SyntaxError` — I had used a global variable before declaring it global in the function. Python doesn't allow that. Fixed by moving the `global` declaration to the top of the function.

Second issue was a `404 Not Found` from Ollama. I had set the default model to `qwen3.5:35b` thinking I had it pulled, but when I checked with the Ollama API only `qwen2.5:1.5b` was actually installed. Changed the default back and it worked.

Third issue was the report getting cut off mid-sentence. The prompt was too long so the model ran out of space to finish. I trimmed the context slices fed from each tool — reduced from 2500/2000/2000 characters to 1800/1500/1500 — and after that the output completed properly.

---

### What I learned that I didn't know before

I didn't fully understand how MCP worked before this. Going through the JSON-RPC handshake manually — initialize, notifications/initialized, then tool calls — made it click. It's basically just structured stdin/stdout between processes.

I also learned that prompt design matters more than I expected. The first version of the prompt gave vague answers. Once I structured it with named sections and told the model to cite which source each claim came from, the quality jumped noticeably.

The constraint-aware output was the part I found most interesting to think through. It's easy to tell someone what a digital twin can do. It's harder to tell them what to skip given 3 months and one engineer. That required the model to actually reason against the constraints, not just summarize the tools.

Also learned about A2A agent cards — had not heard of this protocol before. Makes sense as a discovery layer separate from the execution layer.
