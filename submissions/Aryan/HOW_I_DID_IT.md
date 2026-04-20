# How I Did It — Level 3

## What I built

I built an explainable agent using the LPI (Life Programmable Interface) that answers user queries by combining SMILE methodology knowledge with real-world case studies.

Instead of returning raw tool outputs, the agent uses an LLM (Qwen via Ollama) to generate structured, grounded responses.

---

## Step-by-step approach

### 1. Understanding the LPI tools

I first explored the available tools in the LPI server:

* `smile_overview` → methodology
* `get_case_studies` → real-world examples
* `get_methodology_step`, `get_insights` → implementation guidance

This helped me understand how to combine conceptual knowledge with practical use cases.

---

### 2. Setting up tool communication

I used Python’s `subprocess` to communicate with the LPI server (`dist/src/index.js`) via JSON-RPC.

Steps:

* Initialize the server connection
* Send tool call requests
* Parse nested responses (`result → content → text`)

---

### 3. Implementing tool selection

Instead of calling fixed tools, I added simple query-based logic:

* “how / use” → `smile_overview`, `get_case_studies`
* “implement / steps” → `get_methodology_step`, `get_insights`
* fallback → `query_knowledge`, `get_case_studies`

This makes the agent more adaptive to different types of queries.

---

### 4. Filtering tool outputs

The `get_case_studies` tool returns multiple entries.
To improve relevance, I filtered results to extract only healthcare-related sections.

This reduces noise and improves the quality of the final answer.

---

### 5. Adding LLM reasoning

I integrated Qwen (via Ollama) to:

* combine outputs from multiple tools
* generate structured answers
* enforce grounding using prompt constraints

Instead of summarizing manually, the LLM performs reasoning across both SMILE data and case studies.

---

### 6. Prompt design

I designed a structured prompt that:

* forces use of both SMILE and case study data
* prevents hallucinated examples
* enforces a clear output format:

  * Understanding
  * SMILE Phases
  * Real-World Application
  * Insight
  * Conclusion

---

### 7. Final pipeline

The agent works as follows:

1. User enters query
2. Relevant tools are selected
3. LPI tools are called via JSON-RPC
4. Outputs are parsed and filtered
5. Combined context is sent to LLM
6. LLM generates structured final answer

---

## Challenges faced

* Parsing nested JSON-RPC responses reliably
* Controlling LLM hallucination while still allowing useful reasoning
* Filtering large tool outputs to keep only relevant content
* Balancing strict grounding with readable answers

---

## What worked well

* Combining methodology + case study gives much stronger answers
* Prompt constraints significantly reduce hallucination
* Simple rule-based tool selection is effective and reliable

---

## What I would improve next

* Add reasoning trace (why tools were selected)
* Implement multi-step reasoning instead of single-pass generation
* Improve error handling for tool and LLM failures
* Replace rule-based selection with more adaptive logic

---

## Final takeaway

The key learning was that building an effective agent is not just about calling tools, but about **how their outputs are filtered, combined, and reasoned over** using an LLM.
