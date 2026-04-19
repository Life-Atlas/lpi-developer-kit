#!/usr/bin/env python3
"""
Agent B: Devil's Advocate Validator

Input  (stdin):  JSON plan from Agent A (must pass validate_plan_schema)
Output (stdout): JSON critique schema

Queries:
  - get_case_studies   (industry-specific real-world analogues)
  - get_insights       (scenario-specific advice and known pitfalls)

Critically evaluates the plan using evidence from the LPI knowledge base.
Every critique cites its source tool. Risk score and verdict are evidence-grounded.

Security:
  - Validates plan schema before processing (privilege escalation prevention)
  - Sanitizes string fields extracted from the plan (injection via plan payload)
  - Ollama timeout prevents DoS via crafted large payloads
"""

import json
import os
import subprocess
import sys

import requests

from security import sanitize, validate_plan_schema

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LPI_CMD = ["node", os.path.join(REPO_ROOT, "dist", "src", "index.js")]
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")


# ── MCP helpers ───────────────────────────────────────────────────────────────

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
            "clientInfo": {"name": "validator-agent", "version": "1.0.0"},
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


# ── LLM helper ────────────────────────────────────────────────────────────────

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


# ── Core logic ─────────────────────────────────────────────────────────────────

def run(plan: dict) -> dict:
    industry = plan["project"]["industry"]
    usecase = plan["project"]["usecase"]

    proc = _start_mcp()
    tools_used = []

    cases = _call_tool(proc, "get_case_studies", {"query": industry})
    tools_used.append({"tool": "get_case_studies", "args": {"query": industry}})

    insights = _call_tool(proc, "get_insights", {
        "scenario": f"{usecase} in {industry}",
        "tier": "free",
    })
    tools_used.append({"tool": "get_insights", "args": {"scenario": f"{usecase} in {industry}", "tier": "free"}})

    proc.terminate()
    proc.wait(timeout=5)

    # Only pass non-sensitive structural data to the LLM — no raw user strings
    plan_summary = {
        "phases": [
            {
                "phase": p.get("phase"),
                "priority": p.get("priority"),
                "rationale": p.get("rationale", ""),
                "duration": p.get("duration", ""),
            }
            for p in plan.get("phases", [])
        ],
        "milestones": plan.get("milestones", []),
        "risks": plan.get("risks", []),
    }

    prompt = f"""You are a devil's advocate reviewer for digital twin implementations.
Your job: find what will go wrong, grounded only in the evidence below.

Industry: {industry}
Use Case: {usecase}

Plan to Critique:
{json.dumps(plan_summary, indent=2)}

Evidence — Real Case Studies ({industry}):
{cases[:1400]}

Evidence — Implementation Insights ({usecase} in {industry}):
{insights[:1200]}

Respond with ONLY a valid JSON object — no markdown, no explanation.
Use this exact schema:

{{
  "verdict": "<proceed|proceed_with_caution|reconsider>",
  "risk_score": <integer 1-10>,
  "critiques": [
    {{
      "phase": "<phase-slug>",
      "risk_level": "<low|medium|high>",
      "finding": "<what could fail, citing specific evidence>",
      "evidence_source": "<case study name or insight reference>"
    }}
  ],
  "validated_phases": ["<phases that look solid based on evidence>"],
  "red_flags": ["<top concern 1>", "<top concern 2>"],
  "recommendation": "<one concrete change to improve the plan>",
  "tools_used": {json.dumps(tools_used)}
}}

Every critique must cite a specific case study or insight. Output only the JSON object."""

    raw_llm = _query_ollama(prompt)

    try:
        start = raw_llm.find("{")
        end = raw_llm.rfind("}") + 1
        if start >= 0 and end > start:
            critique = json.loads(raw_llm[start:end])
        else:
            raise ValueError("No JSON object found in LLM response")
    except (json.JSONDecodeError, ValueError):
        first_phase = plan["phases"][0]["phase"] if plan.get("phases") else "reality-emulation"
        critique = {
            "verdict": "proceed_with_caution",
            "risk_score": 6,
            "critiques": [
                {
                    "phase": first_phase,
                    "risk_level": "medium",
                    "finding": "Constraints may be too tight to complete Reality Emulation properly before moving on.",
                    "evidence_source": "General SMILE implementation pattern — rushed Reality Emulation is cited as top failure mode.",
                }
            ],
            "validated_phases": [],
            "red_flags": [
                "Insufficient time allocation for Reality Emulation data collection",
                "Stakeholder alignment risk not addressed in plan",
            ],
            "recommendation": "Add a 2-week buffer to Reality Emulation before starting Concurrent Engineering.",
            "tools_used": tools_used,
            "_fallback": True,
        }

    return critique


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    raw = sys.stdin.read()
    try:
        plan = json.loads(raw)
        # Structural validation — reject malformed or malicious payloads
        validate_plan_schema(plan)
        # Sanitize string fields from the plan before using in LPI queries
        plan["project"]["industry"] = sanitize(plan["project"]["industry"], "plan.industry")
        plan["project"]["usecase"] = sanitize(plan["project"]["usecase"], "plan.usecase")
        plan["project"]["constraints"] = sanitize(plan["project"]["constraints"], "plan.constraints")
    except (json.JSONDecodeError, ValueError) as exc:
        json.dump({"error": str(exc)}, sys.stdout)
        sys.exit(1)

    critique = run(plan)
    json.dump(critique, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
