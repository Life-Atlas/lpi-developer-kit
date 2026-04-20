from tools import lpi_tool_1, lpi_tool_2

def agent(question):
    # ✅ Error handling: validate input
    if not question or not question.strip():
        print("❌ Error: Question cannot be empty.")
        return None

    print("\n🔹 User Question:", question)

    # ✅ Error handling: Tool 1
    try:
        result1 = lpi_tool_1(question)
        if result1 is None:
            print("⚠️ Warning: Tool 1 returned no data.")
            result1 = "Tool 1 data unavailable."
    except Exception as e:
        print(f"❌ Error in Tool 1: {e}")
        result1 = "Tool 1 failed."

    # ✅ Error handling: Tool 2
    try:
        result2 = lpi_tool_2(question)
        if result2 is None:
            print("⚠️ Warning: Tool 2 returned no data.")
            result2 = "Tool 2 data unavailable."
    except Exception as e:
        print(f"❌ Error in Tool 2: {e}")
        result2 = "Tool 2 failed."

    # ✅ Error handling: if both tools failed
    if result1 == "Tool 1 failed." and result2 == "Tool 2 failed.":
        print("❌ Both tools failed. Cannot generate answer.")
        return None

    final_answer = f"""
============================
 FINAL ANSWER:
{result1}
{result2}
----------------------------
📊 SUMMARY:
Linear regression predicts relationships using y = mx + c.
----------------------------
🧠 EXPLAINABILITY:
✔ Tool 1 → Used for theory
✔ Tool 2 → Used for example
============================
"""
    return final_answer

if __name__ == "__main__":
    # ✅ Error handling: catch keyboard interrupt and unexpected crash
    try:
        q = input("Enter your question: ")
        result = agent(q)
        if result:
            print(result)
    except KeyboardInterrupt:
        print("\n⚠️ Program interrupted by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
