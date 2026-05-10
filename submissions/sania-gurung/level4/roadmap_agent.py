#!/usr/bin/env python3
"""
Agent B — SMILE Roadmap Synthesiser

Receives a ReadinessReport from Agent A, identifies the 2 highest-severity
gaps, then calls 4 LPI methodology tools (smile_overview, smile_phase_detail x2,
get_methodology_step) to produce a gap-targeted SMILERoadmap JSON.

Input  (stdin):  ReadinessReport JSON (output of readiness_agent.py)
Output (stdout): SMILERoadmap JSON
"""

import json
import os
import subprocess
import sys

import requests

sys.path.insert(0, os.path.dirname(__file__))
from security import (
    SecurityError,
    sanitize_interagent_strings,
    validate_readiness_schema,
)

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
            "clientInfo": {"name": "roadmap-agent", "version": "1.0.0"},
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
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _pick_top_gaps(report: dict) -> list[str]:
    """Return the 2 dimension names with highest gap_severity (then lowest score)."""
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    dims = sorted(
        report["readiness_dimensions"],
        key=lambda d: (severity_rank.get(d.get("gap_severity", "low"), 2), d.get("score", 5))
    )
    return [d["dimension"] for d in dims[:2]]


def _build_fallback(report: dict, top_gaps: list, tools_used: list) -> dict:
    return {
        "schema_version": "1.0",
        "request_id": report["request_id"],
        "gap_addressed": top_gaps,
        "phases": [
            {
                "phase_slug": "reality-emulation",
                "phase_name": "Reality Emulation",
                "priority": 1,
                "addresses_gap": top_gaps[0] if top_gaps else "data_maturity",
                "duration": "2-4 weeks",
                "immediate_actions": [
                    "Define the 3 most important data sources to capture",
                    "Set up a simple data logging mechanism (even a spreadsheet)"
                ],
                "evidence_source": "smile_overview",
            }
        ],
        "first_week_actions": [
            "List all data sources currently available",
            "Identify one stakeholder to review progress with weekly",
            "Set up a basic version control or notes system for the project"
        ],
        "tools_used": tools_used,
        "_fallback": True,
    }


def run(report: dict) -> dict:
    top_gaps = _pick_top_gaps(report)
    recommended_phase = report.get("recommended_starting_phase", "reality-emulation")

    tools_used = []
    proc = _start_mcp()
    try:
        overview = _call_tool(proc, "smile_overview", {})
        tools_used.append({"tool": "smile_overview", "args": {}, "returned_chars": len(overview)})

        phase1 = _call_tool(proc, "smile_phase_detail", {"phase": recommended_phase})
        tools_used.append({"tool": "smile_phase_detail",
                           "args": {"phase": recommended_phase}, "returned_chars": len(phase1)})

        second_phase = "contextual-intelligence" if recommended_phase != "contextual-intelligence" else "predictive-insight"
        phase2 = _call_tool(proc, "smile_phase_detail", {"phase": second_phase})
        tools_used.append({"tool": "smile_phase_detail",
                           "args": {"phase": second_phase}, "returned_chars": len(phase2)})

        steps = _call_tool(proc, "get_methodology_step", {"phase": recommended_phase})
        tools_used.append({"tool": "get_methodology_step",
                           "args": {"phase": recommended_phase}, "returned_chars": len(steps)})
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    gaps_summary = "\n".join(
        f"  - {d['dimension']} (score {d['score']}/5, {d['gap_severity']} severity): {d['finding']}"
        for d in report["readiness_dimensions"]
    )

    prompt = f"""You are a SMILE methodology roadmap designer.

Given the readiness gaps below, create a targeted implementation roadmap using the LPI methodology evidence.
Return a JSON object with EXACTLY this structure (no markdown, no extra text):

{{
  "schema_version": "1.0",
  "request_id": "{report['request_id']}",
  "gap_addressed": {json.dumps(top_gaps)},
  "phases": [
    {{
      "phase_slug": "<slug from SMILE phases>",
      "phase_name": "<full phase name>",
      "priority": 1,
      "addresses_gap": "<which gap dimension this phase targets>",
      "duration": "<estimated duration>",
      "immediate_actions": ["<concrete action>", "<concrete action>"],
      "evidence_source": "smile_phase_detail"
    }},
    {{
      "phase_slug": "<slug>",
      "phase_name": "<name>",
      "priority": 2,
      "addresses_gap": "<gap dimension>",
      "duration": "<duration>",
      "immediate_actions": ["<action>", "<action>"],
      "evidence_source": "smile_phase_detail"
    }}
  ],
  "first_week_actions": ["<do this on day 1>", "<do this by day 3>", "<do this by end of week>"],
  "tools_used": []
}}

PROJECT READINESS GAPS:
{gaps_summary}

TOP GAPS TO ADDRESS: {', '.join(top_gaps)}

--- LPI Evidence: smile_overview ---
{overview[:1500]}

--- LPI Evidence: smile_phase_detail("{recommended_phase}") ---
{phase1[:1000]}

--- LPI Evidence: smile_phase_detail("{second_phase}") ---
{phase2[:1000]}

--- LPI Evidence: get_methodology_step("{recommended_phase}") ---
{steps[:800]}

Instructions:
- Each phase must name exactly which gap dimension it addresses in the 'addresses_gap' field
- immediate_actions must be concrete (not "plan something" — "do something specific")
- first_week_actions must be actionable on day 1
- Return ONLY the JSON object, no explanation"""

    raw = _query_ollama(prompt)
    parsed = _extract_json(raw) if raw else None

    if parsed is None:
        result = _build_fallback(report, top_gaps, tools_used)
    else:
        parsed["schema_version"] = "1.0"
        parsed["request_id"] = report["request_id"]
        parsed["gap_addressed"] = top_gaps
        parsed["tools_used"] = tools_used
        result = parsed

    return result


def main():
    raw_input = sys.stdin.read().strip()
    try:
        report = json.loads(raw_input)
    except json.JSONDecodeError:
        print(json.dumps({"error": "[SECURITY] Invalid JSON — schema validation failed"}))
        sys.exit(1)

    # Security gate: validate schema BEFORE any processing (privilege escalation defence)
    try:
        validate_readiness_schema(report)
    except SecurityError as e:
        print(json.dumps({"error": f"[SECURITY] schema validation failed: {e}"}))
        sys.exit(1)

    # Re-sanitize string fields from Agent A before they touch any LLM prompt
    interagent_fields = ["project.description"]
    for i in range(len(report.get("readiness_dimensions", []))):
        interagent_fields.append(f"readiness_dimensions.{i}.finding")
    try:
        report = sanitize_interagent_strings(report, interagent_fields)
    except SecurityError as e:
        print(json.dumps({"error": f"[SECURITY] inter-agent sanitization failed: {e}"}))
        sys.exit(1)

    result = run(report)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
