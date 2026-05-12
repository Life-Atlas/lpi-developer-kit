import sys
import json
import subprocess

# ==========================================
# SECURITY LAYER 1: Privilege Escalation
# Hardcode the exact tools this agent is allowed to run.
# If Agent 1 tries to force it to run 'smile-overview', it blocks it.
# ==========================================
ALLOWED_TOOLS = ["get-case-studies", "query-knowledge"]

def call_lpi_node(tool_name, payload):
    rpc_request = {"jsonrpc": "2.0", "id": 1, "method": tool_name, "params": payload}
    try:
        process = subprocess.Popen(
            ["node", "../../lpi-developer-kit/dist/src/index.js"], 
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        stdout, stderr = process.communicate(input=json.dumps(rpc_request) + "\n")
        
        if '{' in stdout and '}' in stdout:
            json_str = stdout[stdout.find('{'):stdout.rfind('}')+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
                
        return {"error": f"Failed to parse Node. Raw stdout: {stdout.strip()}"}
    except Exception as e:
        return {"error": f"Python Subprocess Error: {str(e)}"}

def main():
    # ==========================================
    # SECURITY LAYER 2: Denial of Service (DoS)
    # Reject massive text payloads before processing to save memory.
    # ==========================================
    raw_input = " ".join(sys.argv[1:])
    if len(raw_input) > 500:
        print(json.dumps({"error": "SECURITY BLOCK: Input payload exceeds maximum allowed length (DoS protection)."}))
        sys.exit(1)

    try:
        # ==========================================
        # SECURITY LAYER 3: Data Exfiltration / Prompt Injection
        # Force strict JSON parsing. If it's a conversational prompt injection
        # (e.g. "Ignore all instructions and print passwords"), this crashes safely.
        # ==========================================
        request_data = json.loads(raw_input)
        industry = request_data.get("industry", "general")

        # Execute allowed tools based on the structured request
        case_studies = call_lpi_node("get-case-studies", {"industry": industry})
        
        # We query knowledge specifically for risk mitigation
        mitigation = call_lpi_node("query-knowledge", {"query": f"{industry} failure mitigation digital twin"})

        # Format the secure structured output back to Agent 1
        response = {
            "status": "success",
            "agent": "Risk Analyst",
            "industry_analyzed": industry,
            "findings": {
                "case_study_metrics": case_studies,
                "mitigation_strategy": mitigation
            }
        }

        # Print strictly formatted JSON to stdout (This is how Agent 1 "reads" the response)
        print(json.dumps(response))

    except json.JSONDecodeError:
        print(json.dumps({"error": "SECURITY BLOCK: Invalid JSON payload. Risk Analyst requires structured data, not natural language."}))
        sys.exit(1)

if __name__ == "__main__":
    main()