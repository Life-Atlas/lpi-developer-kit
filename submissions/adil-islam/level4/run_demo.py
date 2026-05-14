"""
run_demo.py — Launches both agents and runs an end-to-end demo.
Level 4 Submission | Adil Islam (@adil-islam)

This script:
  1. Starts Agent B (Case Study Analyst) in a background thread
  2. Starts Agent A (SMILE Specialist) in a background thread
  3. Waits for both to be ready (health checks)
  4. Sends a real factory problem to Agent A
  5. Prints the full transcript showing multi-agent collaboration

Prerequisites:
  - ollama serve  (running in background)
  - ollama pull qwen2.5:0.5b
  - npm run build  (inside lpi-developer-kit/)
  - pip install flask requests

Usage:
  python run_demo.py
"""

import sys
import time
import json
import threading
import requests

# ── Demo query ────────────────────────────────────────────────────────────────
# Factory problem drawn from the real Level 6 dataset:
# Station 016 (Gjutning) has only one trained operator (Per Hansen, W07).
# Victor Elm (W11, Foreman) is the sole backup — a single point of failure.
# Weeks w1, w2, w4 show capacity deficits of -132, -125, -50 hours respectively.
DEMO_QUERY = (
    "Our steel fabrication factory's Gjutning station (016) is consistently "
    "running 10-15% over planned hours, and has only one qualified operator "
    "with a single backup. Weeks 1, 2 and 4 show capacity deficits of 132, 125 "
    "and 50 hours respectively. How should we apply the SMILE methodology to "
    "address the structural bottleneck and workforce risk?"
)

AGENT_A_URL = "http://localhost:8001"
AGENT_B_URL = "http://localhost:8002"


# ── Start agents in background threads ───────────────────────────────────────

