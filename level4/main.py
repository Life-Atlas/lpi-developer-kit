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
{a_result.get('data', 'No data')}

=== AGENT B (INSIGHTS) ===
{b_result.get('data', 'No data')}

=== FINAL RECOMMENDATION ===
Based on SMILE methodology and insights:

- Improve your daily routine by focusing on sleep, exercise, and learning habits
- Apply structured planning to your day for better productivity
- Use insights from your input to adjust your workflow and reduce distractions

=== EXPLAINABILITY ===
This result was generated using:
- smile_overview (Agent A)
- get_insights (Agent B)
"""
