import subprocess
import json
import sys
import logging

# ✅ Logging setup - saves errors to file for production
logging.basicConfig(
    filename='agent_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def call_lpi_tool(tool_name, arguments={}):
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        result = subprocess.run(
            ["node", "../lpi-developer-kit/dist/src/index.js"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            logging.error(f"Tool '{tool_name}' returned non-zero exit: {result.stderr}")
            print(f"⚠️ Tool '{tool_name}' returned error: {result.stderr}")
            return None
        if not result.stdout.strip():
            logging.error(f"Tool '{tool_name}' returned empty response.")
            print(f"⚠️ Tool '{tool_name}' returned empty response.")
            return None
        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        logging.error(f"Tool '{tool_name}' timed out after 30 seconds.")
        print(f"❌ Error: Tool '{tool_name}' timed out after 30 seconds.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error from '{tool_name}': {e}")
        print(f"❌ Error: Could not parse response from '{tool_name}': {e}")
        return None
    except FileNotFoundError:
        logging.error("Node.js not found. LPI server may not be built.")
        print("❌ Error: Node.js not found. Make sure Node.js is installed and LPI is built.")
        return None
    except Exception as e:
        logging.error(f"Unexpected error calling '{tool_name}': {e}")
        print(f"❌ Unexpected error calling '{tool_name}': {e}")
        return None


def main():
    # ✅ Input validation
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("❌ Usage: python agent.py \"Your question here\"")
        sys.exit(1)

    question = sys.argv[1].strip()
    print(f"\n🤖 Agent received question: {question}\n")

    # ✅ Call LPI Tool 1
    print("📡 Calling LPI tool: smile_overview")
    tool1_result = call_lpi_tool("smile_overview")
    if tool1_result is None:
        print("⚠️ Could not get smile_overview. Continuing with partial data...")
    else:
        print("✅ Tool 1 result received\n")

    # ✅ Call LPI Tool 2
    print("📡 Calling LPI tool: query_knowledge")
    tool2_result = call_lpi_tool("query_knowledge", {"query": question})
    if tool2_result is None:
        print("⚠️ Could not get query_knowledge. Continuing with partial data...")
    else:
        print("✅ Tool 2 result received\n")

    # ✅ Both tools failed - exit gracefully
    if tool1_result is None and tool2_result is None:
        logging.error("Both LPI tools failed. No answer could be generated.")
        print("❌ Both LPI tools failed. Cannot generate answer. Check LPI server setup.")
        sys.exit(1)

    # ✅ Output with citations
    print("=" * 50)
    print("📋 ANSWER (with source citations):")
    print("=" * 50)
    print(f"\nQuestion: '{question}'\n")

    if tool1_result:
        print("From [smile_overview]:")
        print(json.dumps(tool1_result, indent=2)[:500])

    if tool2_result:
        print("\nFrom [query_knowledge]:")
        print(json.dumps(tool2_result, indent=2)[:500])

    print("\n✅ Sources used: smile_overview, query_knowledge")


if __name__ == "__main__":
    # ✅ Top level error handling - catches any crash
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Program interrupted by user.")
        print("\n⚠️ Program interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
