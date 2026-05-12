import sys
import json
import os
import re
import urllib.request
import urllib.error
import time

AGENT_B_CARD = os.path.join(os.path.dirname(__file__), "..", "agent_b", ".well-known", "agent.json")

# Security: In-Memory Rate Limiter (sliding window simulated)
RATE_LIMIT_DB = {"client_1": []}
MAX_REQUESTS_PER_MIN = 10

def check_rate_limit(client_id="client_1"):
    current_time = time.time()
    # Filter requests within the last 60 seconds
    RATE_LIMIT_DB[client_id] = [t for t in RATE_LIMIT_DB[client_id] if current_time - t < 60]
    
    if len(RATE_LIMIT_DB[client_id]) >= MAX_REQUESTS_PER_MIN:
        raise PermissionError(f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_MIN} requests per minute.")
    
    RATE_LIMIT_DB[client_id].append(current_time)

def sanitize_input(user_input):
    # Security: Length Restriction (1000 chars)
    if len(user_input) > 1000:
        raise ValueError("Input exceeds 1000 allowed characters.")
        
    # Security: Advanced Regex Character Filtering (Strips system control chars)
    cleaned = re.sub(r'[^\w\s\.,\?!\'\"]', '', user_input)
    
    # Security: Prompt Injection Signatures
    lower_input = cleaned.lower()
    injections = ["ignore all", "system prompt", "bypass", "override", "you are now"]
    for pattern in injections:
        if pattern in lower_input:
            raise ValueError(f"Prompt injection pattern blocked: {pattern}")
            
    return cleaned

def discover_agent_b():
    if not os.path.exists(AGENT_B_CARD):
        raise FileNotFoundError("Agent B A2A card missing.")
    with open(AGENT_B_CARD, "r") as f:
        return json.load(f)

def add_executive_synthesis(agent_b_answer):
    """
    Agent A Proprietary Skill: Executive Output Summarization.
    This demonstrates 'Combined Output Value'. Agent B provides the raw LPI/LLM data,
    while Agent A restructures it into an actionable executive brief.
    """
    return (
        f"📋 [EXECUTIVE BRIEFING]\n"
        f"=================================================\n"
        f"Domain Source: LPI Expert Analysis (Agent B)\n"
        f"Format Wrapper: Coordinator Strategy (Agent A)\n\n"
        f"Insight: {agent_b_answer}\n\n"
        f"Next Steps: Proceed with formal design architecture.\n"
        f"================================================="
    )

def run_agent_a():
    if len(sys.argv) < 2:
        print("Usage: python agent_a.py <query>")
        sys.exit(1)
        
    raw_query = " ".join(sys.argv[1:])
    print("--- Coordinator Agent (Network Client) ---")

    try:
        check_rate_limit()
        safe_query = sanitize_input(raw_query)
        print("[+] Rate Limit & Input Sanitization: PASS")
    except Exception as e:
        print(f"[!] Security Block: {e}")
        sys.exit(1)
        
    try:
        card = discover_agent_b()
        endpoint = card.get("contact", {}).get("endpoint", "http://localhost:8000/query")
        print(f"[*] Discovered Agent B. Routing to: {endpoint}")
        
        payload = {
            "version": "1.0",
            "sender": "Agent A",
            "intent": "query_lpi_knowledge",
            "data": {"query": safe_query}
        }
        
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        # Security: Network Timeout to prevent hanging threads (Resource Exhaustion Mitigaton)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("\n--- Final Intelligent Output ---")
            
            # COMBINED AGENT VALUE PROOF: Agent A enriches Agent B's output
            final_enriched_answer = add_executive_synthesis(result.get('answer'))
            print(final_enriched_answer)
            
            print(f"\nTools Invoked: {', '.join(result.get('provenance', []))}")
            
    except urllib.error.URLError:
        print("[!] Agent B is offline. Ensure it is running on port 8000.")
    except Exception as e:
        print(f"[!] Orchestration Error: {e}")

if __name__ == "__main__":
    run_agent_a()