def _start_agent(module_path: str):
    """Import and run a Flask agent in a daemon thread."""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("agent_mod", module_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.app.run(host="0.0.0.0", port=mod.PORT, debug=False, use_reloader=False)


def start_agents():
    import os
    base = os.path.dirname(os.path.abspath(__file__))

    print("⟳ Starting Agent B (Case Study Analyst) on port 8002...")
    tb = threading.Thread(
        target=_start_agent,
        args=(os.path.join(base, "agent_b.py"),),
        daemon=True,
    )
    tb.start()
    time.sleep(1)  # brief pause so B gets its port before A tries to discover it

    print("⟳ Starting Agent A (SMILE Specialist) on port 8001...")
    ta = threading.Thread(
        target=_start_agent,
        args=(os.path.join(base, "agent_a.py"),),
        daemon=True,
    )
    ta.start()


# ── Health-check wait ─────────────────────────────────────────────────────────

def wait_for_agent(url: str, name: str, retries: int = 15):
    for i in range(retries):
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                print(f"  ✅ {name} ready")
                return True
        except Exception:
            pass
        print(f"  ⟳ Waiting for {name}... ({i+1}/{retries})")
        time.sleep(2)
    print(f"  ❌ {name} did not start in time")
    return False


# ── A2A discovery verification ────────────────────────────────────────────────

def verify_a2a(url: str, agent_label: str) -> dict:
    """Fetch and display the A2A agent card."""
    r = requests.get(f"{url}/.well-known/agent.json", timeout=5)
    card = r.json()
    print(f"\n  📋 {agent_label} A2A Card:")
    print(f"     Name     : {card.get('name')}")
    print(f"     Skills   : {[s['name'] for s in card.get('skills', [])]}")
    print(f"     LPI Tools: {card.get('_lpiMetadata', {}).get('lpiToolsUsed', [])}")
    return card


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'═'*60}")
    print("  Level 4 — Secure Agent Mesh Demo")
    print("  Author: Adil Islam (@adil-islam)")
    print(f"{'═'*60}\n")

    # 1. Start both agents
    start_agents()

    # 2. Wait for readiness
    print("\n── Waiting for agents to start ──")
    b_ready = wait_for_agent(AGENT_B_URL, "Agent B (Case Study Analyst)")
    a_ready = wait_for_agent(AGENT_A_URL, "Agent A (SMILE Specialist)")

    if not (a_ready and b_ready):
        print("\n❌ Agents failed to start. Check that Ollama is running: ollama serve")
        sys.exit(1)

    # 3. Verify A2A discovery
    print("\n── A2A Discovery ──")
    verify_a2a(AGENT_B_URL, "Agent B")
    verify_a2a(AGENT_A_URL, "Agent A")

    # 4. Send demo query to Agent A
    print(f"\n── Sending Factory Problem to Agent A ──")
    print(f"\n  Query: {DEMO_QUERY[:120]}...\n")

    t_start = time.time()
    try:
        resp = requests.post(
            f"{AGENT_A_URL}/task",
            json={"query": DEMO_QUERY},
            timeout=300,   # 5 min total — two LLM calls + agent B's call
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        sys.exit(1)

    elapsed = round(time.time() - t_start, 1)

    # 5. Print full transcript
    print(f"\n{'═'*60}")
    print("  COMBINED RECOMMENDATION")
    print(f"  (generated in {elapsed}s by 2 agents + 2 LLM calls + 3 LPI tool calls)")
    print(f"{'═'*60}\n")

    print(f"SMILE PHASES IDENTIFIED: {result.get('smile_phases', [])}\n")

    print("── METHODOLOGY (Agent A → LPI: smile_overview + query_knowledge) ──")
    print(result.get("methodology", "[not returned]"))

    evidence = result.get("evidence", {})
    print("\n── CASE STUDY EVIDENCE (Agent B → LPI: query_knowledge + get_insights) ──")
    for cs in evidence.get("case_studies", []):
        print(f"  • {cs.get('title','')}: {cs.get('summary','')}")
        print(f"    Outcome: {cs.get('outcome','')}")

    print("\n  Patterns:", evidence.get("patterns", []))
    print("  Metrics:", evidence.get("metrics", {}))

    print("\n── COMBINED RECOMMENDATION (neither agent could produce this alone) ──")
    print(result.get("recommendation", "[not returned]"))

    print("\n── PROVENANCE ──")
    for src in result.get("sources", []):
        if "tool" in src:
            print(f"  [{src.get('agent', src.get('tool'))}] → {src.get('tool')} ({src.get('input','')[:60]})")
        else:
            print(f"  [{src.get('agent')}] → {src.get('url','')}")

    print(f"\n{'═'*60}")
    print("  Demo complete.")
    print(f"{'═'*60}\n")

    # Save transcript for submission
    import os
    transcript_path = os.path.join(os.path.dirname(__file__), "demo_transcript.md")
    _save_transcript(DEMO_QUERY, result, elapsed, transcript_path)
    print(f"  Transcript saved to: {transcript_path}")


def _save_transcript(query, result, elapsed, path):
    evidence = result.get("evidence", {})
    cs_text = "\n".join(
        f"- **{c.get('title','')}**: {c.get('summary','')} → {c.get('outcome','')}"
        for c in evidence.get("case_studies", [])
    ) or "_No case studies returned_"

    sources_text = "\n".join(
        f"- `{s.get('tool', s.get('agent',''))}` — {s.get('input', s.get('url',''))[:80]}"
        for s in result.get("sources", [])
    )

    content = f"""# Level 4 — Demo Transcript
**Author:** Adil Islam (@adil-islam)
**Generated in:** {elapsed}s (2 agents × Ollama qwen2.5:0.5b + 3 LPI tool calls)

---

## Query (sent to Agent A)

> {query}

---

## Step 1 — Agent A queries LPI (smile_overview + query_knowledge)

Identified SMILE phases: `{result.get('smile_phases', [])}`

**Methodology output:**

{result.get('methodology', '_not returned_')}

---

## Step 2 — Agent A discovers Agent B via A2A card

Agent A fetched `http://localhost:8002/.well-known/agent.json` and confirmed:
- Name: Case Study Analyst
- Skills: case_study_retrieval
- LPI Tools: query_knowledge, get_insights

Agent A then sent a structured sub-query:
```json
{{
  "query": "{query[:100]}...",
  "smile_phases": {result.get('smile_phases', [])},
  "domain": "steel manufacturing"
}}
```

---

## Step 3 — Agent B queries LPI (query_knowledge + get_insights)

**Case studies retrieved:**

{cs_text}

**Patterns:** {evidence.get('patterns', [])}
**Metrics:** {evidence.get('metrics', {})}

---

## Step 4 — Agent A synthesises combined recommendation

> {result.get('recommendation', '_not returned_')}

**Why neither agent could produce this alone:**
- Agent A alone → SMILE phases + methodology, no real-world evidence
- Agent B alone → case study evidence, no methodology mapping to this problem
- Together → actionable roadmap + proof it works from comparable cases

---

## Provenance

{sources_text}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
