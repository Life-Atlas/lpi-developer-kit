import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"


def ask_llm(prompt):
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        data = res.json()
        return data.get("response", "LLM error: no response")

    except Exception as e:
        return f"LLM Error: {str(e)}"


def expert_agent(query, context):
    prompt = f"""
You are an expert AI using SMILE methodology.

User Query:
{query}

Available Data:
{context}

Instructions:
- Use ONLY provided data
- Do NOT invent new concepts
- Use correct SMILE phase names only
- If something is missing, say "Not found in provided data"

Output format:

1. Understanding
2. SMILE Phases
3. Explanation
4. Insight
5. Conclusion
"""

    return ask_llm(prompt)


# Optional standalone test
if __name__ == "__main__":
    test_query = "How are digital twins used in healthcare?"
    test_context = "Sample SMILE + case study data"

    result = expert_agent(test_query, test_context)
    print(result)
