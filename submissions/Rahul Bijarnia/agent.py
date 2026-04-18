from tools import lpi_tool_1, lpi_tool_2

def agent(question):
    print("\n🔹 User Question:", question)

    # ✅ FIRST define result1 and result2
    result1 = lpi_tool_1(question)
    result2 = lpi_tool_2(question)

    # ✅ THEN use them
    final_answer = f"""
============================

📌 FINAL ANSWER:

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
    q = input("Enter your question: ")
    print(agent(q))