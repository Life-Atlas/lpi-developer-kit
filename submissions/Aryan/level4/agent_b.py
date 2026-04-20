import subprocess
import json
import os

# Path to LPI server
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# LPI_PATH = os.path.join(BASE_DIR, "..", "dist", "src", "index.js")
LPI_PATH = r"C:\Users\Aryan\Desktop\lpi-developer-kit\dist\src\index.js"


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
        init_msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(init_msg) + "\n")

        # Arguments
        if tool_name == "get_case_studies":
            args = {"query": "healthcare digital twin"}
        else:
            args = {"query": query}

        # Request
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
        print("\n[RAW LPI OUTPUT]:\n", stdout)

        # Parse response
        if stdout.strip():
            lines = stdout.strip().split("\n")

            for line in reversed(lines):
                try:
                    parsed = json.loads(line)

                    if "result" in parsed:
                        result = parsed["result"]

                        if isinstance(result, dict) and "content" in result:
                            content = result["content"]

                            if isinstance(content, list) and len(content) > 0:
                                text = content[0].get("text", "")

                                # Filter healthcare section
                                if tool_name == "get_case_studies":
                                    parts = text.split("## ")
                                    for part in parts:
                                        if "health" in part.lower():
                                            return "## " + part[:800]

                                return text

                        return str(result)

                except:
                    continue

        return "No output received"

    except Exception as e:
        return f"Error: {str(e)}"


def researcher_agent(query):
    """
    Decides which tools to use and gathers data
    """

    q = query.lower()

    # Tool selection
    if "how" in q or "use" in q:
        tools = ["smile_overview", "get_case_studies"]
    elif "implement" in q or "steps" in q:
        tools = ["get_methodology_step", "get_insights"]
    else:
        tools = ["query_knowledge", "get_case_studies"]

    results = {}

    for tool in tools:
        print(f"[Researcher] Calling tool: {tool}")
        results[tool] = call_lpi_tool(tool, query)

    # Combine context
    context = "\n\n".join(
        [f"{k.upper()}:\n{v}" for k, v in results.items()]
    )

    return context, tools


# Optional test
if __name__ == "__main__":
    q = "How are digital twins used in healthcare?"
    ctx, used = researcher_agent(q)

    print("\n--- TOOLS USED ---")
    print(used)

    print("\n--- CONTEXT ---")
    print(ctx[:1000])
