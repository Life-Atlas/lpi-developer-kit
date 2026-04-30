from subprocess import Popen, PIPE
import json

def call_tool(tool, args):
    process = Popen(
        ["node", "../lpi-clean/dist/src/index.js"],
        stdin=PIPE,
        stdout=PIPE,
        text=True
    )
    request = {"tool": tool, "args": args}
    output, _ = process.communicate(json.dumps(request))
    return output.strip()

def handle_request(data):
    try:
        query = data.get("query", "")

        if not query:
            return {"error": "Empty query"}

        insights = call_tool("get_insights", {"query": query})

        return {
            "agent": "INSIGHTS_AGENT",
            "data": insights
        }

    except Exception as e:
        return {"error": str(e)}
