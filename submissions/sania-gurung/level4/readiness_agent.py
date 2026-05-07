#!/usr/bin/env python3
"""
Agent A — Digital Twin Readiness Analyst

Receives a project description, calls 3 LPI tools (get_case_studies,
query_knowledge, get_insights) to gather real-world evidence, then uses
Ollama to produce a scored ReadinessReport JSON.

Input  (stdin):  {"description": "...", "request_id": "..."}
Output (stdout): ReadinessReport JSON
"""

import json
import os
import re
import subprocess
import sys

import requests

sys.path.insert(0, os.path.dirname(__file__))
from security import sanitize_input, SecurityError

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LPI_CMD = ["node", os.path.join(_REPO_ROOT, "dist", "src", "index.js")]
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:5b")
OLLAMA_TIMEOUT = 180


def _start_mcp():
    proc = subprocess.Popen(
        LPI_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=_REPO_ROOT,
    )
    init = {
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "readiness-agent", "version": "1.0.0"},
        },
    }
    proc.stdin.write(json.dumps(init) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()
    return proc


def _call_tool(proc, tool: str, args: dict) -> str:
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": tool, "arguments": args}}
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        return f"[ERROR] No response for {tool}"
    resp = json.loads(line)
    if "result" in resp and "content" in resp["result"]:
        return resp["result"]["content"][0].get("text", "")
    return f"[ERROR] {resp.get('error', {}).get('message', 'unknown')}"


def _query_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.ConnectionError:
        return ""
    except Exception:
        return ""


def _extract_json(text: str) -> dict | None:
    """Extract first JSON object from LLM output (handles markdown fences)."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _build_fallback(description: str, request_id: str, tools_used: list) -> dict:
    """Fallback when LLM fails — conservative scores with explicit flag."""
    return {
        "schema_version": "1.0",
        "request_id": request_id,
        "project": {"description": description},
        "readiness_dimensions": [
            {
                "dimension": "data_maturity",
                "score": 2,
                "finding": "LLM unavailable; conservative score assigned from LPI evidence.",
                "evidence_source": "query_knowledge",
                "gap_severity": "high",
            },
            {
                "dimension": "stakeholder_alignment",
                "score": 3,
                "finding": "LLM unavailable; moderate score assigned.",
                "evidence_source": "get_case_studies",
                "gap_severity": "medium",
            },
            {
                "dimension": "technical_infrastructure",
                "score": 2,
                "finding": "LLM unavailable; conservative score assigned.",
                "evidence_source": "get_insights",
                "gap_severity": "high",
            },
        ],
        "overall_readiness_score": 2,
        "top_gaps": ["data_maturity", "technical_infrastructure"],
        "recommended_starting_phase": "reality-emulation",
        "tools_used": tools_used,
        "_fallback": True,
    }


def run(description: str, request_id: str) -> dict:
    tools_used = []

    proc = _start_mcp()
    try:
        cases = _call_tool(proc, "get_case_studies", {})
        tools_used.append({"tool": "get_case_studies", "args": {}, "returned_chars": len(cases)})

        knowledge = _call_tool(proc, "query_knowledge", {"query": description})
        tools_used.append({"tool": "query_knowledge", "args": {"query": description}, "returned_chars": len(knowledge)})

        insights = _call_tool(proc, "get_insights", {"scenario": description})
        tools_used.append({"tool": "get_insights", "args": {"scenario": description}, "returned_chars": len(insights)})
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    prompt = f"""You are a digital twin implementation expert assessing project readiness.

Evaluate the project below on THREE dimensions based ONLY on the LPI evidence provided.
Return a JSON object with EXACTLY this structure (no markdown, no extra text):

{{
  "schema_version": "1.0",
  "request_id": "{request_id}",
  "project": {{"description": "{description[:200]}"}},
  "readiness_dimensions": [
    {{
      "dimension": "data_maturity",
      "score": <integer 1-5>,
      "finding": "<what the evidence says, max 120 chars>",
      "evidence_source": "query_knowledge",
      "gap_severity": "<low|medium|high>"
    }},
    {{
      "dimension": "stakeholder_alignment",
      "score": <integer 1-5>,
      "finding": "<what the evidence says, max 120 chars>",
      "evidence_source": "get_case_studies",
      "gap_severity": "<low|medium|high>"
    }},
    {{
      "dimension": "technical_infrastructure",
      "score": <integer 1-5>,
      "finding": "<what the evidence says, max 120 chars>",
      "evidence_source": "get_insights",
      "gap_severity": "<low|medium|high>"
    }}
  ],
  "overall_readiness_score": <integer 1-5, average of above>,
  "top_gaps": ["<dimension with lowest score>", "<second lowest>"],
  "recommended_starting_phase": "<one of: reality-emulation|contextual-intelligence|predictive-insight|adaptive-response|strategic-alignment|continuous-evolution>",
  "tools_used": []
}}

Scoring guide:
1 = not ready at all, 2 = early stage, 3 = moderate, 4 = mostly ready, 5 = fully ready
gap_severity: score 1-2 = high, score 3 = medium, score 4-5 = low

--- LPI Evidence: get_case_studies ---
{cases[:1500]}

--- LPI Evidence: query_knowledge("{description[:100]}") ---
{knowledge[:1500]}

--- LPI Evidence: get_insights("{description[:100]}") ---
{insights[:1000]}

--- Project Description ---
{description}

Return ONLY the JSON object. No markdown fences, no explanation."""

    raw = _query_ollama(prompt)
    parsed = _extract_json(raw) if raw else None

    if parsed is None:
        result = _build_fallback(description, request_id, tools_used)
    else:
        parsed["schema_version"] = "1.0"
        parsed["request_id"] = request_id
        parsed["tools_used"] = tools_used
        if "project" not in parsed:
            parsed["project"] = {"description": description}
        result = parsed

    return result


def main():
    raw_input = sys.stdin.read().strip()
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        sys.exit(1)

    try:
        description = sanitize_input(payload.get("description", ""), field="description")
    except SecurityError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if not description:
        print(json.dumps({"error": "description field is required"}))
        sys.exit(1)

    request_id = str(payload.get("request_id", "unknown"))

    result = run(description, request_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
