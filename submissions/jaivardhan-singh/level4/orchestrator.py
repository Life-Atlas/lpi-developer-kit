import json
import subprocess
import sys
import requests
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

def run_agent_script(script_name, query):
    """Executes an agent script as a subprocess and captures its JSON output."""
    try:
        # Run the agent script, passing the query as an argument
        result = subprocess.run(
            [sys.executable, script_name, query],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse the output as JSON
        output_str = result.stdout.strip()
        # Some LLMs might wrap JSON in markdown blocks (```json ... ```), try to strip if present
        if output_str.startswith("```json"):
            output_str = output_str[7:-3].strip()
        elif output_str.startswith("```"):
            output_str = output_str[3:-3].strip()
            
        return json.loads(output_str)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Agent {script_name} crashed: {e.stderr}")
        return {"error": "Agent crashed"}
    except json.JSONDecodeError:
        print(f"[ERROR] Agent {script_name} returned invalid JSON: \n{result.stdout}")
        return {"error": "Invalid JSON from agent"}

def synthesize_final_answer(query, agent_a_data, agent_b_data):
    """Uses LLM to combine the structured data from both agents into a final recommendation."""
    
    prompt = f"""[SYSTEM INSTRUCTIONS]
You are the Lead Digital Twin Consultant. Your job is to synthesize data from your two expert agents into a single, cohesive recommendation for the client.

[CLIENT QUERY]
{query}

[EXPERT DATA (Agent A: SMILE Methodology)]
{json.dumps(agent_a_data, indent=2)}

[EXPERT DATA (Agent B: Real-World Case Studies)]
{json.dumps(agent_b_data, indent=2)}

[OUTPUT REQUIREMENTS]
Write a professional, 3-paragraph recommendation for the client.
Paragraph 1: Acknowledge their goal and explain the recommended SMILE phases (based on Agent A).
Paragraph 2: Provide evidence from relevant case studies (based on Agent B).
Paragraph 3: Give a clear "Next Steps" conclusion.
DO NOT output JSON. Write plain, readable text for the client.
"""
    print("\n[Orchestrator] Synthesizing final recommendation...\n")
    try:
        resp = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "Synthesis failed.")
    except Exception as e:
        return f"[ERROR] Orchestrator LLM failure: {e}"

def main():
    print(f"\n{'='*60}")
    print(" LPI LEVEL 4: SECURE MULTI-AGENT MESH")
    print(f"{'='*60}")
    
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py \"Your scenario/question\"")
        print("Example: python orchestrator.py \"How to build a smart hospital HVAC system\"")
        sys.exit(1)

    user_query = sys.argv[1]
    print(f"\n[Client Request]: {user_query}")
    
    # --- 1. Query Agent A ---
    print("\n[Orchestrator] Dispatching to Agent A (SMILE Expert)...")
    agent_a_response = run_agent_script("agent_a_expert.py", user_query)
    print("Agent A Response (Structured):")
    print(json.dumps(agent_a_response, indent=2))
    
    if "error" in agent_a_response:
        print("\n[CRITICAL] Agent A failed or blocked the request. Halting mesh operations.")
        sys.exit(1)

    # --- 2. Query Agent B ---
    print("\n[Orchestrator] Dispatching to Agent B (Researcher)...")
    agent_b_response = run_agent_script("agent_b_researcher.py", user_query)
    print("Agent B Response (Structured):")
    print(json.dumps(agent_b_response, indent=2))

    if "error" in agent_b_response:
        print("\n[CRITICAL] Agent B failed or blocked the request. Halting mesh operations.")
        sys.exit(1)

    # --- 3. Synthesize ---
    final_output = synthesize_final_answer(user_query, agent_a_response, agent_b_response)
    
    print(f"\n{'='*60}")
    print(" FINAL SYNTHESIZED RECOMMENDATION")
    print(f"{'='*60}\n")
    print(final_output)
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()