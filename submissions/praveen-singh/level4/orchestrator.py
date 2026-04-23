import json
from agent_a_expert import run_agent_a
from agent_b_grounding import run_agent_b

# ---- SECURITY IMPORTS ----
from security import (
    sanitize_input,
    validate_length,
    validate_agent_call,
    prevent_data_leak
)


# ---- ORCHESTRATOR ----
def run_system():
    print("=== LPI MULTI-AGENT SYSTEM ===\n")

    try:
        # ---- SECURE INPUT ----
        use_case = input("Enter use case: ")
        use_case = sanitize_input(use_case)
        use_case = validate_length(use_case)

        constraints = input("Enter constraints: ")
        constraints = sanitize_input(constraints)
        constraints = validate_length(constraints)

    except ValueError as e:
        print(f"[SECURITY BLOCKED INPUT]: {e}")
        return

    # ---- STEP 1: CALL AGENT B ----
    print("\n[Orchestrator] Calling Grounding Agent...\n")

    try:
        grounding_output = run_agent_b({
            "use_case": use_case
        })
    except Exception as e:
        print(f"[ERROR - Agent B]: {e}")
        return

    # ---- SANITIZE AGENT B OUTPUT ----
    grounding_output = {
        "validated_insights": [
            prevent_data_leak(i) for i in grounding_output.get("validated_insights", [])
        ],
        "case_points": [
            prevent_data_leak(c) for c in grounding_output.get("case_points", [])
        ],
        "knowledge": prevent_data_leak(grounding_output.get("knowledge", ""))
    }

    print("[Agent B Output]")
    print(json.dumps(grounding_output, indent=2))

    # ---- STEP 2: PREPARE AGENT A INPUT ----
    agent_a_input = {
        "use_case": use_case,
        "constraints": constraints,
        "grounding_data": grounding_output
    }

    # ---- PRIVILEGE ESCALATION CHECK ----
    try:
        validate_agent_call(agent_a_input)
    except ValueError as e:
        print(f"[SECURITY BLOCKED]: {e}")
        return

    # ---- STEP 3: CALL AGENT A ----
    print("\n[Orchestrator] Calling Decision Agent...\n")

    try:
        final_output = run_agent_a(agent_a_input)
    except Exception as e:
        print(f"[ERROR - Agent A]: {e}")
        return

    # ---- SANITIZE FINAL OUTPUT ----
    final_strategy = prevent_data_leak(final_output.get("strategy", ""))

    # ---- FINAL RESULT ----
    print("\n=== FINAL DEPLOYMENT STRATEGY ===\n")
    print(final_strategy)

    print("\n=== TRACE (Explainability) ===\n")
    print("Grounding data used →")
    print(json.dumps(grounding_output, indent=2))


# ---- RUN ----
if __name__ == "__main__":
    run_system()
