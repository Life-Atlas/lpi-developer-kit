#!/usr/bin/env python3
"""
Agent B - SMILE Agent Server (Secure Agent Mesh)

Acts as an A2A server that receives structured requests,
integrates with LPI MCP tools, and returns secure responses.
"""

import json
import subprocess
import sys
import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from werkzeug.serving import WSGIRequestHandler
import threading
import time

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"
LPI_SERVER_CMD = ["node", os.path.join(os.path.dirname(__file__), "..", "lpi-developer-kit", "dist", "src", "index.js")]
LPI_SERVER_CWD = os.path.join(os.path.dirname(__file__), "..", "lpi-developer-kit")

class SecurityHardening:
    """Security measures for Agent B server"""
    
    # Rate limiting storage (simple in-memory for demo)
    rate_limit_store = {}
    
    @staticmethod
    def validate_request_structure(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate incoming request structure"""
        required_fields = ['task', 'input', 'timestamp', 'client_id']
        
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Validate task
        valid_tasks = ['analyze_problem']
        if data['task'] not in valid_tasks:
            return False, f"Invalid task: {data['task']}"
        
        # Validate input length
        if not isinstance(data['input'], str) or len(data['input']) > 1000:
            return False, "Invalid input: must be string <= 1000 chars"
        
        # Validate client_id
        if not isinstance(data['client_id'], str) or len(data['client_id']) > 100:
            return False, "Invalid client_id"
        
        return True, None
    
    @staticmethod
    def check_rate_limit(client_id: str, max_requests: int = 10, window_seconds: int = 60) -> tuple[bool, Optional[str]]:
        """Simple rate limiting per client"""
        now = time.time()
        
        # Clean old entries
        SecurityHardening.rate_limit_store = {
            cid: times for cid, times in SecurityHardening.rate_limit_store.items()
            if any(t > now - window_seconds for t in times)
        }
        
        # Check current client
        if client_id not in SecurityHardening.rate_limit_store:
            SecurityHardening.rate_limit_store[client_id] = []
        
        # Remove old requests for this client
        SecurityHardening.rate_limit_store[client_id] = [
            t for t in SecurityHardening.rate_limit_store[client_id]
            if t > now - window_seconds
        ]
        
        # Check if over limit
        if len(SecurityHardening.rate_limit_store[client_id]) >= max_requests:
            return False, f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds"
        
        # Add current request
        SecurityHardening.rate_limit_store[client_id].append(now)
        return True, None
    
    @staticmethod
    def sanitize_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize response to prevent data leakage"""
        sanitized = {}
        
        # Only allow specific fields
        allowed_fields = ['problem', 'analysis', 'suggestions', 'sources', 'timestamp']
        
        for field in allowed_fields:
            if field in response_data:
                value = response_data[field]
                # Ensure string values are reasonable length
                if isinstance(value, str) and len(value) > 5000:
                    value = value[:5000] + "... [truncated]"
                sanitized[field] = value
        
        # Add timestamp
        sanitized['timestamp'] = datetime.now().isoformat()
        
        return sanitized

class LPIIntegration:
    """Integration with LPI MCP server"""
    
    @staticmethod
    def call_mcp_tool(process, tool_name: str, arguments: dict) -> str:
        """Send a JSON-RPC request to the MCP server"""
        try:
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
                return "[ERROR] No response from MCP server"
            
            resp = json.loads(line)
            if "result" in resp and "content" in resp["result"]:
                return resp["result"]["content"][0].get("text", "")
            if "error" in resp:
                return f"[ERROR] {resp['error'].get('message', 'Unknown error')}"
            return "[ERROR] Unexpected response format"
        
        except Exception as e:
            return f"[ERROR] MCP tool call failed: {e}"
    
    @staticmethod
    def query_ollama(prompt: str) -> str:
        """Send a prompt to Ollama and return the response"""
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("response", "[No response from model]")
        
        except requests.ConnectionError:
            return "[ERROR] Cannot connect to Ollama. Is it running?"
        except requests.Timeout:
            return "[ERROR] Ollama request timed out."
        except Exception as e:
            return f"[ERROR] Ollama error: {e}"
    
    @staticmethod
    def analyze_with_lpi(user_input: str) -> Dict[str, Any]:
        """Analyze user input using LPI tools and Ollama"""
        # Start MCP server
        proc = None
        try:
            proc = subprocess.Popen(
                LPI_SERVER_CMD,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=LPI_SERVER_CWD,
            )
            
            # MCP initialization
            init_req = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "smile-agent-b", "version": "1.0.0"},
                },
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()
            proc.stdout.readline()  # read init response

            # Send initialized notification
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            proc.stdin.write(json.dumps(notif) + "\n")
            proc.stdin.flush()
            
            # Query LPI tools
            knowledge = LPIIntegration.call_mcp_tool(proc, "query_knowledge", {"query": user_input})
            insights = LPIIntegration.call_mcp_tool(proc, "get_insights", {"query": user_input})
            
            # Build prompt for Ollama
            prompt = f"""You are a SMILE methodology expert. Analyze the user's problem using the provided context.

USER PROBLEM: {user_input}

CONTEXT FROM LPI TOOLS:
- Knowledge Base: {knowledge[:1000]}
- System Insights: {insights[:800]}

Provide a structured response in JSON format:
{{
  "problem": "Brief restatement of the user's problem",
  "analysis": "SMILE-based analysis of the problem",
  "suggestions": "3-4 actionable suggestions",
  "sources": ["query_knowledge", "get_insights"]
}}

Focus on practical, actionable advice based on SMILE methodology."""
            
            # Get analysis from Ollama
            llm_response = LPIIntegration.query_ollama(prompt)
            
            # Try to parse JSON response
            try:
                analysis_data = json.loads(llm_response)
                return analysis_data
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                return {
                    "problem": user_input,
                    "analysis": "Analysis based on SMILE methodology and LPI tools",
                    "suggestions": "1. Track your patterns 2. Identify triggers 3. Implement small changes 4. Evaluate results",
                    "sources": ["query_knowledge", "get_insights"]
                }
        
        except Exception as e:
            return {
                "problem": user_input,
                "analysis": f"Analysis temporarily unavailable: {str(e)}",
                "suggestions": "1. Check system status 2. Try again later 3. Contact support",
                "sources": ["error"]
            }
        
        finally:
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

