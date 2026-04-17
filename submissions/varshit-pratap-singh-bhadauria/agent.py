#!/usr/bin/env python3
"""
Life-Atlas LPI Digital Twin Advisor Agent (Improved)
Level 3 - Strong Submission Version
"""

import json
import subprocess
import sys
import os
import requests
from typing import Dict, Any, List, Tuple
import logging

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LPI_AGENT")

LPI_SERVER_PATH = os.environ.get(
    "LPI_SERVER_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lpi-developer-kit", "dist", "src", "index.js"))
)

LPI_SERVER_CMD = ["node", LPI_SERVER_PATH]

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

# ---------------- MCP TOOL CALL ----------------
def call_mcp_tool(process, tool_name: str, arguments: Dict[str, Any]) -> str:
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
        return "[ERROR] No response"

    resp = json.loads(line)

    if "result" in resp and "content" in resp["result"]:
        return resp["result"]["content"][0].get("text", "")
    
    return "[ERROR] Tool call failed"


# ---------------- LLM ----------------
def query_llm(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except:
        logger.warning("Ollama not running → fallback mode")

    return "[FALLBACK]"


# ---------------- SMART PHASE SELECTION ----------------
def detect_phase(question: str) -> str:
    q = question.lower()

    if "data" in q:
        return "phase2_data_capture"
    elif "model" in q:
        return "phase3_modeling"
    elif "optimize" in q:
        return "phase5_optimization"
    else:
        return "phase1_reality_emulation"


# ---------------- MAIN AGENT ----------------
def run_agent(question: str):

    if not os.path.exists(LPI_SERVER_PATH):
        print("❌ LPI server not found")
        sys.exit(1)

    proc = subprocess.Popen(
        LPI_SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # ---- INIT MCP ----
    init_req = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "advisor-agent", "version": "2.0"}
        }
    }

    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()

    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    # ---- TOOL CALLS ----
    tools_used: List[Tuple[str, Dict[str, Any]]] = []

    logger.info("Calling query_knowledge...")
    knowledge = call_mcp_tool(proc, "query_knowledge", {"query": question})
    tools_used.append(("query_knowledge", {"query": question}))

    phase = detect_phase(question)

    logger.info(f"Calling smile_phase_detail for {phase}...")
    phase_detail = call_mcp_tool(proc, "smile_phase_detail", {"phase": phase})
    tools_used.append(("smile_phase_detail", {"phase": phase}))

    logger.info("Calling smile_overview...")
    overview = call_mcp_tool(proc, "smile_overview", {})
    tools_used.append(("smile_overview", {}))

    proc.terminate()

    # ---- PROMPT (STRICT EXPLAINABILITY) ----
    prompt = f"""
You are a Digital Twin Advisor.

STRICT RULES:
- Use ONLY given data
- Every paragraph MUST include source
- Use format: [SOURCE: tool_name]
- Be concise and structured

--- TOOL: query_knowledge ---
{knowledge[:1200]}

--- TOOL: smile_phase_detail ({phase}) ---
{phase_detail[:1200]}

--- TOOL: smile_overview ---
{overview[:800]}

QUESTION:
{question}
"""

    answer = query_llm(prompt)

    # ---- FALLBACK ----
    if answer == "[FALLBACK]":
        answer = f"""
### Answer (Fallback Mode)

[SOURCE: query_knowledge]
{knowledge[:400]}

[SOURCE: smile_phase_detail]
{phase_detail[:400]}

[SOURCE: smile_overview]
{overview[:300]}
"""

    # ---- FINAL OUTPUT ----
    final_output = f"""
================== ANSWER ==================

{answer}

================== SOURCES ==================

1. query_knowledge → general knowledge
2. smile_phase_detail → specific phase ({phase})
3. smile_overview → full methodology
"""

    return final_output


# ---------------- RUN ----------------
if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "How to build a digital twin for a company?"

    print("\n🚀 LPI DIGITAL TWIN ADVISOR\n")
    print(f"Question: {question}\n")

    result = run_agent(question)
    print(result)
