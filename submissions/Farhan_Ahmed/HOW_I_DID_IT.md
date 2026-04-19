# HOW_I_DID_IT.md — Level 2 Submission
**Farhan Ahmed Siddique | Track A: Agent Builders**

---

## What I Did, Step by Step

### Step 1: Cloned and Set Up the Repo
I forked the `lpi-developer-kit` repo on GitHub, then cloned my fork locally. After navigating into the project directory, I ran:
```bash
npm install
npm run build
npm run test-client
```
All 8/8 tools passed on the first run. The sandbox confirmed: `smile_overview`, `smile_phase_detail`, `query_knowledge`, `get_case_studies`, `get_insights`, `list_topics`, and `get_methodology_step` were all working.

### Step 2: Installed Ollama and Pulled a Local LLM
I already had Ollama installed. I pulled and ran the `qwen2.5:1.5b` model:
```bash
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b
```
The model ran locally on my machine — no cloud API key needed.

### Step 3: Ran the LPI Sandbox Test Client Output
```
=== LPI Sandbox Test Client ===
[LPI Sandbox] Server started — 7 read-only tools available
Connected to LPI Sandbox

=== Results ===
Passed: 8/8
Failed: 0/8
All tools working. Your LPI Sandbox is ready.
You can now build agents that connect to this server.
```

### Step 4: Read the SMILE Methodology
I called `smile_overview` to read all 6 phases and 3 perspectives. I also queried `get_case_studies` to see real-world applications across industries.

### Step 5: Reflected on What Surprised Me About SMILE
(See below — written in my own words.)

---

## What Surprised Me About SMILE (3 Sentences)

1. What's genuinely surprising about SMILE is its framing of sustainability not as an end-state metric but as a *continuous feedback signal* embedded across the entire digital twin lifecycle — meaning AI models governing the twin are expected to adapt their optimization targets as real-world impact data flows back, essentially treating "sustainability" as a dynamic reward function rather than a static KPI.

2. Rather than training a model once and deploying it against a fixed schema, SMILE implicitly demands that the AI layer co-evolve with the twin's fidelity — which is architecturally counterintuitive because it requires designing for *planned model drift* rather than fighting it, treating the twin's state-space expansion as a feature, not a bug.

3. The most innovative — and underappreciated — aspect of SMILE is the *Enablement* pillar, which forces AI engineers to confront the organizational API boundary problem: the digital twin must not only model physical assets but also expose structured interfaces for human decision-makers, meaning the AI architecture must simultaneously serve simulation accuracy, explainability, and real-time actionability — three objectives that are classically in tension.

---

## Problems I Hit and How I Solved Them

- **TypeScript build warnings**: Minor type warnings during `npm run build` that didn't block the build — ignored safely.
- **Ollama model size**: `qwen2.5:1.5b` is lightweight enough to run on my laptop without GPU acceleration, which made local inference fast enough for development.

---

## What I Learned

- How MCP (Model Context Protocol) works as a tool-calling layer between an AI agent and a knowledge server — it's essentially a typed RPC protocol for AI tools.
- That SMILE is not just a methodology checklist — it's a living feedback loop. The "phases" aren't waterfall steps; they're iterative cycles designed for continuous improvement.
- Running a local LLM via Ollama is genuinely practical for development. No latency costs, no API limits, full control.

---

---

# Level 3 — Agent Builders

## What I Did

I built a Python agent (`level3-agent/agent.py`) that:
1. Starts the LPI MCP server as a subprocess over stdio
2. Performs the JSON-RPC handshake (initialize + notifications/initialized)
3. Calls **4 LPI tools** — `smile_overview`, `smile_phase_detail`, `query_knowledge`, `get_case_studies`
4. Concatenates all tool outputs into a structured prompt with provenance labels
5. Sends the prompt to `qwen2.5:1.5b` running locally via Ollama
6. Prints the LLM answer + a provenance table showing exactly which tool contributed what

I also added an `--interactive` flag so the agent can answer multiple questions in a session without restarting.

## Problems I Hit

- **MCP stdio protocol**: The handshake order matters — `initialize` request must come before `notifications/initialized`, otherwise the server silently drops subsequent tool calls. I debugged this by reading the existing `test-client.ts`.
- **LLM hallucination**: When the prompt was too long, `qwen2.5:1.5b` started ignoring the "cite your sources" instruction. Fixed by trimming each tool result to 2000 chars max.
- **Windows path issues**: `os.path.join` with `..` didn't resolve correctly when running from a sub-folder. Fixed with `os.path.abspath`.

## What I Learned

- MCP is a thin JSON-RPC layer — far simpler than I expected. Once you understand the handshake, it's just stdin/stdout pipes.
- Provenance tracking is not just a nice-to-have — it's what makes an AI agent trustworthy. If the agent can't say WHERE its answer came from, it's not safe to ship.
- Local LLMs like `qwen2.5:1.5b` are fast enough for tool-augmented agents. The bottleneck is the MCP tool calls, not the LLM.

---

Signed-off-by: Farhan Ahmed Siddique <farhan@example.com>
