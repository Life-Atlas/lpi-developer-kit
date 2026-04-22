import json
import subprocess
import os
from security import prevent_data_leak


# ---- PATH SETUP (same as your code) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LPI_PATH = os.path.join(BASE_DIR, "..", "..", "dist", "src", "index.js")

if not os.path.exists(LPI_PATH):
    raise FileNotFoundError(f"LPI server not found at {LPI_PATH}")


# ---- CALL LPI TOOL (your logic, cleaned) ----
def call_lpi_tool(tool_name, query):
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
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")

        # ARGUMENT FIX (your special handling preserved)
        if tool_name == "get_case_studies":
            args = {"query": "healthcare digital twin"}
        else:
            args = {"query": query}

        # TOOL CALL
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            },
            "id": 1
        }) + "\n")

        process.stdin.flush()

        stdout, _ = process.communicate(timeout=10)

        if not stdout.strip():
            return ""

        # ---- PARSE OUTPUT (same logic, but forward scan instead of reverse) ----
        for line in stdout.split("\n"):
            try:
                parsed = json.loads(line)

                if "result" in parsed:
                    result = parsed["result"]

                    if isinstance(result, dict) and "content" in result:
                        content = result["content"]

                        if isinstance(content, list) and content:
                            text = content[0].get("text", "")

                            # ---- CASE STUDY FILTER (your idea preserved) ----
                            if tool_name == "get_case_studies":
                                parts = text.split("## ")
                                for part in parts:
                                    if "health" in part.lower():
                                        return "## " + part[:1200]

                            return text

                    return str(result)

            except:
                continue

        return ""

    except Exception as e:
        return f"Error calling {tool_name}: {str(e)}"


# ---- TOOL SELECTION (same as your Level 3) ----
def choose_tools(query):
    q = query.lower()

    if "how" in q or "use" in q:
        return ["smile_overview", "get_case_studies"]
    elif "implement" in q or "steps" in q:
        return ["get_methodology_step", "get_insights"]
    else:
        return ["query_knowledge", "get_case_studies"]


# ---- AGENT B ----
def run_agent_b(input_data):
    query = input_data.get("query", "")

    # ---- SELECT TOOLS ----
    tool1, tool2 = choose_tools(query)

    # ---- CALL TOOLS ----
    data1 = call_lpi_tool(tool1, query)
    data2 = call_lpi_tool(tool2, query)

    # ---- SECURITY FILTER ----
    data1 = prevent_data_leak(data1)
    data2 = prevent_data_leak(data2)

    # ---- STRUCTURED OUTPUT ----
    return {
        "smile_data": data1,
        "case_data": data2,
        "sources": [tool1, tool2]
    }


# ---- TEST ----
if __name__ == "__main__":
    result = run_agent_b({
        "query": "How are digital twins used in healthcare?"
    })

    print("\n=== AGENT B OUTPUT ===\n")
    print(json.dumps(result, indent=2))
