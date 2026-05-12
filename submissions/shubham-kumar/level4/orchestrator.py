#!/usr/bin/env python3
"""
Level 4 Orchestrator — Secure Agent Mesh

Flow:
  1. A2A Discovery  — reads planner.json and validator.json to find agent capabilities
  2. Input          — sanitize user input (blocks prompt injection before it reaches agents)
  3. Agent A        — invoke planner.py via subprocess, receive structured plan JSON
  4. Agent B        — invoke validator.py via subprocess, pass plan JSON, receive critique JSON
  5. Report         — merge plan + critique into a final explainable report with provenance

Security layers:
  - User input is sanitized BEFORE it touches any agent (injection, length)
  - Inter-agent messages are validated against JSON schemas (privilege escalation)
  - Subprocess timeout prevents DoS from runaway agents
  - Errors are surfaced cleanly without leaking internal state

Usage:
  python orchestrator.py
  python orchestrator.py --industry healthcare --usecase "patient flow" --constraints "2 devs, 2 months"
"""

import argparse
import json
import os
import subprocess
import sys

from security import sanitize, validate_plan_schema, validate_critique_schema

HERE = os.path.dirname(os.path.abspath(__file__))
DIVIDER = "=" * 66


# ── A2A discovery ─────────────────────────────────────────────────────────────

def discover_agent(card_path: str) -> dict:
    """
    Read an A2A Agent Card from disk and return its parsed contents.
    In a real deployment this would be an HTTP GET to /.well-known/agent.json.
    """
    with open(card_path, encoding="utf-8") as f:
        return json.load(f)


# ── Agent invocation ──────────────────────────────────────────────────────────

