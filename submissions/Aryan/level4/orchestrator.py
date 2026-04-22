import json
from agent_a import run_agent_a
from agent_b import run_agent_b

# ---- SECURITY ----
from security import sanitize_input, validate_length, prevent_data_leak


# ---- ORCHESTRATOR ----
def run_system():
    print("=== ORCHESTRATOR START ===\n")

    # ---- USER INPUT (same as your original) ----
    try:
        user_query = input("Enter your question: ")
        user_query = sanitize_input(user_query)
        user_query = validate_length(user_query)
    except ValueError as e:
        print(f"[SECURITY BLOCKED]: {e}")
        return

    # ---- STEP 1: AGENT B (RESEARCH) ----
    print("\n[Step 1] Researching...\n")

    try:
        grounding_output = run_agent_b({
            "query": user_query
        })
    except Exception as e:
        print(f"[Agent B Error]: {e}")
        return

    # ---- SANITIZE OUTPUT ----
    grounding_output = {
        "smile_data": prevent_data_leak(grounding_output.get("smile_data", "")),
        "case_data": prevent_data_leak(grounding_output.get("case_data", "")),
        "sources": grounding_output.get("sources", [])
    }

    print("[Agent B Output Ready]\n")

    # ---- STEP 2: AGENT A (REASONING) ----
    print("[Step 2] Generating answer...\n")

    try:
        final_output = run_agent_a({
            "query": user_query,
            "grounding_data": grounding_output
        })
    except Exception as e:
        print(f"[Agent A Error]: {e}")
        return

    # ---- FINAL OUTPUT ----
    answer = prevent_data_leak(final_output.get("answer", ""))

    print("----- FINAL ANSWER -----\n")
    print(answer)

    # ---- SOURCES (same as your Level 3 requirement) ----
    print("\n----- SOURCES -----")
    for src in grounding_output.get("sources", []):
        print(f"- {src}")


# ---- RUN ----
if __name__ == "__main__":
    run_system()
