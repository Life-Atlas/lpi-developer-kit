import requests
from security import prevent_data_leak


# ---- LLM (same as your Level 3) ----
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
            return f"Unexpected LLM response: {data}"

    except Exception as e:
        return f"LLM Error: {str(e)}"


# ---- AGENT A ----
def run_agent_a(input_data):
    user_query = input_data.get("query", "")
    grounding = input_data.get("grounding_data", {})

    smile_data = grounding.get("smile_data", "")
    case_data = grounding.get("case_data", "")

    # ---- YOUR ORIGINAL PROMPT (slightly adapted) ----
    prompt = f"""
        You are a STRICT reasoning agent using SMILE methodology and real case study data.

        ====================
        INPUT
        ====================

        User Query:
        {user_query}

        SMILE Data:
        {smile_data}

        Case Study Data:
        {case_data}

        ====================
        MANDATORY RULES (NO EXCEPTIONS)
        ====================

        1. You MUST use ONLY the provided SMILE Data and Case Study Data.
        2. You MUST NOT use general knowledge.
        3. You MUST NOT invent examples, systems, or explanations.
        4. If information is missing → explicitly write: "Not specified in data".
        5. You MUST NOT introduce any SMILE phase not present in SMILE Data.

        ====================
        ALLOWED SMILE PHASES
        ====================

        Reality Emulation  
        Concurrent Engineering  
        Collective Intelligence  
        Contextual Intelligence  

        If a phase is not explicitly present in SMILE Data → DO NOT use it.

        ====================
        GROUNDING REQUIREMENTS
        ====================

        - Every claim MUST be traceable to SMILE Data or Case Study Data.
        - You MUST reference the case study explicitly (name or scenario).
        - Do NOT generalize beyond given data.
        - Keep reasoning tight and evidence-based.

        ====================
        OUTPUT STRUCTURE (STRICT)
        ====================

        1. Understanding:
        Explain ONLY using SMILE Data (no external explanation).

        2. Key SMILE Phases:
        - Select ONLY 2–3 phases from allowed list
        - Each phase must be justified using provided data

        3. Real-World Application:
        - Use ONLY the given case study
        - Describe what was done (no assumptions)

        4. Insight:
        - Connect SMILE phases with the case study
        - No generic statements

        5. Conclusion:
        - Short, grounded summary

        ====================
        STYLE CONSTRAINTS
        ====================

        - Be concise
        - Avoid long explanations
        - Avoid generic AI statements
        - No extra information outside provided data

        ====================
        FINAL CHECK (MANDATORY)
        ====================

        Before answering, ensure:
        - No invented SMILE phases
        - No general knowledge used
        - All statements trace back to input data

        If any rule is violated → correct internally before answering.
        """

    response = ask_llm(prompt)
    response = prevent_data_leak(response)

    return {
        "answer": response,
        "source": "Agent A (SMILE reasoning)"
    }


# ---- TEST ----
if __name__ == "__main__":
    sample_input = {
        "query": "How are digital twins used in healthcare?",
        "grounding_data": {
            "smile_data": "SMILE methodology phases...",
            "case_data": "Healthcare digital twin case study..."
        }
    }

    output = run_agent_a(sample_input)
    print(output["answer"])
