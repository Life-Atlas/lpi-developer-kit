#!/usr/bin/env python3
"""
Digital Twin ROI Scoper — Level 3 Submission
Track A: Agent Builders

Given an industry, use case, and resource constraints, this agent:
  1. Queries smile_overview    — full methodology map (grounds the LLM before reasoning)
  2. Queries get_insights      — scenario-specific implementation advice
  3. Queries get_case_studies  — real-world analogues in the same industry
  4. Queries query_knowledge   — relevant technical knowledge

Synthesizes via local Ollama LLM and outputs a structured ROI scope report with:
  - Realistic scope for the situation
  - Expected outcomes grounded in real case studies
  - Which SMILE phases to prioritize, and WHY (citing source tool)
  - What to skip/defer given constraints, with risk explanation
  - First 3 concrete actions
  - Full provenance: every claim traces back to a specific tool call

Requirements:
  pip install requests
  npm run build  (from lpi-developer-kit root)
  ollama serve && ollama pull qwen2.5:1.5b

Usage:
  python agent.py
  python agent.py --industry healthcare --usecase "patient flow optimization" --constraints "2 developers, 2 months, no cloud"
"""

import argparse
import json
import os
import subprocess
import sys

import requests

# --- Config ---
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LPI_SERVER_CMD = ["node", os.path.join(_REPO_ROOT, "dist", "src", "index.js")]
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

DIVIDER = "=" * 60


# --- MCP helpers ---

