#!/usr/bin/env python3
"""
Orchestrator — Digital Twin Readiness Assessor + SMILE Roadmap Synthesiser

Chains two agents via A2A discovery:
  Agent A (readiness_agent.py): evidence-based readiness scoring using LPI cases/knowledge/insights
  Agent B (roadmap_agent.py):   gap-targeted SMILE roadmap using LPI methodology tools

Usage:
  python orchestrator.py --description "your project description"
  python orchestrator.py  (will prompt interactively)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid

import requests

sys.path.insert(0, os.path.dirname(__file__))
from security import (
    SecurityError,
    sanitize_input,
    validate_readiness_schema,
    validate_roadmap_schema,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
AGENT_A = os.path.join(_HERE, "readiness_agent.py")
AGENT_B = os.path.join(_HERE, "roadmap_agent.py")
CARD_A = os.path.join(_HERE, "readiness_agent.json")
CARD_B = os.path.join(_HERE, "roadmap_agent.json")
AGENT_TIMEOUT = 300
OLLAMA_URL = "http://localhost:11434"

_ollama_proc = None  # track background process so we don't start it twice


def _ollama_running() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def ensure_ollama():
    """Start ollama serve in the background if it isn't already running."""
    global _ollama_proc
    if _ollama_running():
        print("[setup] Ollama is already running.")
        return
    print("[setup] Starting Ollama in the background...")
    # Suppress all output from ollama serve so it doesn't clutter the terminal
    _ollama_proc = subprocess.Popen(
        "ollama serve",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True,
    )
    for attempt in range(15):
        time.sleep(2)
        if _ollama_running():
            print("[setup] Ollama is ready.")
            return
    print("[setup] WARNING: Ollama did not become ready in 30s — agents will use fallback mode.")


def ensure_lpi_built():
    """Run npm install + npm run build if dist/src/index.js doesn't exist."""
    dist = os.path.join(_REPO_ROOT, "dist", "src", "index.js")
    if os.path.exists(dist):
        print("[setup] LPI server already built.")
        return

    node_modules = os.path.join(_REPO_ROOT, "node_modules")
    if not os.path.exists(node_modules):
        print("[setup] Installing dependencies (npm install)...")
        r = subprocess.run(
            "npm install",
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            shell=True,
        )
        if r.returncode != 0:
            print(f"[setup] ERROR: npm install failed:\n{r.stderr[-500:]}")
            sys.exit(1)
        print("[setup] Dependencies installed.")

    print("[setup] Building LPI server (npm run build)...")
    result = subprocess.run(
        "npm run build",
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode != 0:
        print(f"[setup] ERROR: npm run build failed:\n{result.stderr[-500:]}")
        sys.exit(1)
    print("[setup] LPI server built successfully.")


def discover_agent(card_path: str) -> dict:
    """Read and display an A2A Agent Card."""
    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)
    tools = card.get("_lpiMetadata", {}).get("lpiToolsUsed", [])
    print(f"  Found: {card['name']}  v{card.get('version', '?')}")
    print(f"         LPI tools: {', '.join(tools)}")
    for skill in card.get("skills", []):
        print(f"         Skill: {skill['name']}")
    return card


def invoke_agent(script: str, payload: dict, label: str) -> dict:
    """Run an agent script, passing payload as JSON to stdin. Returns parsed output."""
    try:
        result = subprocess.run(
            [sys.executable, script],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=AGENT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] {label} timed out after {AGENT_TIMEOUT}s.")
        sys.exit(1)

    stderr = result.stderr.strip()
    if stderr:
        # Filter node.js startup noise; surface real errors
        for line in stderr.splitlines():
            if any(kw in line.lower() for kw in ("error", "warn", "traceback", "exception")):
                if "deprecat" not in line.lower():
                    print(f"  [STDERR] {line}", file=sys.stderr)

    stdout = result.stdout.strip()
    if not stdout:
        print(f"\n[ERROR] {label} produced no output.")
        sys.exit(1)

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        print(f"\n[ERROR] {label} returned non-JSON output:\n{stdout[:200]}")
        sys.exit(1)

    if "error" in data:
        print(f"\n[ERROR] {label} returned an error: {data['error']}")
        sys.exit(1)

    return data


def _severity_bar(score: int) -> str:
    filled = "#" * score
    empty = "-" * (5 - score)
    return f"[{filled}{empty}] {score}/5"


