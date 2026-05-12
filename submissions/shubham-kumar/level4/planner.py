#!/usr/bin/env python3
"""
Agent A: SMILE Implementation Planner

Input  (stdin):  JSON  {"industry": str, "usecase": str, "constraints": str}
Output (stdout): JSON  plan schema (validated by security.validate_plan_schema)

Queries:
  - smile_phase_detail  x3  (reality-emulation, concurrent-engineering, collaboration-to-innovate)
  - get_methodology_step    (reality-emulation — the first phase a team should execute)

Synthesizes via local Ollama LLM into a structured implementation plan.
All LPI tool calls are recorded in tools_used for provenance.
"""

import json
import os
import subprocess
import sys

import requests

from security import sanitize

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LPI_CMD = ["node", os.path.join(REPO_ROOT, "dist", "src", "index.js")]
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

PHASES = ["reality-emulation", "concurrent-engineering", "collaboration-to-innovate"]


# ── MCP helpers ──────────────────────────────────────────────────────────────

def _start_mcp() -> subprocess.Popen:
    proc = subprocess.Popen(
        LPI_CMD,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=REPO_ROOT,
    )
    init = {
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "planner-agent", "version": "1.0.0"},
        },
    }
    proc.stdin.write(json.dumps(init) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()
    return proc


def _call_tool(proc: subprocess.Popen, tool: str, args: dict) -> str:
    req = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        return f"[ERROR] No response from MCP for {tool}"
    resp = json.loads(line)
    if "result" in resp and "content" in resp["result"]:
        return resp["result"]["content"][0].get("text", "")
    return f"[ERROR] {resp.get('error', {}).get('message', 'unknown MCP error')}"


# ── LLM helper ───────────────────────────────────────────────────────────────

def _query_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.ConnectionError:
        return "[ERROR] Ollama not running. Start with: ollama serve"
    except requests.Timeout:
        return "[ERROR] Ollama timed out. Try a smaller model."
    except Exception as exc:
        return f"[ERROR] Ollama: {exc}"


# ── Core logic ────────────────────────────────────────────────────────────────

def run(industry: str, usecase: str, constraints: str) -> dict:
    proc = _start_mcp()
    tools_used = []

    phase_data = {}
    for phase in PHASES:
        raw = _call_tool(proc, "smile_phase_detail", {"phase": phase})
        phase_data[phase] = raw[:600]
        tools_used.append({"tool": "smile_phase_detail", "args": {"phase": phase}})

    steps = _call_tool(proc, "get_methodology_step", {"phase": "reality-emulation"})
    tools_used.append({"tool": "get_methodology_step", "args": {"phase": "reality-emulation"}})

    proc.terminate()
    proc.wait(timeout=5)

    prompt = f"""You are a SMILE methodology implementation planner for digital twins.

Project brief:
  Industry:    {industry}
  Use Case:    {usecase}
  Constraints: {constraints}

SMILE Phase Reference Data:
{json.dumps(phase_data, indent=2)[:2500]}

Step-by-Step Guide (Reality Emulation):
{steps[:600]}

Respond with ONLY a valid JSON object — no markdown, no explanation, just the JSON.
Use this exact schema:

{{
  "project": {{"industry": "{industry}", "usecase": "{usecase}", "constraints": "{constraints}"}},
  "phases": [
    {{
      "phase": "<phase-slug>",
      "priority": <1|2|3>,
      "rationale": "<why this phase, grounded in the data above, max 80 words>",
      "duration": "<estimated time given constraints>",
      "key_activities": ["<activity>", "<activity>"]
    }}
  ],
  "milestones": ["<milestone1>", "<milestone2>", "<milestone3>"],
  "risks": ["<risk1>", "<risk2>"],
  "tools_used": {json.dumps(tools_used)}
}}

Include all 3 phases ordered by priority. Output only the JSON object."""

    raw_llm = _query_ollama(prompt)

    # Extract JSON — LLMs sometimes wrap in markdown fences
    try:
        start = raw_llm.find("{")
        end = raw_llm.rfind("}") + 1
        if start >= 0 and end > start:
            plan = json.loads(raw_llm[start:end])
        else:
            raise ValueError("No JSON object found in LLM response")
    except (json.JSONDecodeError, ValueError):
        # Fallback plan constructed from raw LPI data so provenance is preserved
        plan = {
            "project": {"industry": industry, "usecase": usecase, "constraints": constraints},
            "phases": [
                {
                    "phase": "reality-emulation",
                    "priority": 1,
                    "rationale": "Establish a shared reality canvas before designing changes. Identify data sources and current-state gaps.",
                    "duration": "2-4 weeks",
                    "key_activities": ["Map current state", "Identify data sources", "Define KPIs"],
                },
                {
                    "phase": "concurrent-engineering",
                    "priority": 2,
                    "rationale": "Define scope collaboratively with stakeholders to avoid over-engineering early.",
                    "duration": "4-8 weeks",
                    "key_activities": ["Stakeholder workshops", "Scope document", "As-is vs to-be mapping"],
                },
                {
                    "phase": "collaboration-to-innovate",
                    "priority": 3,
                    "rationale": "Iterate with real feedback loops once baseline is established.",
                    "duration": "Ongoing",
                    "key_activities": ["Pilot deployment", "Feedback collection", "Model refinement"],
                },
            ],
            "milestones": ["Reality canvas approved", "Scope document signed off", "Pilot live with live data"],
            "risks": ["Scope creep without stakeholder lock-in", "Data access delays slowing Reality Emulation"],
            "tools_used": tools_used,
            "_fallback": True,
        }

    return plan


# ── Entry point (reads JSON from stdin, writes JSON to stdout) ─────────────

def main():
    raw = sys.stdin.read()
    try:
        inp = json.loads(raw)
        industry = sanitize(inp.get("industry", ""), "industry")
        usecase = sanitize(inp.get("usecase", ""), "usecase")
        constraints = sanitize(inp.get("constraints", ""), "constraints")
        if not all([industry, usecase, constraints]):
            raise ValueError("industry, usecase, and constraints are all required")
    except (json.JSONDecodeError, ValueError) as exc:
        json.dump({"error": str(exc)}, sys.stdout)
        sys.exit(1)

    plan = run(industry, usecase, constraints)
    json.dump(plan, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