def _start_mcp() -> subprocess.Popen:
    proc = subprocess.Popen(
        LPI_SERVER_CMD,
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
            "clientInfo": {"name": "roi-scoper", "version": "0.2.0"},
        },
    }
    proc.stdin.write(json.dumps(init) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()  # consume init response

    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()
    return proc


def _call_tool(proc: subprocess.Popen, tool: str, args: dict) -> str:
    req = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
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
    if "error" in resp:
        return f"[ERROR] {resp['error'].get('message', 'unknown')}"
    return "[ERROR] Unexpected MCP response"


# --- Ollama helper ---

def _query_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json().get("response", "[No response]")
    except requests.ConnectionError:
        return "[ERROR] Cannot connect to Ollama. Run: ollama serve"
    except requests.Timeout:
        return "[ERROR] Ollama timed out. Try a smaller model."
    except Exception as exc:
        return f"[ERROR] Ollama: {exc}"


# --- Prompt builder ---

def _build_prompt(industry: str, usecase: str, constraints: str,
                  overview: str, insights: str, cases: str, knowledge: str) -> str:
    return f"""You are a digital twin implementation consultant using the SMILE methodology.
Your job is to give constraint-aware advice — not generic overviews.

A client has come to you with the following situation:
  Industry:    {industry}
  Use Case:    {usecase}
  Constraints: {constraints}

You have gathered data from four authoritative sources:

--- SOURCE 1: smile_overview() — full SMILE methodology map ---
{overview[:800]}

--- SOURCE 2: get_insights("{usecase} in {industry}") ---
{insights[:1600]}

--- SOURCE 3: get_case_studies("{industry}") ---
{cases[:1400]}

--- SOURCE 4: query_knowledge("{usecase} digital twin implementation") ---
{knowledge[:1200]}

Based ONLY on the sources above, produce a structured ROI Scope report.
For EVERY recommendation, state which source informed it and WHY it applies to this client's constraints.

## 1. Realistic Scope
What can realistically be achieved given the constraints? Be specific and honest about what's out of reach.
Cite [Source X] for each claim.

## 2. Expected Outcomes
Based on real-world cases in SOURCE 3, what results can this client expect?
Reference case studies by name. Explain why those cases are analogous to this situation.

## 3. SMILE Phases to Prioritize
Which 2-3 SMILE phases should this client focus on first?
For each: state the phase, explain WHY it fits the constraints (cite source), and give a realistic timeline.
The agent chose these phases because they align with both the scenario data and the constraint envelope.

## 4. What to Skip or Defer
Given the constraints, what should NOT be attempted yet?
Explain the specific risk of attempting it too early — cite the case study or insight that shows this risk.

## 5. First 3 Actions
Concrete steps they can take this week. Each action should cite the tool that informed it.

## 6. Decision Trace
For each major recommendation above, list:
  - The decision made
  - The reason (which source, what it said)
  - The constraint it addresses

## Sources
List each tool call with what it contributed:
Format: [Tool: tool_name(args)] — what it provided and which section used it
"""


# --- Main agent ---

def run_scoper(industry: str, usecase: str, constraints: str):
    print(f"\n{DIVIDER}")
    print("  Digital Twin ROI Scoper  v0.2")
    print(DIVIDER)
    print(f"  Industry:    {industry}")
    print(f"  Use Case:    {usecase}")
    print(f"  Constraints: {constraints}")
    print(f"{DIVIDER}\n")

    print("[1/4] Starting LPI server and querying smile_overview...")
    proc = _start_mcp()
    tools_used = []

    overview = _call_tool(proc, "smile_overview", {})
    tools_used.append(("smile_overview", {}))

    print("[2/4] Querying get_insights...")
    insights = _call_tool(proc, "get_insights", {
        "scenario": f"{usecase} in {industry}",
        "tier": "free"
    })
    tools_used.append(("get_insights", {"scenario": f"{usecase} in {industry}", "tier": "free"}))

    print("[3/4] Querying get_case_studies...")
    cases = _call_tool(proc, "get_case_studies", {"query": industry})
    tools_used.append(("get_case_studies", {"query": industry}))

    print("[4/4] Querying knowledge base...")
    knowledge = _call_tool(proc, "query_knowledge", {
        "query": f"{usecase} digital twin implementation"
    })
    tools_used.append(("query_knowledge", {"query": f"{usecase} digital twin implementation"}))

    proc.terminate()
    proc.wait(timeout=5)

    print("\nSending to Ollama for synthesis...\n")
    prompt = _build_prompt(industry, usecase, constraints, overview, insights, cases, knowledge)
    report = _query_ollama(prompt)

    print(f"\n{DIVIDER}")
    print("  ROI SCOPE REPORT")
    print(DIVIDER)
    print(report)

    print(f"\n{DIVIDER}")
    print("  PROVENANCE — LPI Tools Called")
    print(DIVIDER)
    for i, (name, args) in enumerate(tools_used, 1):
        arg_str = json.dumps(args) if args else "(no args)"
        print(f"  [{i}] {name}({arg_str})")
    print()


# --- Input validation ---

def _validate(value: str, field: str, max_len: int = 500) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field} cannot be empty")
    if len(value) > max_len:
        raise ValueError(f"{field} exceeds {max_len} chars")
    return value.strip()


# --- CLI ---

def _interactive() -> tuple[str, str, str]:
    print("\nDigital Twin ROI Scoper — Interactive Mode")
    print("Press Ctrl+C to exit.\n")
    industry = input("Industry (e.g. healthcare, manufacturing, smart buildings): ").strip()
    usecase = input("Use case (e.g. predictive maintenance, energy optimization): ").strip()
    constraints = input("Constraints (e.g. small team, 3 months, limited budget): ").strip()
    return industry, usecase, constraints


def main():
    global OLLAMA_MODEL
    parser = argparse.ArgumentParser(description="Digital Twin ROI Scoper")
    parser.add_argument("--industry", help="Target industry")
    parser.add_argument("--usecase", help="Specific use case")
    parser.add_argument("--constraints", help="Resource constraints")
    parser.add_argument("--model", help="Ollama model name", default=OLLAMA_MODEL)
    args = parser.parse_args()

    OLLAMA_MODEL = args.model

    if args.industry and args.usecase and args.constraints:
        industry, usecase, constraints = args.industry, args.usecase, args.constraints
    else:
        industry, usecase, constraints = _interactive()

    try:
        industry = _validate(industry, "industry")
        usecase = _validate(usecase, "usecase")
        constraints = _validate(constraints, "constraints")
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    run_scoper(industry, usecase, constraints)


if __name__ == "__main__":
    main()
