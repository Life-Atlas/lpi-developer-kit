#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
SMILE Digital Twin Advisor — Level 3 Agent
Author: Farhan Ahmed Siddique (Farhan-Ahmed-code)

An AI agent that connects to the LPI MCP server, queries SMILE methodology tools,
and uses a local Ollama LLM to produce explainable, source-cited answers.

Features:
  - Queries 4 LPI tools per question
  - Full provenance tracking (every answer cites which tool)
  - Interactive CLI mode (multi-turn conversation)
  - Single-question mode via CLI arg

Requirements:
  pip install requests
  Node.js + npm run build (in lpi-developer-kit root)
  ollama serve && ollama pull qwen2.5:1.5b

Usage:
  python agent.py "What is Phase 1 of SMILE?"
  python agent.py --interactive
"""

import json
import subprocess
import sys
import os
import requests
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LPI_CMD     = ["node", os.path.join(REPO_ROOT, "dist", "src", "index.js")]
OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

AGENT_NAME  = "SMILE Digital Twin Advisor"
AGENT_VER   = "1.0.0"
AUTHOR      = "Farhan Ahmed Siddique"

# ── MCP Helpers ────────────────────────────────────────────────────────────────

def start_mcp_server():
    """Start LPI MCP server subprocess and perform handshake."""
    proc = subprocess.Popen(
        LPI_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=REPO_ROOT,
    )
    # Initialize
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "smile-advisor", "version": AGENT_VER},
        },
    }) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()  # consume init response

    # Notify initialized
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()
    return proc


def call_tool(proc, tool_name: str, arguments: dict) -> str:
    """Call one LPI MCP tool and return its text result."""
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }) + "\n")
    proc.stdin.flush()

    line = proc.stdout.readline()
    if not line:
        return f"[ERROR] No response from MCP for {tool_name}"
    resp = json.loads(line)
    if "result" in resp and "content" in resp["result"]:
        return resp["result"]["content"][0].get("text", "")
    if "error" in resp:
        return f"[ERROR] {resp['error'].get('message', 'unknown')}"
    return "[ERROR] Unexpected MCP response"


def stop_mcp_server(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        pass

# ── Ollama ─────────────────────────────────────────────────────────────────────

def ask_llm(prompt: str) -> str:
    """Send prompt to Ollama, return response text."""
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        r.raise_for_status()
        return r.json().get("response", "[No response]")
    except requests.ConnectionError:
        return "[ERROR] Ollama not running. Run: ollama serve"
    except requests.Timeout:
        return "[ERROR] Ollama timed out (180s)."
    except Exception as e:
        return f"[ERROR] Ollama: {e}"

# ── Agent Core ─────────────────────────────────────────────────────────────────

def gather_context(question: str, verbose: bool = True) -> tuple[str, list]:
    """
    Query 4 LPI tools and return (combined_context, provenance_list).
    Provenance list: [(tool_name, args, snippet), ...]
    """
    proc = start_mcp_server()
    provenance = []

    def fetch(label, tool, args, max_chars=2000):
        if verbose:
            print(f"  → [{label}] {tool}({json.dumps(args) if args else ''})")
        result = call_tool(proc, tool, args)
        snippet = result[:max_chars]
        provenance.append({"tool": tool, "args": args, "chars": len(result), "snippet": snippet})
        return snippet

    # Tool 1 — SMILE overview (always useful as backbone)
    overview   = fetch("1/4", "smile_overview", {})

    # Tool 2 — Phase detail for Phase 1 (Reality Emulation) as contextual anchor
    phase_detail = fetch("2/4", "smile_phase_detail", {"phase": "reality-emulation"})

    # Tool 3 — Knowledge base search using the actual question
    knowledge  = fetch("3/4", "query_knowledge", {"query": question})

    # Tool 4 — Case studies for real-world grounding
    cases      = fetch("4/4", "get_case_studies", {})

    stop_mcp_server(proc)

    context = f"""
=== Tool 1: smile_overview ===
{overview}

=== Tool 2: smile_phase_detail (phase: reality-emulation) ===
{phase_detail}

=== Tool 3: query_knowledge("{question}") ===
{knowledge}

=== Tool 4: get_case_studies ===
{cases[:1500]}
""".strip()

    return context, provenance


def build_prompt(question: str, context: str) -> str:
    return f"""You are a SMILE Digital Twin methodology advisor. Use ONLY the context below to answer.
After your answer, include a "Sources" section citing which Tool (1-4) provided each key point.

{context}

===  User Question ===
{question}

Answer clearly and concisely. End with:
Sources:
[Tool N: <tool_name>] — what it contributed.
"""


def run_query(question: str, verbose: bool = True) -> dict:
    """Full pipeline: gather -> build prompt -> LLM -> return result dict."""
    if verbose:
        print(f"\n" + "-"*60)
        print(f"  Question: {question}")
        print("-"*60)
        print("  Gathering context from LPI tools...")

    context, provenance = gather_context(question, verbose)

    if verbose:
        print("  Reasoning with LLM...")

    prompt  = build_prompt(question, context)
    answer  = ask_llm(prompt)
    ts      = datetime.now().strftime("%H:%M:%S")

    return {"question": question, "answer": answer, "provenance": provenance, "timestamp": ts}


def print_result(result: dict):
    print("\n" + "="*60)
    print("  ANSWER")
    print("="*60 + "\n")
    print(result["answer"])
    print("\n" + "-"*60)
    print("  PROVENANCE (LPI tools queried)")
    print("-"*60)
    for i, p in enumerate(result["provenance"], 1):
        args_str = json.dumps(p["args"]) if p["args"] else "(no args)"
        print(f"  [{i}] {p['tool']} {args_str}  →  {p['chars']} chars retrieved")
    print(f"\n  Timestamp: {result['timestamp']}")

# ── Modes ──────────────────────────────────────────────────────────────────────

def interactive_mode():
    print("\n" + "="*60)
    print(f"  {AGENT_NAME} v{AGENT_VER}")
    print(f"  Author: {AUTHOR}")
    print(f"  Model:  {OLLAMA_MODEL} via Ollama")
    print(f"  LPI:    4 tools")
    print("="*60)
    print("  Type your question and press Enter. Type 'quit' to exit.\n")

    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break
        result = run_query(q)
        print_result(result)
        print()


def single_mode(question: str):
    result = run_query(question)
    print_result(result)


# ── Entry ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage:")
        print(f'  python agent.py "Your question"')
        print(f'  python agent.py --interactive')
        sys.exit(1)

    if sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        single_mode(" ".join(sys.argv[1:]))
