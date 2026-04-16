# LPI Developer Kit

**Build AI agents on the Life Programmable Interface.**

> **DEADLINE: Sunday April 20, 23:59 UTC.** All Level 3 submissions must be in by then. No exceptions.

The LPI is an open MCP server with 7 tools exposing the [SMILE methodology](https://lifeatlas.online) — a digital twin implementation framework. This repo is your sandbox AND the entry point for the **LifeAtlas Contributor Program**.

---

## How It Works (read this first)

```
┌─────────────────────────────────────────────────────────┐
│  1. FORK this repo                                      │
│  2. CLONE your fork locally                             │
│  3. RUN: npm install && npm run test-client              │
│  4. DO the challenge for your level (see below)         │
│  5. SUBMIT a Pull Request back to this repo             │
│  6. BOT auto-validates → auto-merges (Level 1)         │
│     or auto-scores → posts feedback (Level 2/3)        │
│  7. LEADERBOARD updates automatically                   │
│     → life-atlas.github.io/lpi-developer-kit            │
└─────────────────────────────────────────────────────────┘
```

**Where do I submit?** → Pull Request to this repo. That's it.
**Who reviews?** → GitHub Actions bot (auto). Team leads review top submissions manually.
**How do I know what to do?** → Pick your track below. Each level has exact instructions.
**What if I'm stuck?** → Open an issue on this repo or ask in the Teams channel.

### Key Concepts

- **MCP** — a standard way for AI agents to call tools. Your agent sends a request, the server sends back data.
- **A2A** — a protocol for agents to discover each other and describe their capabilities.
- **LLM** — a Large Language Model (ChatGPT, Claude, or local models via Ollama).
- **Ollama** — free software to run AI models on your laptop. No cloud, no API key, no cost.
- **SMILE** — our methodology for building digital twins. The LPI server contains all the knowledge about it.

---

## Quick Start

**Requirements:** Node.js 18+ and npm.

```bash
git clone https://github.com/Life-Atlas/lpi-developer-kit.git
cd lpi-developer-kit
npm install
npm run build
npm run test-client
```

You should see all 7 tools pass. If they do, your sandbox is ready.

**Troubleshooting:**
- If `npm install` fails on slow internet, try: `npm install --prefer-offline --no-audit`
- If `npm run build` shows TypeScript errors, check your Node version: `node --version` (must be 18+)
- On Windows, use PowerShell or Git Bash, not cmd.exe

### Available Tools

| Tool | Description |
|------|-------------|
| `smile_overview` | Full overview of the SMILE methodology — 6 phases, 3 perspectives, AI journey |
| `smile_phase_detail` | Deep dive into a specific SMILE phase |
| `query_knowledge` | Search the knowledge base (63 entries across 11 topic areas) |
| `get_case_studies` | Browse 10 anonymized case studies across 10 industries |
| `get_insights` | Get scenario-specific implementation advice |
| `list_topics` | Browse all available topics in the knowledge base |
| `get_methodology_step` | Step-by-step guidance for implementing a SMILE phase |

### Connect from Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lpi-sandbox": {
      "command": "node",
      "args": ["<full-path-to>/lpi-developer-kit/dist/src/index.js"]
    }
  }
}
```

---

## LifeAtlas Contributor Program

### What You're Joining

LifeAtlas is building the world's first edge-native digital twin OS — a platform where AI agents help people understand and optimize their lives using the SMILE methodology (Sustainable Methodology for Impact Lifecycle Enablement).

This is a **multi-track contributor program**. Not everyone writes code — some people research, design, write, test, or build 3D visualizations. Every track contributes to the same product. Every contribution is real.

**Five tracks:**
- **Agent Builders** — code, AI agents, MCP tools, data pipelines
- **Content & Research** — case studies, course modules, competitive analysis, grant writing
- **Design & UX** — UI/UX, infographics, dashboards, brand materials
- **3D & Visualization** — Unity, Unreal, Three.js, spatial twins, AR/VR
- **QA & Security** — testing, security audits, bug hunting, accessibility

Pick the track that matches your skills. Details for each track's screening challenge are below. You can switch tracks later — this is a starting point, not a cage.

**Read the full program guide:** [PROGRAM.md](docs/PROGRAM.md) — how sprints work, how tasks get assigned, IP ownership, what you get, what we expect.

This isn't a classroom exercise. This is open-source contribution to a live product.

### How You're Evaluated

Five metrics. Weighted equally. Assessed continuously.

**1. Contribution Quality** — Does your code work? Is it clean? Small and working beats large and broken.

**2. Discussion & Collaboration** — Do you ask good questions? Do you help teammates? Do you engage?

**3. Explainability** — Can you explain what your agent does and WHY? AI that can't explain itself is AI we don't ship.

**4. Initiative** — Do you find problems and solve them, or wait to be told?

**5. Growth Velocity** — Where did you start vs. where are you now? **Someone who starts at Level 1 and ships a working agent by week 3 scores higher than someone who started at Level 3 and stayed there.** We measure trajectory, not starting point.

---

## The Screening Challenge

Complete as many levels as you can. Each level brings you closer to a guaranteed place on the team.

- **Level 1** — You're registered and on the leaderboard
- **Level 2** — You've proven you can set up and run the tools
- **Level 3** — **You're in. Completing Level 3 guarantees your place on the WINNIIO / LifeAtlas contributor team.**

**Deadline:** 7 days from receiving this.

### Level 1 — Register (5 minutes)

1. Fork this repo
2. Copy `contributors/TEMPLATE.json` to `contributors/your-name.json`
3. Fill in your details:

```json
{
  "name": "Your Full Name",
  "github": "your-github-username",
  "program": "B.Tech CSE / M.Tech AI / etc",
  "campus": "Amity Noida / Lucknow / etc",
  "skills": ["python", "pytorch", "react"],
  "interests": ["agents", "NLP", "3D", "security"],
  "my_twin": "Write something real here — see below"
}
```

**About the `my_twin` field:** There is no wrong answer. We want to know how YOU think about personal data, not what sounds impressive. Bad answer: "I would track my CGPA." Good answer: "I would track my energy levels throughout the day and correlate them with what I ate and how I slept, because I crash every afternoon and don't know why." Be specific. Be personal. This is the most interesting field in the form.

4. Submit a PR. Title: `level-1: Your Name`

**That's it. You're registered.**

### Level 2 & 3 — Choose Your Track

**Everyone runs the LPI sandbox first** (all tracks):

```bash
git clone <your-fork>
cd lpi-developer-kit
npm install
npm run build
npm run test-client
```

Capture the output showing all 7 tools pass. Then pick your track:

---

#### Track A: Agent Builders (technical)

**Level 2** (45-90 min): Run the LPI sandbox (above) + install [Ollama](https://ollama.com) and run a local LLM. Submit: test client output + LLM output + 3 sentences on what surprised you about SMILE.

**Level 3** (2-4 hours): Build an AI agent that connects to the LPI and does something useful. Use any approach: Python, LangGraph, CrewAI, raw API calls. Must query at least 2 LPI tools and cite its sources. Submit as a separate GitHub repo. See `examples/agent.py` for a working starting point.

#### Track B: Content & Research

**Level 2** (30-60 min): Run the LPI sandbox (above). Read the SMILE methodology output from `smile_overview` and at least 2 case studies. Write a 1-page summary: how does SMILE apply to an industry YOU find interesting? (healthcare, manufacturing, energy, agriculture, smart cities, sports — your choice).

**Level 3** (2-4 hours): Find 3 real-world digital twin implementations NOT already in the LPI knowledge base. For each: describe the challenge, the approach, the outcome, and which SMILE phases were applied. Sources must be cited. Submit as a structured document in `submissions/your-name/`.

#### Track C: Design & UX

**Level 2** (30-60 min): Run the LPI sandbox (above). Read the SMILE methodology output. Sketch a visual representation of the 6 SMILE phases that a non-technical person could understand in 30 seconds. Any tool: Figma, Canva, pen and paper (photograph it).

**Level 3** (2-4 hours): Design a dashboard mockup for ONE of: (a) a personal health digital twin showing sleep, nutrition, exercise, and stress, (b) a professional's client management view, or (c) a course landing page for "The Future of People: Digital Twins for Life." Submit as images or a Figma link in `submissions/your-name/`.

#### Track D: 3D & Visualization

**Level 2** (30-60 min): Run the LPI sandbox (above). Read about Reality Emulation (Phase 1). Write a short description of what a 3D "Reality Canvas" would look like for: a hospital, a horse stable, a smart building, or a human body.

**Level 3** (2-4 hours): Build a simple 3D scene (Unity, Unreal, Godot, Three.js, or Blender) showing a digital twin concept. Must have at least one data overlay (temperature, heart rate, occupancy — whatever fits). Export a video walkthrough or a playable build. Submit a link in `submissions/your-name/`.

#### Track E: QA & Security

**Level 2** (30-60 min): Run the LPI sandbox (above). Try to make it fail. Send unexpected inputs, long queries, special characters. Document everything — what broke, what didn't, what error messages you got. Submit as a bug report.

**Level 3** (2-4 hours): We have planted **at least 5 intentional security vulnerabilities** in `examples/vulnerable-api.py`. Run it locally (`pip install flask && python examples/vulnerable-api.py`) and write a security audit report:
- Find as many vulnerabilities as you can
- Classify each one (OWASP category)
- Explain the impact (what could an attacker do?)
- Propose a fix for each

Also audit the LPI sandbox server itself (`src/`) for any real issues. Even finding nothing is valuable if your methodology is sound. Submit in `submissions/your-name/`.

---

**Submit all Level 2/3 work as PRs.** Title: `level-2: Your Name` or `level-3: Your Name`

**Required for all Level 2/3 submissions:** Include a `HOW_I_DID_IT.md` in your submission folder. Write in your own words:
- What you did, step by step
- What problems you hit and how you solved them
- What you learned that you didn't know before

This is not optional. We read these to understand how you think. AI-generated write-ups are easy to spot and will count against you. Write like you're explaining it to a teammate, not a professor.

### Track A: Level 3 — Detailed Agent Requirements

For Track A specifically, your agent must:
1. Accept a user question or input
2. Query at least 2 LPI tools to get relevant knowledge
3. Process the results — summarize, analyze, combine, or visualize
4. **Cite which LPI tools and data it used** — explainable AI means the user traces every part of the answer

Use any approach: raw Python, LangGraph, CrewAI, LangChain, any LLM (local or cloud), or no LLM at all. A working example is in `examples/agent.py`.

Submit as a **separate GitHub repo** with a link in `submissions/your-name/level3.md`.

PR title: `level-3: Your Name`

**Optional bonus:** Include an A2A Agent Card (`agent.json`) describing your agent's capabilities. See `submissions/AGENT_CARD_TEMPLATE.json` for the format. This is not required but demonstrates you understand how agents discover each other.

### What We're Looking For

| | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| **Time** | 5 min | 45-90 min | 2-4 hours |
| **Proves** | Git basics, follow instructions | Dev setup, local AI, reading comprehension | Independent building, agent design, explainability |
| **Key signal** | The `my_twin` answer shows how you think | Model choice + SMILE reflection shows curiosity | Does it work? Can it explain itself? |

---

## How the Program Works

### The Principle

Everything you build is a **module**. Your own repo, your own code, plugging into the LPI. You don't edit our core platform. You build on top of it. By the end of this program, you will have built a **personal backpack of AI agents** — tools that connect to real data, use real methodology, and produce explainable results. This is your portfolio. It goes on your GitHub. It's yours.

### Daily Standups

Every working day. **Camera on. Be prepared. Be on time.**

This is where you learn the most. You will be in active discussions with your team. Come ready to:
- Show what you built (screen share)
- Explain what you're working on
- Ask for help or offer help to teammates

Don't worry about having something perfect to show — showing a broken build and asking for help is more valuable than sitting silent. The point is engagement, not perfection.

If you prefer written communication, async written updates are accepted — but you must still attend and listen. The learning happens in the discussion.

### Weekly Rhythm

| Day | Activity |
|---|---|
| Mon-Thu | Build. Daily standup with your team. |
| Friday | **Demo + Learning** — team demos what shipped that week. We share cutting-edge developments in AI agents, MCP, open-source LLMs, explainable AI, and edge computing. This is your window into what the industry is building right now. |

### Assessment (Weeks 1-2)

After the first 1-2 weeks of contribution, we reassess:
- What have you actually shipped?
- What skills are emerging?
- What do YOU want to go deeper on?

You'll move into a focus team based on your performance and your preference. We want you where you're most effective AND most excited.

### Focus Teams

Teams form after the initial assessment:

- **Agent Builders** — build AI agents on the LPI using local and cloud LLMs
- **AI/ML Pipeline** — RAG, embeddings, fine-tuning, model evaluation
- **Research & Content** — SMILE documentation, case studies, course materials
- **QA & Security** — break things, find vulnerabilities, write test suites
- **Data & Knowledge** — knowledge graphs, data pipelines, analytics
- **3D & Visualization** — spatial twins, Unreal Engine *(separate brief)*

### What You Get

- Real AI agent development experience on a production platform
- Published open-source work on YOUR GitHub — your name, your code, your portfolio
- Your personal **agent backpack** — a collection of working tools you built
- Experience with cutting-edge tooling: MCP protocol, open-source LLMs, explainable AI, edge-native architecture
- Weekly exposure to industry-current AI developments — not textbook material
- Letter of recommendation based on your actual contributions

### What We Expect

- **Show up.** Daily standups, on time, camera on.
- **Ship.** Working code, every week. Small is fine. Broken is not.
- **Explain.** If you can't explain what your agent does and why, it's not done.
- **Collaborate.** This is a team sport. Help others. Ask for help.
- **Own your work.** Your repos, your commits, your `Signed-off-by`. Every contribution has your name on it.

---

## How MCP and A2A Work Together

This developer kit uses two complementary protocols:

- **MCP (Model Context Protocol)** is a tool-calling protocol. It defines how your agent invokes a specific tool: "call `query_knowledge` with query='digital twins'". MCP handles execution — input, output, streaming. Think of it as the USB cable between devices.

- **A2A (Agent-to-Agent Protocol)** is a discovery and task-routing protocol. It defines how agents find each other and describe what they can do. Think of it as the business card you exchange before plugging in the cable.

In this developer kit:
1. The **LPI server** publishes an A2A Agent Card (`.well-known/agent.json`) describing its 7 tools as skills.
2. **Your agent** can also publish an Agent Card describing what it does.
3. **Execution** happens over MCP (subprocess/stdio locally). A2A tells you what exists; MCP lets you use it.

```
Discovery:   A2A Agent Card  →  "What can you do?"
Execution:   MCP Protocol    →  "Do this specific thing."
```

## Example Agent

An example Python agent is included in `examples/agent.py`. It demonstrates:
- Connecting to the LPI MCP server via subprocess
- Calling 3 LPI tools to gather context
- Passing results to a local LLM (Ollama) with a provenance-tracking prompt
- Returning an explainable answer that cites which tools provided which information

```bash
# Prerequisites: npm run build, ollama serve, ollama pull qwen2.5:1.5b
pip install requests
python examples/agent.py "What is the SMILE methodology and how do I start?"
```

Use this as a starting point for your Level 3 submission. Extend it, replace it, or build something completely different — as long as it uses LPI tools and explains itself.

---

## Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [A2A Protocol Specification](https://a2a-protocol.org)
- [Ollama — Run LLMs locally](https://ollama.com)
- [SMILE Methodology](https://lifeatlas.online)
- [LifeAtlas on GitHub](https://github.com/Life-Atlas)

## License

MIT — build whatever you want on top of this.

Level 3 retry submission v2
