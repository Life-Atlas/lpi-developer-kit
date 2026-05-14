"""
agent_a.py — SMILE Methodology Specialist Agent (Port 8001)
Level 4 Submission | Adil Islam (@adil-islam)

Responsibilities:
  - Serves A2A agent card at GET /.well-known/agent.json
  - Accepts user queries at POST /task
  - Queries LPI: smile_overview + query_knowledge
  - Discovers Agent B via its A2A card, delegates case-study retrieval
  - Merges both outputs → structured recommendation neither agent could produce alone

What makes this output unique (neither agent alone):
  Agent A alone → SMILE methodology framework, no evidence
  Agent B alone → case studies, no methodology mapping
  Combined      → "Here is your SMILE roadmap [A] backed by real-world cases
                   that followed this exact path and achieved X% improvement [B]"

Security:
  - All inputs sanitized (injection + exfil + length)
  - Output scrubbed before returning
  - Only allowed LPI tools: smile_overview, query_knowledge
  - Cannot call Agent B's tools directly (privilege guard)
  - 120s timeout on all LLM + inter-agent calls

Usage:
  # Start Agent B first, then Agent A:
  python agent_b.py   (terminal 1)
  python agent_a.py   (terminal 2)

  # Or use run_demo.py which manages both automatically
"""

import os
import json
import logging
import requests
from pathlib import Path
from flask import Flask, request, jsonify

from security import SecurityGuard, SecurityError, MAX_TOKENS, TIMEOUT_SECONDS
from mcp_client import MCPClient

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("agent_a")

# ── Config ────────────────────────────────────────────────────────────────────
PORT          = 8001
AGENT_B_URL   = "http://localhost:8002"
AGENT_NAME    = "SMILE Methodology Specialist"
OLLAMA_URL    = "http://localhost:11434/api/generate"
OLLAMA_MODEL  = "qwen2.5:0.5b"

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

# Agent A may only call these LPI tools — NOT Agent B's tools
ALLOWED_TOOLS = ["smile_overview", "query_knowledge"]

# ── Security guard (Agent A instance) ────────────────────────────────────────
guard = SecurityGuard(agent_name=AGENT_NAME, allowed_tools=ALLOWED_TOOLS)

# ── Load A2A agent card ───────────────────────────────────────────────────────
_card_path = Path(__file__).parent / ".well-known" / "agent_a.json"
with open(_card_path) as f:
    AGENT_CARD = json.load(f)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)


@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    """A2A discovery endpoint."""
    return jsonify(AGENT_CARD)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": AGENT_NAME})


