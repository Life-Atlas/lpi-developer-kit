"""
agent_b.py — Case Study Analyst Agent (Port 8002)
Level 4 Submission | Adil Islam (@adil-islam)

Responsibilities:
  - Serves A2A agent card at GET /.well-known/agent.json
  - Accepts structured sub-queries from Agent A at POST /task
  - Queries LPI: query_knowledge + get_insights
  - Returns structured JSON evidence: {case_studies, patterns, metrics}

Security:
  - All inputs sanitized via SecurityGuard before touching LLM
  - Output scrubbed for internal leaks before returning
  - Only allowed tools: query_knowledge, get_insights (privilege guard)
  - 120s timeout on every Ollama call (DoS guard)
  - Input length capped at 600 chars (DoS guard)

Start this agent BEFORE agent_a.py — Agent A discovers Agent B on startup.

Usage:
  python agent_b.py              # runs forever on port 8002
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
logger = logging.getLogger("agent_b")

# ── Config ────────────────────────────────────────────────────────────────────
PORT         = 8002
AGENT_NAME   = "Case Study Analyst"
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:0.5b"

# 3 levels up from submissions/adil-islam/level4/ → repo root
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

# Agent B is only permitted to call these two LPI tools
ALLOWED_TOOLS = ["query_knowledge", "get_insights"]

# ── Security guard (Agent B instance) ────────────────────────────────────────
guard = SecurityGuard(agent_name=AGENT_NAME, allowed_tools=ALLOWED_TOOLS)

# ── Load A2A agent card ───────────────────────────────────────────────────────
_card_path = Path(__file__).parent / ".well-known" / "agent_b.json"
with open(_card_path) as f:
    AGENT_CARD = json.load(f)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)


@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    """A2A discovery endpoint — Agent A calls this to learn what Agent B can do."""
    return jsonify(AGENT_CARD)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": AGENT_NAME})


@app.route("/task", methods=["POST"])
def handle_task():
    """
    Main task endpoint.

    Expected request body:
    {
        "query"        : "describe the operational problem",
        "smile_phases" : ["Scan", "Model"],   # from Agent A
        "domain"       : "manufacturing"
    }

    Response:
    {
        "agent"       : "Case Study Analyst",
        "case_studies": [...],
        "patterns"    : [...],
        "metrics"     : {...},
        "sources"     : [...]
    }
    """
    body = request.get_json(silent=True) or {}
    raw_query = body.get("query", "")
    smile_phases = body.get("smile_phases", [])
    domain = body.get("domain", "manufacturing")

    # ── 1. Sanitize input (injection + exfil + length guards) ─────────────────
    try:
        safe_query = guard.sanitize_input(raw_query)
    except SecurityError as e:
        logger.warning("Security violation on /task input: %s", e)
        return jsonify({"error": str(e), "blocked": True}), 400

    # ── 2. Query LPI tools ────────────────────────────────────────────────────
    client = MCPClient(REPO_ROOT, guard)
    sources = []
    try:
        client.start()

        enriched = f"{safe_query} Focus on SMILE phases: {', '.join(smile_phases)}. Domain: {domain}."

        case_raw = client.call_tool("query_knowledge", {"query": enriched})
        sources.append({"tool": "query_knowledge", "input": enriched})

        insights_raw = client.call_tool("get_insights", {"scenario": safe_query})
        sources.append({"tool": "get_insights", "input": safe_query})

    finally:
        client.stop()

    # ── 3. Ask Ollama to extract structured evidence ──────────────────────────
    prompt = _build_prompt(safe_query, smile_phases, case_raw, insights_raw)

    try:
        llm_output = guard.with_timeout(_call_ollama, prompt, timeout=TIMEOUT_SECONDS)
    except TimeoutError as e:
        logger.error("Ollama timed out: %s", e)
        return jsonify({"error": "LLM timeout — try again"}), 504
    except Exception as e:
        logger.error("Ollama error: %s", e)
        return jsonify({"error": f"LLM error: {e}"}), 500

    # ── 4. Scrub output for leaks ─────────────────────────────────────────────
    llm_output = guard.scrub_output(llm_output)

    # ── 5. Parse structured JSON from LLM output ──────────────────────────────
    structured = _parse_llm_output(llm_output)
    structured["agent"]   = AGENT_NAME
    structured["sources"] = sources

    return jsonify(structured)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_prompt(query, smile_phases, case_raw, insights_raw):
    phases_str = ", ".join(smile_phases) if smile_phases else "all phases"
    return f"""You are a Case Study Analyst. Extract relevant case study evidence from the LPI knowledge base.
Use ONLY the provided context. Return ONLY valid JSON — no preamble, no markdown fences.

SMILE phases to match: {phases_str}
Problem: {query}

--- LPI query_knowledge result ---
{case_raw}

--- LPI get_insights result ---
{insights_raw}

Return this exact JSON structure:
{{
  "case_studies": [
    {{"title": "...", "summary": "...", "outcome": "..."}}
  ],
  "patterns": ["pattern 1", "pattern 2"],
  "metrics": {{"success_rate": "...", "avg_improvement": "..."}}
}}

JSON only. No other text."""


def _call_ollama(prompt: str) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": MAX_TOKENS,
                "temperature": 0.2,   # low temp for structured output
                "num_gpu": 0,
            },
        },
        timeout=TIMEOUT_SECONDS + 5,
    )
    resp.raise_for_status()
    return resp.json().get("response", "{}")


def _parse_llm_output(raw: str) -> dict:
    """
    Safely parse JSON from Ollama output.
    Falls back to a structured error dict if parsing fails.
    """
    # Strip any accidental markdown fences the model might add
    cleaned = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("LLM did not return valid JSON — returning raw as text")
        return {
            "case_studies": [],
            "patterns": [raw[:300]],
            "metrics": {"note": "LLM returned non-JSON; raw excerpt above"},
        }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'─'*55}")
    print(f"  Agent B — {AGENT_NAME}")
    print(f"  Listening on http://localhost:{PORT}")
    print(f"  A2A card: http://localhost:{PORT}/.well-known/agent.json")
    print(f"  Allowed tools: {ALLOWED_TOOLS}")
    print(f"{'─'*55}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
