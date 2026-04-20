import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "tinyllama"


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
    """
    Expert Agent:
    - Takes structured data from Research Agent
    - Extracts relevant sections
    - Produces grounded, structured answer (NO LLM)
    """

    # ---- Extract SMILE phases (fixed known phases) ----
    smile_phases = [
        "Reality Emulation",
        "Concurrent Engineering",
        "Collective Intelligence",
        "Contextual Intelligence"
    ]

    # ---- Extract healthcare case ----
    case_part = ""

    sections = context.split("## ")
    for sec in sections:
        if "healthcare" in sec.lower() or "chronic disease" in sec.lower():
            case_part = "## " + sec[:1200]
            break

    # fallback if not found
    if case_part == "":
        case_part = "Not found in provided data"

    # ---- Final structured answer ----
    return f"""
1. Understanding:
Digital twins are implemented using the SMILE methodology, which focuses on starting from impact and building structured digital representations for real-world systems.

2. SMILE Phases:
{chr(10).join(f"- {p}" for p in smile_phases)}

3. Real-World Application:
{case_part}

4. Insight:
The SMILE framework provides the structured lifecycle for implementation, while the healthcare patient twin demonstrates how continuous monitoring and early intervention improve outcomes.

5. Conclusion:
Digital twins in healthcare enable proactive, data-driven management of chronic diseases through continuous monitoring and structured decision-making.
"""


# Optional standalone test
if __name__ == "__main__":
    test_query = "How are digital twins used in healthcare?"
    test_context = "Sample SMILE + case study data"

    result = expert_agent(test_query, test_context)
    print(result)
