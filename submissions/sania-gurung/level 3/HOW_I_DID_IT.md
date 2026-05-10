# How I Did It - Level 3

## What I did, step by step

I started by reading the README twice, not just once. The second read is where
I noticed the A2A section properly. It says A2A is about agents discovering and
describing each other. That made me think: what if the output of my agent is
itself an agent? Most people will build something that answers questions. I
decided to build something that builds things that answer questions.

My approach: before writing any code, I mapped each of the 7 LPI tools to a
question I'd need to answer when generating a domain-specific agent. What phase
does this domain start from? (smile_overview). What does the knowledge base say?
(query_knowledge). What have others done in this industry? (get_case_studies).
What's the implementation path for this exact scenario? (get_insights). What are
the details of the key phase? (smile_phase_detail). Once that mapping was clear,
the architecture was obvious.

**Step 1** — I built the `Provenance` class first, before writing any LPI calls.
I decided to do this because I wanted explainability baked into the data flow,
not added as a post-hoc log. Every tool call stores its result in provenance,
and every section of the generated output cites it.

**Step 2** — I built the MCP client using subprocess stdio. I chose this because
the LPI server uses standard MCP stdio transport. I tried to over-engineer it
first by adding a connection pool, but I realised each tool call is independent
so stateless subprocess.run() is cleaner and easier to reason about.

**Step 3** — I called 5 tools instead of the minimum 2. The trade-off is
slightly slower runs; the benefit is that the generated agent has much richer
context to work with. I chose depth over speed here.

**Step 4** — The code generator was the hardest part. Generating Python code
inside a Python f-string means inner curly braces need to be doubled (`{{` and
`}}`). I tried several approaches and the one that worked cleanly was building
the tool call block as a separate function so the doubling is contained.

**Step 5** — I wrote the A2A Agent Card (`agent.json`). I noticed the README
says it's optional but also says it "demonstrates you understand how agents
discover each other." I decided to include it because I understand what it
represents — a contract, not just metadata. Any agent that reads the card knows
exactly what this agent accepts, what it produces, and what it guarantees about
its output.

---

## What problems I hit and how I solved them

**Problem 1 — MCP stdio is one-shot per subprocess call.**
I expected the LPI server to stay alive across calls. It doesn't — each
subprocess.run() is a fresh node process. I solved this by making the client
stateless: each call is fully independent. This actually made the provenance
tracking cleaner because there's no shared state to manage.

**Problem 2 — Server returns multiple JSON lines.**
I tried `json.loads(proc.stdout)` first — it broke on multi-line output. Fixed
by iterating line by line and matching on the JSON-RPC request ID field.

**Problem 3 — F-string escaping in the code generator.**
When you generate Python f-strings inside Python f-strings, the inner braces
need to be doubled. I caught this by actually running the generated file and
reading the syntax errors carefully. I tried a different approach — using
`.format()` instead — but that made the template harder to read. I chose to
keep f-strings and accept the double-brace discipline.

**Problem 4 — Industry detection edge cases.**
"Smart building" contains "building" which I had mapped to "real_estate", but
the user probably means smart city or energy. I resolved this by ordering the
keyword checks so more specific terms take priority. Not a perfect solution —
I would add a confidence score in a real system — but honest and documented.

---

## What I learned that I didn't know before

I hadn't worked with MCP before this. The stdio transport approach — where the
server is a subprocess you talk to with JSON-RPC over stdin/stdout — was new to
me. It's simpler than I expected. I can see why it's a good standard: no HTTP
setup, no ports, no auth for local tooling.

I also learned something about explainability. In my Symbiotex project I
generate structured JSON reports with confidence scores. But the report doesn't
explain why the threat was assessed that way — it just states the number. After
reading the SMILE methodology and the evaluation criteria here, I realised a
confidence score without a source trace is just a number. The citation system I
built for this agent is something I'm going to bring back to Symbiotex.

The A2A concept also clicked in a way it didn't on first read. A2A isn't just a
discovery protocol — it's a contract. When an agent publishes an Agent Card,
it's saying: here is what I accept, here is what I produce, here is what I
guarantee. Writing agent.json made that concrete.

What I would do differently next time: I would add a caching layer for LPI tool
responses so the builder doesn't re-query the same tool when generating multiple
agents in the same session. That's a 20-minute addition that would make the tool
noticeably faster.

Signed-off-by: Sania Gurung <saniagurung5452@gmail.com>