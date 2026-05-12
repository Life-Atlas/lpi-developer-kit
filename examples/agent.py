#!/usr/bin/env python3
"""
LPI Sandbox Agent — Example Level 3 Submission

Connects to the LPI MCP server (stdio), queries SMILE methodology tools,
passes results to a local LLM via Ollama, and returns an explainable answer.

Requirements:
  - Node.js (for the LPI MCP server)
  - Ollama running locally (ollama serve)
  - A pulled model: ollama pull qwen2.5:1.5b
  - Python 3.10+
  - requests: pip install requests

Usage:
  cd lpi-developer-kit
  npm run build
  python examples/agent.py "What are the phases of SMILE and how do I start?"
"""

import json
import subprocess
import sys
import requests

# --- Configuration ---
import os as _os
_REPO_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
LPI_SERVER_CMD = ["node", _os.path.join(_REPO_ROOT, "dist", "src", "index.js")]
LPI_SERVER_CWD = _REPO_ROOT  # always resolves to repo root regardless of where you run from
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:0.5b"


def call_mcp_tool(process, tool_name: str, arguments: dict) -> str:
    """Send a JSON-RPC request to the MCP server and return the text result."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    line = process.stdout.readline()
    if not line:
        return f"[ERROR] No response from MCP server for {tool_name}"
    resp = json.loads(line)
    if "result" in resp and "content" in resp["result"]:
        return resp["result"]["content"][0].get("text", "")
    if "error" in resp:
        return f"[ERROR] {resp['error'].get('message', 'Unknown error')}"
    return "[ERROR] Unexpected response format"


def query_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and return the full response."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "[No response from model]")
    except requests.ConnectionError:
        return "[ERROR] Cannot connect to Ollama. Is it running? (ollama serve)"
    except requests.Timeout:
        return "[ERROR] Ollama request timed out."
    except Exception as e:
        return f"[ERROR] Ollama error: {e}"


def run_agent(question: str):
    """Main agent loop: gather context from LPI tools, then reason with LLM."""
    print(f"\n{'='*60}")
    print(f"  LPI Agent — Question: {question}")
    print(f"{'='*60}\n")

    # Start the MCP server as a subprocess
    proc = subprocess.Popen(
        LPI_SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=LPI_SERVER_CWD,
    )

    # MCP initialization handshake
    init_req = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "lpi-example-agent", "version": "0.1.0"},
        },
    }
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()  # read init response

    # Send initialized notification
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    proc.stdin.write(json.dumps(notif) + "\n")
    proc.stdin.flush()

    # --- Step 1: Gather context from LPI tools ---
    tools_used = []

    print("[1/3] Querying SMILE overview...")
    overview = call_mcp_tool(proc, "smile_overview", {})
    tools_used.append(("smile_overview", {}))

    print("[2/3] Searching knowledge base...")
    knowledge = call_mcp_tool(proc, "query_knowledge", {"query": question})
    tools_used.append(("query_knowledge", {"query": question}))

    print("[3/3] Checking case studies...")
    cases = call_mcp_tool(proc, "get_case_studies", {})
    tools_used.append(("get_case_studies", {}))

    # Clean up MCP server
    proc.terminate()
    proc.wait(timeout=5)

    # --- Step 2: Build prompt with provenance ---
    prompt = f"""You are a digital twin methodology advisor. Answer the user's question
using ONLY the context provided below. Cite which source (Tool 1, Tool 2, or Tool 3)
each part of your answer comes from.

--- Tool 1: smile_overview ---
{overview[:2000]}

--- Tool 2: query_knowledge("{question}") ---
{knowledge[:2000]}

--- Tool 3: get_case_studies ---
{cases[:1500]}

--- User Question ---
{question}

Answer concisely. After your answer, add a "Sources" section listing which tools
provided which parts of your answer. Format: [Tool N: tool_name] - what it contributed.
"""

    print("\nSending to LLM (Ollama)...\n")
    answer = query_ollama(prompt)

    # --- Step 3: Print explainable result ---
    print(f"\n{'='*60}")
    print("  ANSWER")
    print(f"{'='*60}\n")
    print(answer)

    print(f"\n{'='*60}")
    print("  PROVENANCE (tools used)")
    print(f"{'='*60}")
    for i, (name, args) in enumerate(tools_used, 1):
        args_str = json.dumps(args) if args else "(no args)"
        print(f"  [{i}] {name} {args_str}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python agent.py "Your question about digital twins"')
        print('Example: python agent.py "What is the SMILE methodology?"')
        sys.exit(1)
    run_agent(sys.argv[1])
