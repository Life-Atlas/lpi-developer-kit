# Level 2 — QA & Security Bug Report  
Name: Kailash Narayana Prasad  

## Objective  
To test the robustness of the LPI sandbox by providing unexpected and invalid inputs and documenting system behavior, failures, and error handling.

---

## Test Cases & Results  

### 1. Normal Query  
- Input: "explainable AI"  
- Result: Returned valid results  
- Status: Working correctly  

---

### 2. Long Input (Stress Test)  
- Input: Very long string (10,000+ characters)  
- Result: No crash, returned "No knowledge entries found"  
- Status: Did not break  

- Observation:  
  - System accepts very large inputs  
  - No input size restriction  

- Risk:  
  - Possible Denial of Service (DoS) if abused  

---

### 3. Special Characters  
- Input: "!@#$%^&*()_+{}[]<>?/\\|"  
- Result: No crash, returned no results  
- Status: Handled safely  

---

### 4. SQL Injection Attempt  
- Input: "' OR 1=1 --"  
- Result: Returned normal results  
- Status: Did not break  

- Observation:  
  - No visible SQL execution  
  - No explicit sanitization feedback  

---

### 5. Empty Input  
- Input: ""  
- Result: Error → `'query' parameter is required`  
- Status: Proper validation  

---

### 6. Null Input  
- Input: null  
- Result: Error → `'query' parameter is required`  
- Status: Proper validation  

---

### 7. Invalid Data Type (CRITICAL ISSUE)  
- Input: 12345 (number instead of string)  

- Result:  
  - Error: `input.slice is not a function`  
  - Logged internally:  
    `[LPI Sandbox] Error in tool query_knowledge: input.slice is not a function`  
  - BUT system still shows `[PASS]`  

- Status: BROKEN  

- What broke:  
  - System tries to use `.slice()` on non-string input  
  - No type validation before processing  

- Issue:  
  - Internal error occurs  
  - Incorrectly marked as PASS  

- Risk:  
  - Runtime crashes  
  - Misleading success status  
  - Hard debugging  

---

### 8. get_case_studies Invalid Input  
- Input: query = 12345  

- Result:  
  - Error: `input.slice is not a function`  
  - Same internal log error  
  - Still marked as `[PASS]`  

- Status: BROKEN  

- What broke:  
  - Same type validation issue across multiple tools  

---

### 9. get_case_studies Empty Query  
- Input: ""  
- Result: Returned default case studies  
- Status: Inconsistent behavior  

- Observation:  
  - No validation  
  - Falls back to default data  

---

## Key Findings  

### What Broke
- Invalid data type inputs cause runtime errors  
- System incorrectly marks failed operations as PASS  

### What Didn’t Break (but is risky)
- Long input accepted without restriction  
- SQL-like input processed without validation  
- Empty query inconsistently handled  

### Error Messages Observed
- `input.slice is not a function`  
- `'query' parameter is required`  

---

## Summary  

- System is stable and does not crash completely  
- However, major validation issues exist  
- Error handling is inconsistent  
- PASS/FAIL reporting is unreliable  

---

## Recommendations  

- Add strict type validation (string checks)  
- Fix PASS/FAIL reporting logic  
- Add input size limits  
- Ensure consistent validation across all tools  
- Improve error messages for debugging  

---

## Conclusion  

The LPI sandbox is functionally stable but has critical weaknesses in input validation and error reporting. These issues can lead to runtime errors and misleading test results, which should be addressed to improve reliability and security.

---

## Test Client Output
```[PASS] smile_overview({})
[PASS] smile_phase_detail({"phase":"reality-emulation"})
[PASS] list_topics({})
[PASS] query_knowledge({"query":"explainable AI"})
[PASS] query_knowledge({"query":"AAAAAAAA...long input"})
[PASS] query_knowledge({"query":"!@#$%^&*()_+{}[]<>?/\|"})
[PASS] query_knowledge({"query":"' OR 1=1 --"})
[PASS] query_knowledge({"query":""})
[PASS] query_knowledge({"query":null})
[PASS] query_knowledge({"query":12345})
[PASS] get_case_studies({})
[PASS] get_case_studies({"query":12345})
[PASS] get_case_studies({"query":""})
[PASS] get_case_studies({"query":"smart buildings"})
[PASS] get_insights({"scenario":"personal health digital twin","tier":"free"})
[PASS] get_methodology_step({"phase":"concurrent-engineering"})

=== Results ===
Passed: 16/16
Failed: 0/16
```
---

## LLM Output Observation

The system generated outputs related to digital twins, particularly in scenarios like "personal health digital twin". This confirms that the system is capable of producing domain-specific and context-aware responses.
