import subprocess

def run_agent(query):
    print("Running LPI Agent...\n")

    try:
        result = subprocess.run(
            ["python3", "examples/agent.py", query],
            capture_output=True,
            text=True
        )

        return result.stdout

    except Exception as e:
        return f"Error running agent: {str(e)}"


def format_response(raw_output, user_query):
    return f"""
===============================
SMART HEALTH ADVISOR RESPONSE
===============================

User Query:
{user_query}

-------------------------------
Analysis:
This response is generated using LPI tools including:
- SMILE methodology overview
- Knowledge base queries
- Case studies

-------------------------------
Agent Output:
{raw_output}

-------------------------------
Explainability:
The agent combines structured knowledge from SMILE and relevant insights to generate actionable advice.

The reasoning is based on:
1. Understanding the user problem
2. Retrieving structured knowledge
3. Synthesizing recommendations

===============================
"""


if __name__ == "__main__":
    query = input("Enter your health query: ")
    raw = run_agent(query)
    final_output = format_response(raw, query)
    print(final_output)
