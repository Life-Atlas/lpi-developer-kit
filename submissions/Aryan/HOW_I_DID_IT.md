# HOW_I_DID_IT

## Overview

I built a Python-based agent that connects to the LPI (Life Programmable Interface) sandbox and answers questions by selecting and calling relevant tools. The agent uses multiple tools, processes their outputs, and generates a structured response.

---

## Approach

### 1. Understanding the LPI Setup

* Explored the LPI Developer Kit to understand available tools.
* Identified that tools are exposed via a Node.js server (`dist/src/index.js`), not the test client.
* Learned that communication follows a JSON-RPC pattern.

---

### 2. Building the Agent

* Created a Python script (`agent.py`) to:

  * Accept user input
  * Select relevant tools
  * Call tools via subprocess (Node.js)
  * Process and combine results

---

### 3. Tool Integration

* Used two tools:

  * `smile_overview` → for methodology explanation
  * `get_case_studies` → for real-world examples

* Implemented subprocess communication:

  * Started Node server using `subprocess.Popen`
  * Sent JSON-RPC requests via stdin
  * Received responses via stdout

---

### 4. Handling Protocol Issues

Initial attempts failed due to:

* Using `test-client.js` instead of the actual server
* Missing initialization step

Fixes:

* Switched to `dist/src/index.js`
* Added:

  ```json
  {"jsonrpc": "2.0", "method": "notifications/initialized"}
  ```

---

### 5. Parsing Tool Output

* Tool responses returned nested JSON:

  ```json
  {
    "result": {
      "content": [
        { "type": "text", "text": "..." }
      ]
    }
  }
  ```
* Extracted actual text using:

  ```python
  result["content"][0]["text"]
  ```

---

### 6. Improving Relevance

Problem:

* Case studies returned multiple industries, not always healthcare.

Fix:

* Modified tool arguments:

  ```python
  {"query": "healthcare digital twin"}
  ```
* Extracted only the healthcare-related section from the response.

---

### 7. Result Processing

* Implemented simple summarization:

  * Trimmed text instead of splitting sentences (to avoid broken headings)
* Combined:

  * SMILE methodology summary
  * Healthcare case study
  * Analysis + conclusion

---

## Challenges Faced

### 1. Incorrect Tool Execution

* Initially used `test-client.js`
* Result: only test logs, no usable data

### 2. Path and Environment Issues

* Node process couldn’t find server files
* Fixed using:

  ```python
  cwd="lpi-developer-kit"
  ```

### 3. Empty Outputs

* Caused by incorrect JSON parsing and incomplete reads
* Fixed using `process.communicate()` and proper parsing

### 4. Irrelevant Case Study Results

* Default tool output included multiple industries
* Fixed by filtering healthcare-specific content

---

## Key Learnings

* Tool-based agents depend more on **data flow and integration** than model complexity
* Correct environment setup is critical (paths, working directory, build)
* Parsing structured responses properly is essential
* Multi-tool orchestration improves answer quality significantly
* Relevance filtering is necessary when tools return broad results

---

## Final Outcome

The agent:

* Uses multiple tools
* Retrieves real data from LPI
* Processes and filters results
* Produces structured, relevant answers

---
