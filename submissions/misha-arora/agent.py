#!/usr/bin/env python3

"""
Level 3 Submission by Misha Arora

LPI Sandbox Agent

Connects to the LPI MCP server, queries SMILE methodology tools,
and returns a simple explainable answer.
"""

import json
import subprocess
import sys
import requests
import os as _os

# --- Configuration ---
_REPO_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))

LPI_SERVER_CMD = ["node", _os.path.join(_REPO_ROOT, "dist", "src", "index.js")]
LPI_SERVER_CWD = _REPO_ROOT

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"


def call_mcp_tool(process, tool_name: str, arguments: dict) -> str:
    """Send JSON-RPC request to MCP server"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    return response


def ask_llm(prompt: str) -> str:
    """Send prompt to local LLM via Ollama"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload)
        return res.json().get("response", "")
    except:
        return "LLM not available"


def main():
    if len(sys.argv) < 2:
        print("Usage: python agent.py 'your question'")
        return

    question = sys.argv[1]

    print("🚀 Starting LPI Agent...\n")

    process = subprocess.Popen(
        LPI_SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=LPI_SERVER_CWD
    )

    try:
        # Query SMILE overview
        result = call_mcp_tool(process, "smile_overview", {})

        print("📊 MCP Response:\n", result)

        # Send to LLM
        final_answer = ask_llm(
            f"Explain this in simple terms:\n{result}\n\nQuestion: {question}"
        )

        print("\n🤖 Final Answer:\n", final_answer)

    finally:
        process.kill()


if __name__ == "__main__":
    main()