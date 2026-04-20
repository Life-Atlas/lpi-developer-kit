import requests
import json


# ---- LLM CALL ----
def ask_llm(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:5b",   # use stronger model now
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
    """
    Expected input:
    {
        "use_case": "...",
        "constraints": "...",
        "grounding_data": {
            "validated_insights": [],
            "case_points": [],
            "knowledge": ""
        }
    }
    """

    use_case = input_data.get("use_case", "")
    constraints = input_data.get("constraints", "")
    grounding = input_data.get("grounding_data", {})

    insights = grounding.get("validated_insights", [])
    cases = grounding.get("case_points", [])
    knowledge = grounding.get("knowledge", "")

    # ---- PROMPT ----
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
TASK
====================

Generate a constraint-aware deployment strategy.

====================
OUTPUT STRUCTURE
====================

1. Recommended Architecture
2. SMILE Phases (2–3 max, with justification)
3. Key Risks
4. What to Avoid
5. First 3 Actions
6. Decision Reasoning

====================
STRICT RULES
====================

- Use ONLY provided grounding data
- Do NOT invent technologies/tools
- Respect constraints strictly
- Prefer minimal viable solution
- Avoid generic explanations

If any rule is violated → internally fix before answering.
"""

    response = ask_llm(prompt)

    return {
        "strategy": response,
        "reasoning": "Generated using grounding agent data only"
    }


# ---- TEST ----
if __name__ == "__main__":
    sample_input = {
        "use_case": "ICU patient monitoring digital twin",
        "constraints": "2 developers, 3 months, no cloud",
        "grounding_data": {
            "validated_insights": ["Real-time monitoring is critical"],
            "case_points": ["Hospitals used phased deployment approach"],
            "knowledge": "Healthcare systems require reliability"
        }
    }

    output = run_agent_a(sample_input)

    print("\n--- AGENT A OUTPUT ---\n")
    print(json.dumps(output, indent=2))
