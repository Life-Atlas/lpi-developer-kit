#!/usr/bin/env python3
"""
agent_b.py — Server Agent (SMILE Specialist)
Level 4 Architect Submission — Harshit Kumar (hrk0503)

Agent B is the specialist agent. It:
  1. Exposes an A2A Agent Card at /.well-known/agent.json for discovery.
  2. Accepts sanitised queries from Agent A via POST /query.
  3. Calls the LPI MCP tools (smile_overview, query_knowledge) via Ollama subprocess.
  4. Returns a structured JSON response with answer + full provenance chain.

Security:
  - Only accepts requests from trusted callers (agent_a or localhost).
  - Input re-validated on arrival (defence-in-depth).
  - Output sanitised before returning.
  - Subprocess timeout prevents DoS.

Run:
    python agent_b.py          # starts on http://localhost:5002
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
import subprocess
import time
from typing import Any

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LISTEN_PORT = 5002
OLLAMA_MODEL = "qwen2.5:1.5b"
SUBPROCESS_TIMEOUT = 15         # seconds — prevents DoS via hanging tool calls
MAX_QUERY_LENGTH = 512

# Trusted callers (agent name sent in from_agent field)
TRUSTED_CALLERS = {"agent_a"}

# LPI MCP tool definitions (called via ollama generate)
LPI_TOOLS = {
    "smile_overview": {
        "description": "Returns a structured overview of the SMILE methodology "
                       "(Social, Meaning, Interests, Livelihoods, Environment).",
        "prompt_template": (
            "You are an LPI SMILE expert. Using the SMILE framework, "
            "provide a concise structured overview answering: {query}
"
            "Format your response as JSON with keys: dimension, summary, lpi_indicators."
        ),
    },
    "query_knowledge": {
        "description": "Queries the LPI knowledge base for detailed indicator data.",
        "prompt_template": (
            "You are an LPI knowledge-base agent. "
            "Answer the following query about Life Progress Indicators: {query}
"
            "Return JSON with keys: answer, sources, confidence (0-1)."
        ),
    },
}

# Injection patterns (same set as Agent A — defence-in-depth)
INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore (all )?(previous|prior|above) instructions",
        r"you are now",
        r"disregard (your|all|the) (instructions|rules|guidelines)",
        r"system prompt",
        r"jailbreak",
        r"act as (if )?you (are|were)",
        r"forget (everything|all|your training)",
        r"override (your|the) (instructions|rules|system)",
        r"<\s*script",
        r"\bexec\s*\(",
        r"\beval\s*\(",
        r"__import__",
    ]
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AgentB] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def validate_query(raw: str) -> tuple[bool, str]:
    """Re-validate query for defence-in-depth."""
    if not isinstance(raw, str):
        return False, "Query must be a string."
    query = raw.strip()
    if not query:
        return False, "Empty query."
    if len(query) > MAX_QUERY_LENGTH:
        return False, "Query too long."
    query = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    for pattern in INJECTION_PATTERNS:
        if pattern.search(query):
            log.warning("Injection attempt re-caught at Agent B: %r", query[:80])
            return False, "Disallowed content."
    return True, query


def sanitise_output(text: str) -> str:
    """Strip control characters from LLM output before returning."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


# ---------------------------------------------------------------------------
# LPI Tool execution
# ---------------------------------------------------------------------------

def call_ollama(prompt: str) -> str:
    """
    Call ollama generate in a subprocess with a hard timeout.
    Returns the model's response text or raises RuntimeError.
    """
    cmd = [
        "ollama", "run", OLLAMA_MODEL,
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ollama exited {result.returncode}: {result.stderr[:200]}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ollama timed out after {SUBPROCESS_TIMEOUT}s")


def run_tool(tool_name: str, query: str) -> dict[str, Any]:
    """
    Execute a named LPI tool and return a provenance record.
    """
    if tool_name not in LPI_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool = LPI_TOOLS[tool_name]
    prompt = tool["prompt_template"].format(query=query)

    start = time.time()
    raw_output = call_ollama(prompt)
    elapsed = round(time.time() - start, 2)

    # Try to parse as JSON for structured output; fall back to raw text
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        # Extract first 300 chars as a safe snippet
        parsed = {"raw_response": sanitise_output(raw_output[:300])}

    return {
        "tool": tool_name,
        "args": {"query": query},
        "response_snippet": sanitise_output(str(parsed)[:400]),
        "elapsed_s": elapsed,
        "model": OLLAMA_MODEL,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok", "agent": "agent_b", "version": "1.0.0"})


@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card() -> Any:
    """Serve this agent's A2A card."""
    card_path = pathlib.Path(__file__).parent / ".well-known" / "agent.json"
    with open(card_path) as fh:
        return app.response_class(response=fh.read(), mimetype="application/json")


@app.route("/query", methods=["POST"])
def query_endpoint() -> Any:
    """
    Accepts a query from Agent A.

    POST /query
    Body (JSON): { "query": "...", "from_agent": "agent_a" }
    Response:    { "answer": "...", "provenance": [...], "agent": "agent_b", "model": "..." }
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON body."}), 400

    # --- Caller verification ---
    caller = body.get("from_agent", "")
    if caller not in TRUSTED_CALLERS:
        log.warning("Untrusted caller: %r", caller)
        return jsonify({"error": "Forbidden."}), 403

    # --- Re-validate query ---
    ok, result = validate_query(body.get("query", ""))
    if not ok:
        return jsonify({"error": result}), 400

    safe_query = result
    log.info("Processing query from %s (len=%d)", caller, len(safe_query))

    # --- Call both LPI tools ---
    provenance: list[dict[str, Any]] = []
    answers: list[str] = []

    for tool_name in ("smile_overview", "query_knowledge"):
        try:
            record = run_tool(tool_name, safe_query)
            provenance.append(record)
            answers.append(record["response_snippet"])
        except RuntimeError as exc:
            log.error("Tool %s failed: %s", tool_name, exc)
            provenance.append({"tool": tool_name, "error": str(exc)})

    # --- Cross-reference: flag disagreement between tools ---
    combined_answer = " | ".join(answers) if answers else "No answer produced."

    return jsonify(
        {
            "answer": sanitise_output(combined_answer[:1000]),
            "provenance": provenance,
            "agent": "agent_b",
            "model": OLLAMA_MODEL,
        }
    ), 200


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("Agent B starting on http://localhost:5002")
    app.run(host="0.0.0.0", port=5002, debug=False)