def print_report(description: str, readiness: dict, roadmap: dict) -> None:
    w = 65
    print("\n" + "=" * w)
    print("  DIGITAL TWIN READINESS ASSESSMENT + SMILE ROADMAP")
    print("=" * w)
    print(f"\nProject: {description[:80]}")
    print(f"Trace ID: {readiness.get('request_id', 'n/a')}")
    if readiness.get("_fallback"):
        print("  [NOTE] Readiness Agent ran in fallback mode (LLM unavailable)")

    print(f"\n{'─'*w}")
    print("  AGENT A — READINESS ASSESSMENT")
    print(f"{'─'*w}")
    for dim in readiness.get("readiness_dimensions", []):
        label = dim["dimension"].replace("_", " ").title()
        bar = _severity_bar(dim["score"])
        sev = dim["gap_severity"].upper()
        print(f"\n  {label}")
        print(f"    Score:    {bar}")
        print(f"    Gap:      {sev}")
        print(f"    Finding:  {dim['finding']}")
        print(f"    Source:   [{dim['evidence_source']}]")

    overall = readiness.get("overall_readiness_score", "?")
    print(f"\n  Overall Readiness: {_severity_bar(overall) if isinstance(overall, int) else overall}")
    print(f"  Top Gaps:          {', '.join(readiness.get('top_gaps', []))}")
    print(f"  Starting Phase:    {readiness.get('recommended_starting_phase', '?')}")

    print(f"\n{'─'*w}")
    print("  AGENT B — SMILE ROADMAP  (targeting your top gaps)")
    print(f"{'─'*w}")
    if roadmap.get("_fallback"):
        print("  [NOTE] Roadmap Agent ran in fallback mode (LLM unavailable)")

    for phase in roadmap.get("phases", []):
        print(f"\n  Phase {phase['priority']}: {phase['phase_name']}  ({phase.get('duration', '?')})")
        print(f"    Addresses gap: {phase['addresses_gap'].replace('_', ' ').title()}")
        print(f"    Source:        [{phase['evidence_source']}]")
        print(f"    Actions:")
        for action in phase.get("immediate_actions", []):
            print(f"      • {action}")

    print(f"\n  First-Week Checklist:")
    for i, action in enumerate(roadmap.get("first_week_actions", []), 1):
        print(f"    {i}. {action}")

    print(f"\n{'─'*w}")
    print("  PROVENANCE — All LPI Tool Calls")
    print(f"{'─'*w}")
    all_tools = [
        ("Agent A", readiness.get("tools_used", [])),
        ("Agent B", roadmap.get("tools_used", [])),
    ]
    for agent_label, tool_list in all_tools:
        for entry in tool_list:
            args_str = json.dumps(entry.get("args", {}))
            chars = entry.get("returned_chars", "?")
            print(f"  [{agent_label}] {entry['tool']} {args_str}  → {chars} chars")

    print(f"\n{'='*w}\n")


def main():
    parser = argparse.ArgumentParser(description="Digital Twin Readiness + Roadmap Mesh")
    parser.add_argument("--description", "-d", type=str, default=None,
                        help="Describe the digital twin project to assess (max 400 chars)")
    args = parser.parse_args()

    if args.description:
        raw_desc = args.description
    else:
        print("Digital Twin Readiness Assessor + SMILE Roadmap Synthesiser")
        print("Describe your digital twin project (max 400 chars):")
        raw_desc = input("> ").strip()

    try:
        description = sanitize_input(raw_desc, field="description")
    except SecurityError as e:
        print(str(e))
        sys.exit(1)

    if not description:
        print("[ERROR] Description cannot be empty.")
        sys.exit(1)

    request_id = str(uuid.uuid4())

    # Auto-start prerequisites
    ensure_lpi_built()
    ensure_ollama()

    # A2A Discovery
    print(f"\n[A2A] Discovering agents via Agent Cards...")
    discover_agent(CARD_A)
    discover_agent(CARD_B)

    # Invoke Agent A
    print(f"\n[Mesh] Invoking Agent A (Readiness Analyst)...")
    readiness = invoke_agent(AGENT_A, {"description": description, "request_id": request_id}, "Agent A")

    # Validate schema before passing to Agent B
    try:
        validate_readiness_schema(readiness)
    except SecurityError as e:
        print(f"\n[ERROR] Agent A output failed schema validation: {e}")
        sys.exit(1)

    # Invoke Agent B
    print(f"[Mesh] Invoking Agent B (Roadmap Synthesiser)...")
    roadmap = invoke_agent(AGENT_B, readiness, "Agent B")

    # Validate Agent B output
    try:
        validate_roadmap_schema(roadmap)
    except SecurityError as e:
        print(f"\n[ERROR] Agent B output failed schema validation: {e}")
        sys.exit(1)

    print_report(description, readiness, roadmap)


if __name__ == "__main__":
    main()
