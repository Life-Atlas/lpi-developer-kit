# How I Did It — Level 4

### What I did, step by step

Coming off Level 3, I had one agent that could scope a digital twin ROI. Decent, but it was basically one script doing everything alone. For Level 4 the challenge was building two agents that actually *need* each other — not just two scripts that happen to run in sequence.

The idea I kept coming back to was: what if one agent makes a plan, and the other agent's entire job is to poke holes in it? That felt genuinely useful. Not two agents answering the same question differently, but two agents doing completely different jobs that only make sense together. The Planner uses SMILE methodology data to build an implementation roadmap. The Validator goes and reads real case studies to find where similar plans have gone wrong. By themselves, each one is half a picture. Together you get a plan that's already been stress-tested before you act on it.

I kept the agents simple on purpose — each one just reads JSON from stdin and writes JSON to stdout. That way I could test them individually without the full system running. The orchestrator wires them together and handles everything around them: reading the A2A cards, sanitizing input, passing the plan from Agent A to Agent B, printing the final report.

For the A2A part I wrote proper agent cards for both — `planner.json` and `validator.json` — with typed input and output schemas. So the orchestrator knows what each agent expects before it invokes anything. That's the whole point of A2A: discovery before execution.

Security took the most thinking. I wrote a shared `security.py` that both agents import. The main thing I learned here is that you can't just sanitize at the front door and consider yourself done. If Agent A got replaced or compromised, it could send a malicious plan payload to Agent B. So Agent B also re-validates and re-sanitizes everything it receives, even though it came from "inside" the system. Defense at every boundary, not just the entry point.

Then I tried to break it. Seven different attack attempts, all documented in `security_audit.md`. The most interesting one was bypassing the orchestrator entirely and piping a hand-crafted injection payload straight to `validator.py`. Before I added the re-sanitization step in the validator, that attack worked. After the fix, it got blocked.

---

### What problems I hit and how I solved them

The biggest headache was the LLM refusing to output clean JSON. `qwen2.5:1.5b` has a habit of wrapping everything in markdown code fences, or adding a little explanation paragraph before the actual JSON. At first this just broke my JSON parser every time. I fixed it by scanning the response for the first `{` and last `}` and only parsing what's between them. And if that still fails, there's a fallback plan built from the raw LPI data — it's marked with `_fallback: true` so it's obvious what happened, and the provenance is still correct since the LPI tool calls did happen.

The other thing I had to figure out was what "structured data exchange" actually looks like without a network. In production, agents would call each other over HTTP with proper endpoints. Here I'm using subprocess pipes — Agent A's stdout feeds directly into Agent B's stdin, with the orchestrator validating the schema in between. It's the same data contract, just no HTTP layer. A bit unconventional but it makes the agent boundaries very clear.

---

### What I learned that I didn't know before

I genuinely didn't understand the point of A2A before this. I kept thinking "why do I need a JSON card when I can just call the script?" But working through it made it click — A2A is about knowing what an agent *can* do before you commit to calling it. The card is a contract. If the validator card declares it expects a specific plan schema, the orchestrator can enforce that contract and reject anything that doesn't conform. That's actually where the privilege escalation protection comes from — it's the schema check, not any clever firewall.

The security work also changed how I think about trust in multi-agent systems. With a single agent it's simple: trust the user or don't. With multiple agents you have to make a decision at every boundary about how much each agent trusts the previous one. The safe answer is "not completely" — even if Agent A is yours, what if it's been tampered with, or produces bad output due to a buggy prompt? You still validate. Every agent in the chain is a potential attack surface, not just the first one that touches user input.