def invoke_agent(script: str, payload: dict, timeout: int = 300) -> dict:
    """
    Spawn an agent as a subprocess, send payload as JSON on stdin,
    read JSON response from stdout.
    """
    result = subprocess.run(
        [sys.executable, os.path.join(HERE, script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=HERE,
    )
    if result.returncode != 0:
        stderr_snippet = result.stderr.strip()[:400]
        raise RuntimeError(f"{script} exited with code {result.returncode}: {stderr_snippet}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        snippet = result.stdout.strip()[:300]
        raise RuntimeError(f"{script} returned non-JSON output: {snippet}")


# ── Report renderer ───────────────────────────────────────────────────────────

def print_report(inp: dict, plan: dict, critique: dict) -> None:
    print(f"\n{DIVIDER}")
    print("  SECURE AGENT MESH — Final Report")
    print(DIVIDER)
    print(f"  Industry:    {inp['industry']}")
    print(f"  Use Case:    {inp['usecase']}")
    print(f"  Constraints: {inp['constraints']}")
    print(DIVIDER)

    # ── Plan ──
    print("\n## IMPLEMENTATION PLAN  [Agent A: SMILE Planner]")
    for phase in plan.get("phases", []):
        print(f"\n  [{phase.get('priority', '?')}] {phase.get('phase', '?').upper()}")
        print(f"      Duration:   {phase.get('duration', 'TBD')}")
        print(f"      Rationale:  {phase.get('rationale', '')}")
        acts = phase.get("key_activities", [])
        if acts:
            print(f"      Activities: {', '.join(acts)}")

    milestones = plan.get("milestones", [])
    if milestones:
        print(f"\n  Milestones: {' → '.join(milestones)}")

    plan_risks = plan.get("risks", [])
    if plan_risks:
        print(f"\n  Planner-identified risks: {'; '.join(plan_risks)}")

    # ── Critique ──
    verdict = critique.get("verdict", "unknown").upper().replace("_", " ")
    score = critique.get("risk_score", "?")
    print(f"\n{DIVIDER}")
    print(f"## VALIDATION  [Agent B: Devil's Advocate]  |  Verdict: {verdict}  |  Risk: {score}/10")
    print(DIVIDER)

    red_flags = critique.get("red_flags", [])
    if red_flags:
        print("\n  RED FLAGS:")
        for flag in red_flags:
            print(f"    !  {flag}")

    validated = critique.get("validated_phases", [])
    if validated:
        print(f"\n  Validated (evidence-backed): {', '.join(validated)}")

    print("\n  CRITIQUES BY PHASE:")
    for c in critique.get("critiques", []):
        print(f"\n    Phase:   {c.get('phase', '?')}")
        print(f"    Risk:    {c.get('risk_level', '?').upper()}")
        print(f"    Finding: {c.get('finding', '')}")
        print(f"    Source:  [{c.get('evidence_source', 'LPI')}]")

    rec = critique.get("recommendation", "")
    if rec:
        print(f"\n  RECOMMENDATION: {rec}")

    # ── Provenance ──
    print(f"\n{DIVIDER}")
    print("  PROVENANCE — All LPI Tool Calls")
    print(DIVIDER)
    print("  Agent A (Planner):")
    for t in plan.get("tools_used", []):
        print(f"    • {t['tool']}({json.dumps(t['args'])})")
    print("  Agent B (Validator):")
    for t in critique.get("tools_used", []):
        print(f"    • {t['tool']}({json.dumps(t['args'])})")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _interactive() -> tuple:
    print("\nSecure Agent Mesh — Interactive Mode  (Ctrl+C to exit)\n")
    industry = input("Industry (e.g. healthcare, manufacturing): ").strip()
    usecase = input("Use case (e.g. predictive maintenance): ").strip()
    constraints = input("Constraints (e.g. 2 devs, 3 months, no cloud): ").strip()
    return industry, usecase, constraints


def main():
    parser = argparse.ArgumentParser(description="Level 4 — Secure Agent Mesh Orchestrator")
    parser.add_argument("--industry", help="Target industry")
    parser.add_argument("--usecase", help="Specific use case")
    parser.add_argument("--constraints", help="Resource constraints")
    args = parser.parse_args()

    if args.industry and args.usecase and args.constraints:
        industry, usecase, constraints = args.industry, args.usecase, args.constraints
    else:
        industry, usecase, constraints = _interactive()

    # ── Security gate: sanitize all user inputs before passing to any agent ──
    try:
        industry = sanitize(industry, "industry")
        usecase = sanitize(usecase, "usecase")
        constraints = sanitize(constraints, "constraints")
    except ValueError as exc:
        print(f"\n[BLOCKED] Input rejected: {exc}")
        sys.exit(1)

    if not all([industry, usecase, constraints]):
        print("[ERROR] All three inputs are required.")
        sys.exit(1)

    inp = {"industry": industry, "usecase": usecase, "constraints": constraints}

    # ── A2A Discovery ──
    print(f"\n{DIVIDER}")
    print("  [A2A] Discovering agents via Agent Cards...")
    print(DIVIDER)
    try:
        planner_card = discover_agent(os.path.join(HERE, "planner.json"))
        validator_card = discover_agent(os.path.join(HERE, "validator.json"))
    except FileNotFoundError as exc:
        print(f"[ERROR] Agent card not found: {exc}")
        sys.exit(1)

    print(f"  Found: {planner_card['name']}  v{planner_card['version']}")
    print(f"         Skill: {planner_card['skills'][0]['id']} — {planner_card['skills'][0]['description'][:60]}...")
    print(f"  Found: {validator_card['name']}  v{validator_card['version']}")
    print(f"         Skill: {validator_card['skills'][0]['id']} — {validator_card['skills'][0]['description'][:60]}...")

    # ── Agent A: Planner ──
    print(f"\n[1/2] Invoking Agent A: {planner_card['name']}...")
    try:
        plan = invoke_agent("planner.py", inp, timeout=300)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"[ERROR] Planner failed: {exc}")
        sys.exit(1)

    if "error" in plan:
        print(f"[BLOCKED] Planner rejected input: {plan['error']}")
        sys.exit(1)

    # Validate plan schema before sending to Agent B
    try:
        validate_plan_schema(plan)
    except ValueError as exc:
        print(f"[ERROR] Planner returned invalid plan: {exc}")
        sys.exit(1)

    print("       Plan received. Passing to Agent B...")

    # ── Agent B: Validator ──
    print(f"[2/2] Invoking Agent B: {validator_card['name']}...")
    try:
        critique = invoke_agent("validator.py", plan, timeout=300)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"[ERROR] Validator failed: {exc}")
        sys.exit(1)

    if "error" in critique:
        print(f"[BLOCKED] Validator rejected plan: {critique['error']}")
        sys.exit(1)

    try:
        validate_critique_schema(critique)
    except ValueError as exc:
        print(f"[ERROR] Validator returned invalid critique: {exc}")
        sys.exit(1)

    # ── Final report ──
    print_report(inp, plan, critique)


if __name__ == "__main__":
    main()
