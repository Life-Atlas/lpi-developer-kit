#!/usr/bin/env python3
"""
Life-Atlas LPI Digital Twin Agent
---------------------------------
Track A (Agent Builders) Level 3 Implementation

This module connects to the local Life Programmable Interface (LPI) MCP server
via stdio. It facilitates dynamic querying of digital twin methodology
and automatically falls back to deterministic parsing if strict LLM
backends (like Ollama) are unavailable, guaranteeing fail-safe execution.

Author: Vineet Sharma
Date: 2026-04-16
"""

import json
import subprocess
import sys
import os
import requests
from typing import Dict, Any, List, Tuple, cast

# --- Configuration & Logging ---
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("LPI_Agent")

LPI_SERVER_PATH = os.environ.get(
    "LPI_SERVER_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lpi-developer-kit", "dist", "src", "index.js"))
)
LPI_SERVER_CMD = ["node", LPI_SERVER_PATH]
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"


def call_mcp_tool(process: subprocess.Popen, tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Executes a JSON-RPC method call to the underlying MCP server.

    Args:
        process: The subprocess.Popen instance representing the MCP server.
        tool_name: The name of the tool to execute (e.g., 'query_knowledge').
        arguments: The arguments dictionary expected by the specific tool.

    Returns:
        str: The extracted text result or an error trace.
    """
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    if process.stdin:
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

    if process.stdout:
        line = process.stdout.readline()
        if not line:
            return f"[ERROR] No response from MCP server for {tool_name}"
        resp = json.loads(line)
        if "result" in resp and "content" in resp["result"]:
            # Type hinting assertion for pyre
            return str(resp["result"]["content"][0].get("text", ""))
        if "error" in resp:
            return f"[ERROR] {resp['error'].get('message', 'Unknown error')}"
        return "[ERROR] Unexpected response format"
    return "[ERROR] Stdout PIPE not established"


def query_llm(prompt: str) -> str:
    """
    Delegates insight generation to a local Ollama instance.
    Includes a fail-safe exception handler designed for edge cases.

    Args:
        prompt: The complete contextual prompt formatted with MCP data.

    Returns:
        str: The LLM output or a fallback flag.
    """
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=3,
        )
        if resp.status_code == 200:
            return str(resp.json().get("response", "[No response from model]"))
    except requests.exceptions.RequestException:
        logger.warning("Ollama API unreachable. Defaulting to gracefully formatted raw extraction.")
    
    return "[FALLBACK]"


def run_agent(question: str) -> Dict[str, Any]:
    """
    Main orchestration function. Initializes the MCP pipe, polls
    required tools, routes data to logic engines, and guarantees provenance.

    Args:
        question: The target methodology inquiry.

    Returns:
        dict: The final explainable answer mapped alongside its exact provenance sources.
    """
    if not os.path.exists(LPI_SERVER_PATH):
        logger.error(f"Failed to locate LPI MCP node server at {LPI_SERVER_PATH}. Verify LPI_SERVER_PATH.")
        sys.exit(1)

    proc = subprocess.Popen(
        LPI_SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # MCP Phase 1: Negotiation & Handshake
    init_req = {
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "vineet-agent", "version": "1.0.0"}}
    }
    if proc.stdin:
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
    if proc.stdout:
        proc.stdout.readline()

    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    if proc.stdin:
        proc.stdin.write(json.dumps(notif) + "\n")
        proc.stdin.flush()

    tools_used: List[Tuple[str, Dict[str, Any]]] = []

    logger.info("Extracting general methodology context using 'query_knowledge' tool...")
    knowledge = str(call_mcp_tool(proc, "query_knowledge", {"query": question}))
    tools_used.append(("query_knowledge", {"query": question}))

    logger.info("Extracting structured specifics using 'smile_phase_detail' tool...")
    phase_detail = str(call_mcp_tool(proc, "smile_phase_detail", {"phase": "phase1_reality_emulation"}))
    tools_used.append(("smile_phase_detail", {"phase": "phase1_reality_emulation"}))

    proc.terminate()
    proc.wait(timeout=5)

    # Formulate Prompt with explicit AI constraints
    prompt = f"""You are a helpful expert advising on digital twin methodology.
Answer the user's question concisely using ONLY the provided tools.
After the answer, cite the sources clearly like "[Tool N: tool_name] - usage details".

--- Tool 1: query_knowledge("{question}") ---
{knowledge[:1500]}

--- Tool 2: smile_phase_detail("phase1_reality_emulation") ---
{phase_detail[:1500]}

--- User Question ---
{question}
"""

    answer = query_llm(prompt)
    if answer == "[FALLBACK]":
        str_knowledge = knowledge[:800].replace("\n", " ")
        str_phase = phase_detail[:800].replace("\n", " ")
        answer = (
            "**[Fallback Mode]** I noticed you don't have the Ollama LLM running locally! "
            "That's okay, I have successfully extracted exactly what you need straight from the methodologies:\n\n"
            f"**1. Knowledge Base Search Result:**\n\"{str_knowledge}...\"\n\n"
            f"**2. Core Phase Details:**\n\"{str_phase}...\""
        )
    
    return {
        "answer": answer,
        "provenance": tools_used
    }


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "How do I build a digital twin for an office building?"
    
    print(f"\n{'='*80}")
    print(f"  TRACK A AGENT — Orchestrating methodology inquiry: {q}")
    print(f"{'='*80}\n")
    
    res = run_agent(q)
    
    print(f"\n{'='*80}")
    print("  EXPLAINABLE ANSWER")
    print(f"{'='*80}\n")
    print(res["answer"])

    print(f"\n{'='*80}")
    print("  EXACT PROVENANCE / CITATIONS")
    print(f"{'='*80}")
    for i, (name, args) in enumerate(res["provenance"], 1):
        print(f"  [{i}] Source: {name} | Parameters: {json.dumps(args)}")
    print()
