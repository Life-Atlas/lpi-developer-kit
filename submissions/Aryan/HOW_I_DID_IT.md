# How I Built the LPI Life Agent

## Step-by-Step Process

### Phase 1: Understanding the LPI System

I started by exploring how the LPI (Life Programmable Interface) works. The initial example showed how to connect to tools, but it wasn’t clear how real tool execution happens. I realized that:

* The system uses JSON-RPC communication
* Tools are exposed via a Node.js server
* Proper initialization (`notifications/initialized`) is required before calling tools

This phase was mostly about understanding the protocol rather than writing code.

---

### Phase 2: Defining the Use Case

Instead of building a generic agent, I focused on a specific query:

> “How are digital twins used in healthcare?”

This helped me design the agent around:

* Conceptual understanding (methodology)
* Real-world application (case studies)

---

### Phase 3: Tool Selection Strategy

Rather than using many tools, I intentionally selected two:

* `smile_overview` → provides structured methodology
* `get_case_studies` → provides real-world implementations

The idea was:

> Combine theory + application to produce a meaningful answer

---

### Phase 4: Fixing Tool Execution

Initially, I used `test-client.js`, which only runs demo tests.

The key fix was:

* Switching to `dist/src/index.js` (actual server)
* Adding initialization message:

```json
{"jsonrpc": "2.0", "method": "notifications/initialized"}
```

Without this, tool calls returned empty results.

---

### Phase 5: Parsing Tool Output

The biggest challenge was handling tool responses.

The output format was nested:

```json
result → content → text
```

Instead of treating it as plain text, I extracted:

```python
content[0]["text"]
```

This allowed me to access actual usable data.

---

### Phase 6: Improving Relevance

The `get_case_studies` tool returned multiple industries.

Problem:

* The first case study was often unrelated (e.g., smart buildings)

Solution:

* Modified tool arguments:

  ```python
  {"query": "healthcare digital twin"}
  ```
* Extracted only the healthcare section from the response

This ensured the answer actually matched the user query.

---

### Phase 7: Structuring the Output

Instead of dumping raw text, I structured the response into:

* SMILE Framework (Summary)
* Case Study (Summary)
* Analysis
* Conclusion

This made the agent:

* easier to read
* more explainable
* aligned with real-world reasoning

---

## Problems I Faced

### 1. Wrong Execution Path

Using `test-client.js` resulted in logs instead of real data.

Fix:

* Switched to actual LPI server (`dist/src/index.js`)

---

### 2. Missing Initialization

Without sending the initialization message, tool calls silently failed.

Fix:

* Added JSON-RPC initialization before requests

---

### 3. Empty or Broken Output

Initially, outputs were empty or incomplete.

Cause:

* Using `readline()` instead of full output read

Fix:

* Switched to `process.communicate()`

---

### 4. Irrelevant Case Studies

Tool returned multiple industries.

Fix:

* Filtered for healthcare-specific content

---

### 5. Poor Summarization

Splitting by sentences broke headings like `# S.M.I.L.E.`

Fix:

* Switched to simple truncation (`text[:400]`)

---

## How I Solved Them

* Read and understood JSON-RPC communication instead of guessing
* Used proper server instead of test client
* Implemented structured parsing for nested responses
* Added domain-specific filtering for relevance
* Simplified summarization instead of overengineering

---

## What I Learned

### Tool Integration Matters More Than Models

The challenge wasn’t AI—it was correctly connecting and using tools.

---

### More Data ≠ Better Output

Raw tool output was too large and noisy. Filtering made answers significantly better.

---

### Explainability Improves Quality

Structuring output into sections made the agent more understandable and useful.

---

### Debugging Is the Real Work

Most time was spent fixing:

* paths
* protocol issues
* parsing

Not writing logic.

---

### Simplicity Wins

The final agent is simple:

* 2 tools
* basic parsing
* structured output

But it works reliably.

---

## Final Thoughts

This project was less about building a complex AI system and more about:

* understanding how tools communicate
* extracting meaningful information
* presenting it clearly

The biggest takeaway was that a good agent is not defined by complexity, but by:

> how effectively it connects, filters, and explains information.

---
