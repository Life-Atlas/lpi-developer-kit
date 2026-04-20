from agent_b_researcher import researcher_agent
from agent_a_expert import expert_agent


def orchestrate(query):
    print("\n=== ORCHESTRATOR START ===")

    # Step 1: Research
    print("\n[Step 1] Researching...")
    context, tools_used = researcher_agent(query)

    print("\n--- TOOLS USED ---")
    for t in tools_used:
        print("-", t)

    # Step 2: Expert reasoning
    print("\n[Step 2] Expert analysis...")
    answer = expert_agent(query, context)

    print("\n=== FINAL ANSWER ===\n")
    print(answer)

    print("\n=== TRACE ===")
    print("Tools Used:", tools_used)


# CLI entry
if __name__ == "__main__":
    user_query = input("Enter your question: ")
    orchestrate(user_query)
