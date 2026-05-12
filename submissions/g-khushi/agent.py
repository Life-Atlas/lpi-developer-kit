#!/usr/bin/env python3
import json
import subprocess
import sys
import requests
import os

# --- Configuration ---
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LPI_SERVER_CMD = ["node", os.path.join(REPO_ROOT, "dist", "src", "index.js")]
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"


def call_mcp_tool(process, tool_name: str, arguments: dict) -> str:
    """Call MCP tool with error handling"""
    try:
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
            return f"[ERROR] No response from {tool_name}"

        resp = json.loads(line)

        if "result" in resp and "content" in resp["result"]:
            return resp["result"]["content"][0].get("text", "")

        if "error" in resp:
            return f"[ERROR] {resp['error'].get('message')}"

        return "[ERROR] Unexpected response format"

    except Exception as e:
        return f"[ERROR] Tool {tool_name} failed: {str(e)}"


def query_ollama(prompt: str) -> str:
    """Query LLM with strong error handling"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )

        response.raise_for_status()
        return response.json().get("response", "[No response from model]")

    except requests.ConnectionError:
        return "[ERROR] Ollama not running. Start using: ollama serve"

    except requests.Timeout:
        return "[ERROR] Ollama request timed out"

    except Exception as e:
        return f"[ERROR] LLM failure: {str(e)}"


def run_agent(question: str):
    """Main agent logic"""

    # 🔴 INPUT VALIDATION (NEW)
    if not question or len(question.strip()) == 0:
        print("❌ Please enter a valid question.")
        return

    print("\n" + "=" * 60)
    print(f"LPI Agent — Question: {question}")
    print("=" * 60 + "\n")

    try:
        proc = subprocess.Popen(
            LPI_SERVER_CMD,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=REPO_ROOT,
        )
    except Exception as e:
        print(f"[ERROR] Failed to start MCP server: {e}")
        return

    # --- INIT ---
    try:
        init_req = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
        }

        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        proc.stdout.readline()

        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()

    except Exception as e:
        print(f"[ERROR] MCP initialization failed: {e}")
        return

    # --- TOOL CALLS ---
    tools_used = []

    print("[1/3] SMILE overview...")
    overview = call_mcp_tool(proc, "smile_overview", {})
    tools_used.append(("smile_overview", {}))

    print("[2/3] Knowledge search...")
    knowledge = call_mcp_tool(proc, "query_knowledge", {"query": question})
    tools_used.append(("query_knowledge", {"query": question}))

    print("[3/3] Case studies...")
    cases = call_mcp_tool(proc, "get_case_studies", {})
    tools_used.append(("get_case_studies", {}))

    proc.terminate()

    # --- PROMPT ---
    prompt = f"""
Answer using ONLY the data below. Explain clearly and cite sources.

Tool1:
{overview[:1500]}

Tool2:
{knowledge[:1500]}

Tool3:
{cases[:1000]}

Question:
{question}

Explain clearly and add Sources section.
"""

    print("\nSending to LLM...\n")
    answer = query_ollama(prompt)

    # --- OUTPUT ---
    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(answer)

    print("\n" + "=" * 60)
    print("PROVENANCE")
    print("=" * 60)

    for i, (name, args) in enumerate(tools_used, 1):
        print(f"[{i}] {name} {args if args else '(no args)'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py 'your question'")
        sys.exit(1)

    run_agent(sys.argv[1])
