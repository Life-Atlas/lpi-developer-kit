import requests
import sys
def safe_call(url, params=None):
    try:
        res = requests.get(url, params=params)
        return res.json()
    except Exception as e:
        return {"error": str(e)}
query = sys.argv[1]

BASE_URL = "http://localhost:8000"

def smile_overview():
    return safe_call(f"{BASE_URL}/smile_overview")

def query_knowledge(q):
    return safe_call(f"{BASE_URL}/query_knowledge", {"query": q})

def get_case_studies(q):
    return safe_call(f"{BASE_URL}/get_case_studies", {"query": q})

# ---- CALL TOOLS ----
smile = smile_overview()
knowledge = query_knowledge(query)
cases = get_case_studies(query)

# ---- COMBINE ----
combined = f"""
SMILE:
{smile}

KNOWLEDGE:
{knowledge}

CASE STUDIES:
{cases}
"""

# ---- LLM CALL ----
def call_llm(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False}
        )
        return res.json()["response"]
    except:
        return "LLM not running.\n" + prompt

final = call_llm(combined)

# ---- OUTPUT ----
print("\n--- SMILE OVERVIEW ---")
print(smile)

print("\n--- KNOWLEDGE ---")
print(knowledge)

print("\n--- CASE STUDIES ---")
print(cases)

print("\n--- FINAL ANSWER ---")
print(final)
