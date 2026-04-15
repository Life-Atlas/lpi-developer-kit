#!/usr/bin/env python3
import json
import subprocess
import sys
import requests

# --- Configuration ---
LPI_SERVER_CMD = ["node", "dist/src/index.js"]
LPI_SERVER_CWD = "."
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:0.5b"


def call_mcp_tool(process, tool_name: str, arguments: dict) -> str:
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
    return "[ERROR] Unexpected response"


def query_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json().get("response", "[No response]")
    except Exception as e:
        return f"[ERROR] {e}"


def run_agent(question: str):
    print("\n" + "="*60)
    print(f" LPI Explainable Agent")
    print("="*60)

    # --- NEW: User focus selection ---
    print("\nChoose focus area:")
    print("1. General SMILE")
    print("2. Personal Health Digital Twin")
    print("3. Smart Building Digital Twin")

    choice = input("Enter choice (1/2/3): ")

    if choice == "2":
        question = "How to build a personal health digital twin?"
    elif choice == "3":
        question = "How to build a smart building digital twin?"

    print(f"\nQuestion: {question}\n")

    # Start MCP server
    proc = subprocess.Popen(
        LPI_SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=LPI_SERVER_CWD,
    )

    # Init MCP
    init_req = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "custom-agent", "version": "1.0"},
        },
    }
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()

    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    proc.stdin.write(json.dumps(notif) + "\n")
    proc.stdin.flush()

    tools_used = []

    print("[1/3] Getting SMILE overview...")
    overview = call_mcp_tool(proc, "smile_overview", {})
    tools_used.append("smile_overview")

    print("[2/3] Querying knowledge base...")
    knowledge = call_mcp_tool(proc, "query_knowledge", {"query": question})
    tools_used.append("query_knowledge")

    print("[3/3] Getting insights...")
    insights = call_mcp_tool(proc, "get_insights", {"scenario": question, "tier": "free"})
    tools_used.append("get_insights")

    proc.terminate()
    proc.wait(timeout=5)

    # --- IMPROVED PROMPT ---
    prompt = f"""
You are an AI agent using structured tools.

Rules:
- Use ONLY the provided tool data
- Do NOT hallucinate
- If unsure, say "Not found in tools"
- Clearly explain which tool gave which info

{overview[:800]}
{knowledge[:800]}
{insights[:800]}

--- Question ---
{question}

Give a clear answer, then list sources used.
"""

    print("\nGenerating answer with local AI...\n")
    answer = query_ollama(prompt)

    # --- CLEAN OUTPUT ---
    print("="*60)
    print(" FINAL ANSWER")
    print("="*60)
    print(answer)

    print("\n" + "="*60)
    print(" SOURCES USED")
    print("="*60)
    for i, tool in enumerate(tools_used, 1):
        print(f"{i}. {tool}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python my-agent.py "Your question"')
        sys.exit(1)

    run_agent(sys.argv[1])