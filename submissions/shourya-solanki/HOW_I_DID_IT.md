# HOW_I_DID_IT — Level 2 | Shourya Solanki | Track A: Agent Builders

## What I Did, Step by Step

1. Forked the repo and cloned it locally on my MacBook Pro (M4 Pro)
2. Ran `npm install && npm run build && npm run test-client` — all 8 tests passed first try
3. Installed Ollama and pulled `qwen2.5:1.5b` (~986MB)
4. Hit a pip issue on macOS (externally managed environment) — fixed it by creating a venv
5. Ran `examples/agent.py` with the question about SMILE — got a clean cited response from the local LLM

## Problems I Hit

- `npm install` failed initially because I was in the parent `Developer/` directory instead of inside the repo. Fixed by `cd lpi-developer-kit`.
- macOS blocked `pip install requests` system-wide. Fixed with `python3 -m venv venv && source venv/bin/activate`.
- PyPI was unreachable on first attempt (hostel WiFi) — switched to hotspot, worked immediately.

## What I Learned That I Didn't Know Before

Three things genuinely surprised me about SMILE:

First, the "Impact first, data last" principle. Coming from an ML background where every project starts with data collection and preprocessing, it felt counterintuitive to define the outcome and impact before touching any data. But it makes sense — without knowing what decision the data needs to drive, you end up collecting everything and using nothing.

Second, SMILE starts with people and stakeholder alignment before any sensors or infrastructure. Most AI pipelines I've built jump straight to architecture. The idea that Phase 1 is about establishing a shared *reality canvas* — agreeing on what exists and why it matters — is a very different starting point.

Third, Perpetual Wisdom as a phase. The idea that a digital twin eventually shares its learnings across an entire ecosystem rather than staying siloed in one org changes how I think about what a "finished" AI system even means. It's not a product, it's a living contributor.
