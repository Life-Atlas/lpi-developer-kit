#!/usr/bin/env python3
"""
agent_a.py — Client Agent (A2A Orchestrator)
Level 4 Architect Submission — Harshit Kumar (hrk0503)

Agent A is the entry-point for user queries. It:
  1. Discovers Agent B via the A2A protocol (fetches /.well-known/agent.json).
  2. Validates and sanitises incoming queries (prompt-injection guard, rate limiter).
  3. Forwards the sanitised query to Agent B over HTTP and collects a structured response.
  4. Presents the final answer with full provenance (tool name, args, snippet).

Run:
    python agent_a.py          # starts on http://localhost:5001
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import defaultdict
from typing import Any

import requests
from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AGENT_B_BASE_URL = "http://localhost:5002"
AGENT_CARD_PATH = "/.well-known/agent.json"
RATE_LIMIT_WINDOW = 60          # seconds
RATE_LIMIT_MAX_REQUESTS = 10    # per window per client IP
MAX_QUERY_LENGTH = 512          # characters
REQUEST_TIMEOUT = 10            # seconds

# Prompt-injection pattern list (deny-list approach)
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
        r"<\s*script",        # XSS attempt
        r"\bexec\s*\(",     # code-execution attempt
        r"\beval\s*\(",
        r"__import__",
    ]
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AgentA] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)

# In-memory rate-limit store  { ip: [timestamp, ...] }
_rate_store: dict[str, list[float]] = defaultdict(list)


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def check_rate_limit(client_ip: str) -> bool:
    """Return True if the client is within the rate limit."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    hits = _rate_store[client_ip]
    # Purge old entries
    _rate_store[client_ip] = [t for t in hits if t >= window_start]
    if len(_rate_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    _rate_store[client_ip].append(now)
    return True


def sanitise_query(raw: str) -> tuple[bool, str]:
    """
    Validate and clean a raw query string.
    Returns (ok, sanitised_or_error_msg).
    """
    if not isinstance(raw, str):
        return False, "Query must be a string."
    query = raw.strip()
    if not query:
        return False, "Query must not be empty."
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters."
    # Strip dangerous Unicode control characters
    query = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    # Prompt-injection check
    for pattern in INJECTION_PATTERNS:
        if pattern.search(query):
            log.warning("Prompt-injection attempt blocked: %r", query[:120])
            return False, "Query contains disallowed content and was rejected."
    return True, query


def whitelist_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Return only the fields we trust from Agent B's response."""
    allowed = {"answer", "provenance", "agent", "model", "error"}
    return {k: v for k, v in raw.items() if k in allowed}


# ---------------------------------------------------------------------------
# A2A discovery
# ---------------------------------------------------------------------------

def discover_agent_b() -> dict[str, Any] | None:
    """Fetch Agent B's A2A Agent Card."""
    try:
        url = AGENT_B_BASE_URL + AGENT_CARD_PATH
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        card = resp.json()
        log.info("Discovered Agent B: %s v%s", card.get("name"), card.get("version"))
        return card
    except Exception as exc:
        log.error("A2A discovery failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok", "agent": "agent_a", "version": "1.0.0"})


@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card() -> Any:
    """Serve Agent A's own A2A card."""
    import os, pathlib
    card_path = pathlib.Path(__file__).parent / ".well-known" / "agent.json"
    with open(card_path) as fh:
        return app.response_class(response=fh.read(), mimetype="application/json")


@app.route("/query", methods=["POST"])
def query() -> Any:
    """
    Main endpoint.

    POST /query
    Body (JSON): { "query": "<user question>" }
    Response:    { "answer": "...", "provenance": [...], "agent": "...", "model": "..." }
    """
    client_ip = request.remote_addr or "unknown"

    # --- Rate limiting ---
    if not check_rate_limit(client_ip):
        log.warning("Rate limit exceeded for %s", client_ip)
        return jsonify({"error": "Rate limit exceeded. Max 10 requests/minute."}), 429

    # --- Parse body ---
    body = request.get_json(silent=True)
    if not body or "query" not in body:
        return jsonify({"error": "Request body must be JSON with a 'query' field."}), 400

    ok, result = sanitise_query(body["query"])
    if not ok:
        return jsonify({"error": result}), 400

    sanitised_query = result
    log.info("Forwarding sanitised query to Agent B (len=%d)", len(sanitised_query))

    # --- A2A: discover Agent B ---
    card = discover_agent_b()
    if card is None:
        return jsonify({"error": "Agent B is unavailable (A2A discovery failed)."}), 503

    # --- Forward to Agent B ---
    try:
        resp = requests.post(
            AGENT_B_BASE_URL + "/query",
            json={"query": sanitised_query, "from_agent": "agent_a"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json()
    except requests.Timeout:
        return jsonify({"error": "Agent B timed out."}), 504
    except requests.HTTPError as exc:
        return jsonify({"error": f"Agent B returned an error: {exc}"}), 502
    except Exception as exc:
        log.error("Unexpected error calling Agent B: %s", exc)
        return jsonify({"error": "Internal communication error."}), 500

    # --- Whitelist output ---
    safe = whitelist_response(raw)
    safe["routed_by"] = "agent_a"
    return jsonify(safe), 200


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("Agent A starting on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