@app.route("/task", methods=["POST"])
def handle_task():
    """
    Main orchestration endpoint.

    Request body:
    { "query": "describe the factory/operational problem" }

    Response:
    {
        "agent"        : "SMILE Methodology Specialist",
        "methodology"  : "...",
        "smile_phases" : ["Scan", "Model", ...],
        "evidence"     : { ...from Agent B... },
        "recommendation": "...",
        "sources"      : [...]
    }
    """
    body = request.get_json(silent=True) or {}
    raw_query = body.get("query", "")

    # ── 1. Sanitize input ─────────────────────────────────────────────────────
    try:
        safe_query = guard.sanitize_input(raw_query)
    except SecurityError as e:
        logger.warning("Security violation on /task input: %s", e)
        return jsonify({"error": str(e), "blocked": True}), 400

    # ── 2. Discover Agent B via A2A card ──────────────────────────────────────
    agent_b_card = _discover_agent_b()
    if agent_b_card is None:
        return jsonify({"error": "Agent B unavailable — is it running on port 8002?"}), 503

    logger.info("Discovered Agent B: %s", agent_b_card.get("name"))

    # ── 3. Query LPI for SMILE methodology ───────────────────────────────────
    client = MCPClient(REPO_ROOT, guard)
    sources = []
    try:
        client.start()

        overview_raw = client.call_tool("smile_overview", {})
        sources.append({"tool": "smile_overview", "agent": AGENT_NAME})

        knowledge_raw = client.call_tool("query_knowledge", {"query": safe_query})
        sources.append({"tool": "query_knowledge", "agent": AGENT_NAME, "input": safe_query})

    finally:
        client.stop()

    # ── 4. LLM: identify applicable SMILE phases ──────────────────────────────
    phase_prompt = _build_phase_prompt(safe_query, overview_raw, knowledge_raw)

    try:
        phase_output = guard.with_timeout(_call_ollama, phase_prompt, timeout=TIMEOUT_SECONDS)
    except (TimeoutError, Exception) as e:
        logger.error("Phase identification failed: %s", e)
        return jsonify({"error": f"LLM error: {e}"}), 500

    phase_output = guard.scrub_output(phase_output)
    smile_phases = _extract_phases(phase_output)
    methodology_text = phase_output

    # ── 5. Delegate to Agent B (structured sub-query) ─────────────────────────
    # This is what neither agent can do alone — A knows the phases, B has the evidence
    b_request = {
        "query"       : safe_query,
        "smile_phases": smile_phases,
        "domain"      : "steel manufacturing",
    }
    evidence = _call_agent_b(b_request)
    sources.append({"agent": "Case Study Analyst (Agent B)", "url": AGENT_B_URL})

    # ── 6. LLM: synthesise final combined recommendation ──────────────────────
    synth_prompt = _build_synthesis_prompt(safe_query, methodology_text, evidence)

    try:
        recommendation = guard.with_timeout(_call_ollama, synth_prompt, timeout=TIMEOUT_SECONDS)
    except (TimeoutError, Exception) as e:
        recommendation = f"[Synthesis failed: {e}]"

    recommendation = guard.scrub_output(recommendation)

    return jsonify({
        "agent"         : AGENT_NAME,
        "query"         : safe_query,
        "smile_phases"  : smile_phases,
        "methodology"   : methodology_text,
        "evidence"      : evidence,
        "recommendation": recommendation,
        "sources"       : sources,
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _discover_agent_b() -> dict | None:
    """
    A2A discovery: fetch Agent B's agent card.
    Returns the card dict, or None if Agent B is not reachable.
    This is the A2A protocol handshake — Agent A learns what B can do
    before delegating to it, rather than hardcoding the interface.
    """
    try:
        resp = requests.get(
            f"{AGENT_B_URL}/.well-known/agent.json",
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("A2A discovery failed for Agent B: %s", e)
        return None


def _call_agent_b(payload: dict) -> dict:
    """
    Send a structured sub-query to Agent B's /task endpoint.
    Returns Agent B's structured evidence dict.
    """
    try:
        resp = requests.post(
            f"{AGENT_B_URL}/task",
            json=payload,
            timeout=TIMEOUT_SECONDS + 30,  # give B time for its own LLM call
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Agent B /task call failed: %s", e)
        return {"case_studies": [], "patterns": [], "metrics": {}, "error": str(e)}


def _build_phase_prompt(query, overview, knowledge):
    return f"""You are a SMILE methodology specialist. Use ONLY the provided context.
Identify which SMILE phases apply to this factory problem and explain why briefly.

SMILE methodology:
{overview}

Knowledge base result:
{knowledge}

Problem: {query}

Respond in this format (max 150 words):
PHASES: [list the applicable SMILE phase names]
METHODOLOGY: [2-3 sentences on how to apply them to this problem]
"""


def _build_synthesis_prompt(query, methodology, evidence):
    cs = evidence.get("case_studies", [])
    cs_text = "\n".join(
        f"- {c.get('title','')}: {c.get('summary','')} → {c.get('outcome','')}"
        for c in cs[:3]
    ) or "No case studies retrieved."

    patterns = ", ".join(evidence.get("patterns", [])) or "None identified."

    return f"""You are synthesising a final recommendation from two specialist agents.
Combine the SMILE methodology roadmap with the case study evidence into one actionable recommendation.
Be specific. Max 120 words. No hallucination — use only what's provided.

Problem: {query}

SMILE Methodology (Agent A):
{methodology}

Case Study Evidence (Agent B):
{cs_text}

Patterns from evidence: {patterns}

Write the combined recommendation:
RECOMMENDATION: [specific, actionable, cites both methodology and evidence]
"""


def _extract_phases(llm_output: str) -> list:
    """Parse SMILE phase names out of the LLM PHASES: line."""
    known = ["Scan", "Model", "Implement", "Learn", "Evolve"]
    line = ""
    for ln in llm_output.splitlines():
        if ln.strip().upper().startswith("PHASES:"):
            line = ln
            break
    return [p for p in known if p.lower() in line.lower()] or ["Scan", "Model"]


def _call_ollama(prompt: str) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": MAX_TOKENS,
                "temperature": 0.4,
                "num_gpu": 0,
            },
        },
        timeout=TIMEOUT_SECONDS + 5,
    )
    resp.raise_for_status()
    return resp.json().get("response", "[no response]")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'─'*55}")
    print(f"  Agent A — {AGENT_NAME}")
    print(f"  Listening on http://localhost:{PORT}")
    print(f"  A2A card: http://localhost:{PORT}/.well-known/agent.json")
    print(f"  Discovers Agent B at: {AGENT_B_URL}/.well-known/agent.json")
    print(f"  Allowed LPI tools: {ALLOWED_TOOLS}")
    print(f"{'─'*55}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
