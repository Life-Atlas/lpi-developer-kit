import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

# Permitted LPI Tools
ALLOWED_TOOLS = ["query_knowledge", "smile_phase_detail"]

class MockMCPClient:
    """Simulates a securely restricted MCP connection."""
    def call_tool(self, tool_name, kwargs):
        if tool_name not in ALLOWED_TOOLS:
            raise ValueError(f"Unauthorized tool requested: {tool_name}")
        if tool_name == "query_knowledge":
            return "The SMILE methodology is Life-Atlas's 5-phase structured approach to development."
        elif tool_name == "smile_phase_detail":
            return f"Phase context for '{kwargs.get('phase')}': Ensures robust design and planning before coding."

def query_ollama(prompt):
    """Integrates with Ollama local LLM."""
    url = "http://localhost:11434/api/generate"
    data = {"model": "llama3", "prompt": prompt, "stream": False}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "").strip()
    except Exception as e:
        # Graceful fallback if Llam3 isn't available
        print(f"[Agent B System] Ollama connection failed or model not found: {e}")
        return "Fallback Active: Based on LPI tools, the SMILE methodology structures your development robustly."

class AgentBHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/query':
            self.send_error(404, "Endpoint Not Found")
            return
            
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON payload.")
            return

        # Security: Input Structure Validation
        if request.get("intent") != "query_lpi_knowledge":
            self.send_error(401, "Unauthorized intent.")
            return
            
        query = request.get("data", {}).get("query", "")
        mcp = MockMCPClient()
        provenance = []

        try:
            knowledge_res = mcp.call_tool("query_knowledge", {"query": query})
            provenance.append("tool:query_knowledge")
            
            phase_res = ""
            if "design" in query.lower() or "smile" in query.lower():
                phase_res = mcp.call_tool("smile_phase_detail", {"phase": "Design"})
                provenance.append("tool:smile_phase_detail")

            # Ollama Integration
            llm_prompt = f"Given this LPI context: '{knowledge_res} {phase_res}', please answer the user query: '{query}'"
            final_answer = query_ollama(llm_prompt)
            
        except Exception as e:
            self.send_error(500, f"Internal Execution Error: {e}")
            return

        response = {
            "status": "success",
            "answer": final_answer,
            "provenance": provenance
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, AgentBHandler)
    print("Agent B (LPI Expert) running as Network Server on port 8000...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
