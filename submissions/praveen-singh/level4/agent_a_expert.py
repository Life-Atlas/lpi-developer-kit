import requests
from security import prevent_data_leak


# ---- LLM CALL ----
def ask_llm(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:1.5b",
                "prompt": prompt,
                "stream": False
            }
        )

        data = res.json()

        if "response" in data:
            return data["response"]
        else:
            return str(data)

    except Exception as e:
        return f"LLM Error: {str(e)}"


# ---- MAIN FUNCTION ----
def run_agent_a(input_data):
    use_case = input_data.get("use_case", "")
    constraints = input_data.get("constraints", "")
    grounding = input_data.get("grounding_data", {})

    insights = grounding.get("validated_insights", [])
    cases = grounding.get("case_points", [])
    knowledge = grounding.get("knowledge", "")

    # ---- STRICT PROMPT ----
    prompt = f"""
You are a deployment strategy decision agent.

You MUST generate a deployment strategy using ONLY the provided grounding data.

====================
INPUT
====================

Use Case:
{use_case}

Constraints:
{constraints}

Validated Insights:
{insights}

Case Study Points:
{cases}

Knowledge:
{knowledge}

====================
CRITICAL RULES
====================

- Use ONLY the provided grounding data
- Do NOT invent technologies, tools, or components
- Do NOT assume system elements (e.g., sensors, pipelines) unless explicitly mentioned
- Ignore cross-domain or irrelevant case studies
- If data is insufficient → stay minimal and conservative
- Respect constraints strictly
- Prefer simplest viable solution

====================
OUTPUT STRUCTURE
====================

1. Recommended Architecture
2. SMILE Phases (2–3 max, justified using data)
3. Key Risks
4. What to Avoid
5. First 3 Actions
6. Decision Reasoning (must reference insights or case data)

====================
QUALITY CHECK
====================

Before answering:
- Remove any invented elements
- Ensure all decisions trace back to provided data
- Avoid generic statements

If any rule is violated → internally fix before answering.
"""

    response = ask_llm(prompt)
    response = prevent_data_leak(response)

    return {
        "strategy": response,
        "reasoning": "Generated using strictly grounded data"
    }


# ---- TEST ----
if __name__ == "__main__":
    sample_input = {
        "use_case": "ICU patient monitoring digital twin",
        "constraints": "2 developers, 3 months, no cloud",
        "grounding_data": {
            "validated_insights": ["Real-time monitoring is critical"],
            "case_points": ["Phased deployment improves reliability"],
            "knowledge": "Healthcare systems require reliability"
        }
    }

    output = run_agent_a(sample_input)

    print(output["strategy"])
