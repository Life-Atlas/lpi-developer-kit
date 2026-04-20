import json
import subprocess
import os


# ---- PATH SETUP ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LPI_PATH = os.path.join(BASE_DIR, "..", "dist", "src", "index.js")

if not os.path.exists(LPI_PATH):
    raise FileNotFoundError(f"LPI server not found at {LPI_PATH}")


# ---- CALL LPI TOOL ----
def call_tool(tool_name, args):
    try:
        process = subprocess.Popen(
            ["node", LPI_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

        # INIT
        init_msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(init_msg) + "\n")

        # TOOL CALL
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            },
            "id": 1
        }

        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        stdout, stderr = process.communicate(timeout=10)

        for line in stdout.split("\n"):
            try:
                parsed = json.loads(line)
                if "result" in parsed:
                    content = parsed["result"]["content"]
                    return content[0].get("text", "")
            except:
                continue

        return ""

    except Exception as e:
        return f"Error calling {tool_name}: {str(e)}"


# ---- SIMPLE FILTERING ----
def filter_relevant(text, keyword):
    """
    Basic filtering:
    - keeps only relevant sections
    - avoids cross-domain noise
    """
    lines = text.split("\n")
    filtered = [l for l in lines if keyword.lower() in l.lower()]

    return "\n".join(filtered[:10]) if filtered else text[:500]


# ---- MAIN AGENT ----
def run_agent_b(input_data):
    """
    Expected input:
    {
        "use_case": "..."
    }
    """

    use_case = input_data.get("use_case", "")

    # ---- TOOL CALLS ----
    insights_raw = call_tool("get_insights", {"scenario": use_case})
    cases_raw = call_tool("get_case_studies", {"query": use_case})
    knowledge_raw = call_tool("query_knowledge", {"query": use_case})

    # ---- FILTERING ----
    insights = filter_relevant(insights_raw, use_case)
    cases = filter_relevant(cases_raw, use_case)
    knowledge = knowledge_raw[:800]

    # ---- STRUCTURED OUTPUT ----
    return {
        "validated_insights": insights.split("\n")[:5],
        "case_points": cases.split("\n")[:5],
        "knowledge": knowledge
    }


# ---- TEST ----
if __name__ == "__main__":
    sample_input = {
        "use_case": "ICU patient monitoring digital twin"
    }

    result = run_agent_b(sample_input)

    print("\n--- AGENT B OUTPUT ---\n")
    print(json.dumps(result, indent=2))
