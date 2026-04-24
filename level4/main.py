from agent_a import handle_request as agent_a
from agent_b import handle_request as agent_b

def run_system(user_input):
    try:
        if not user_input.strip():
            return "Error: Empty input"

        a_result = agent_a({"query": user_input})
        b_result = agent_b({"query": user_input})

        final = f"""
=== AGENT A (SMILE) ===
{a_result['data']}

=== AGENT B (INSIGHTS) ===
{b_result['data']}

=== FINAL OUTPUT ===
Combined recommendation based on both agents.
"""

        return final

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print(run_system("How to improve productivity?"))
