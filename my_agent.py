import subprocess
import json
import requests
import sys
import os

# ── Start the LPI server ──────────────────────────────────────────
lpi_process = subprocess.Popen(
    ["node", "dist/src/index.js"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    cwd=os.path.dirname(os.path.abspath(__file__))
)

request_id = 0

def call_lpi_tool(tool_name, params={}):
    """Call an LPI tool and return the result"""
    global request_id
    request_id += 1
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
        "id": request_id
    }
    lpi_process.stdin.write(json.dumps(request).encode() + b"\n")
    lpi_process.stdin.flush()
    response = lpi_process.stdout.readline()
    return json.loads(response)

def ask_phi(prompt):
    """Send prompt to local Ollama phi model"""
    print("\n⏳ Thinking...")
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "phi",
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

def run_agent(user_question):
    print(f"\n🔍 Question: {user_question}")
    print("─" * 50)

    # ── Tool 1: Get SMILE overview ────────────────────────────────
    print("📡 Calling tool 1: smile_overview...")
    smile_data = call_lpi_tool("smile_overview")

    # ── Tool 2: Query knowledge base ─────────────────────────────
    print("📡 Calling tool 2: query_knowledge...")
    knowledge_data = call_lpi_tool("query_knowledge", {"query": user_question})

    # ── Tool 3: Get a case study ──────────────────────────────────
    print("📡 Calling tool 3: get_case_studies...")
    case_data = call_lpi_tool("get_case_studies", {"industry": "healthcare"})

    # ── Build prompt with all 3 tool results ─────────────────────
    prompt = f"""You are a helpful AI assistant that answers questions about the SMILE methodology and digital twins.

User question: {user_question}

Here is data gathered from 3 different tools:

[Tool 1 - smile_overview]:
{json.dumps(smile_data)[:1000]}

[Tool 2 - query_knowledge]:
{json.dumps(knowledge_data)[:1000]}

[Tool 3 - get_case_studies]:
{json.dumps(case_data)[:1000]}

Using ONLY the above data, give a clear and helpful answer.
At the end, list which tools provided which information.
"""

    answer = ask_phi(prompt)

    print("\n✅ ANSWER:")
    print("─" * 50)
    print(answer)
    print("\n📚 TOOLS USED:")
    print("  1. smile_overview     — provided SMILE methodology context")
    print("  2. query_knowledge    — searched knowledge base for relevant info")
    print("  3. get_case_studies   — provided real-world industry examples")
    print("─" * 50)

# ── Main entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("\n💬 Enter your question: ")
    
    run_agent(question)
    lpi_process.terminate()