# Flask App
app = Flask(__name__)

@app.route('/.well-known/agent.json')
def agent_card():
    """A2A Agent Card for discovery"""
    return jsonify({
        "name": "smile_agent",
        "description": "Provides SMILE-based analysis for personal optimization problems",
        "version": "1.0.0",
        "endpoint": "http://localhost:8000/analyze",
        "capabilities": [
            {
                "id": "analyze_problem",
                "name": "Analyze Problem",
                "description": "Analyze personal problems using SMILE methodology",
                "input": {
                    "type": "text",
                    "description": "Problem description (max 1000 chars)",
                    "max_length": 1000
                },
                "output": {
                    "type": "structured_analysis",
                    "description": "Structured analysis with problem, analysis, suggestions, and sources"
                }
            }
        ],
        "security": {
            "rate_limiting": True,
            "input_validation": True,
            "output_sanitization": True
        },
        "protocols": ["A2A", "HTTP/JSON"],
        "maintainer": "Secure Agent Mesh Team"
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """Main analysis endpoint"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON request"}), 400
        
        # Security validation
        is_valid, error = SecurityHardening.validate_request_structure(data)
        if not is_valid:
            return jsonify({"error": f"Validation failed: {error}"}), 400
        
        # Rate limiting
        client_id = data.get('client_id', 'unknown')
        is_allowed, rate_error = SecurityHardening.check_rate_limit(client_id)
        if not is_allowed:
            return jsonify({"error": rate_error}), 429
        
        # Process request
        task = data['task']
        user_input = data['input']
        
        if task == 'analyze_problem':
            # Analyze using LPI integration
            result = LPIIntegration.analyze_with_lpi(user_input)
            
            # Sanitize response
            sanitized_result = SecurityHardening.sanitize_response(result)
            
            return jsonify(sanitized_result)
        else:
            return jsonify({"error": f"Unsupported task: {task}"}), 400
    
    except Exception as e:
        # Log error but don't expose internal details
        print(f"[ERROR] Analysis endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with basic info"""
    return jsonify({
        "name": "Agent B - SMILE Agent Server",
        "status": "running",
        "endpoints": {
            "agent_card": "/.well-known/agent.json",
            "analyze": "/analyze (POST)",
            "health": "/health (GET)"
        }
    })

def run_server():
    """Run the Flask server with security configurations"""
    # Disable Werkzeug console logging for cleaner output
    WSGIRequestHandler.log_request = lambda *args, **kwargs: None
    
    print("=" * 60)
    print("  Agent B - SMILE Agent Server")
    print("  Starting on http://localhost:8000")
    print("=" * 60)
    
    app.run(
        host='localhost',
        port=8000,
        debug=False,  # Disable debug in production
        threaded=True,
        use_reloader=False  # Prevent reloader issues
    )

if __name__ == "__main__":
    run_server()
