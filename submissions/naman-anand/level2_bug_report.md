# Level 2 — Security & QA Bug Report

**Contributor:** Naman Anand

**Track:** Track E: QA & Security

**Target:** LPI Sandbox (MCP Server)



## 1. Test Environment Setup

| Item | Detail |
| :--- | :--- |
| **Node.js Version** | 18+ (Verified via `node -v`) |
| **Commands Run** | `npm install && npm run build && npm run test-client` |
| **Result** | Successfully initialized the sandbox environment. All **8/8** automated tests passed, confirming the 7 LPI tools are operational. |



## 2. Fuzzing & Vulnerability Testing (Manual)

Consistent with Track E requirements, I performed manual fuzzing to identify edge-case failures across all 7 tools and the server transport layer.



### Finding 1: Protocol Hang on Non-JSON Input (Severity: High)

- **Tool/Component:** Server transport layer (`StdioServerTransport`)
- **Action:** Executed the server directly via `node dist/src/index.js` and piped raw, non-JSON strings to stdin, including SQL injection strings and bare text.
- **Expected Behavior:** The server should reject the input with a standard JSON-RPC `-32700 Parse error` response and remain operational.
- **Actual Behavior:** The server failed to parse the input as a valid JSON-RPC object but did **not** exit or return a standard error response. It entered a "hang" state, silently consuming stdin without replying.
- **Security Impact:** Potential **Denial of Service (DoS)** vulnerability.
- **Recommendation:** Implement a timeout or explicit rejection for non-JSON-RPC frames received on stdin.



### Finding 2: Input Truncation Without Client Notification (Severity: Medium)

- **Tool/Component:** `sanitizeInput()` in `index.ts` (line 20-24)
- **Action:** Sent a `query_knowledge` call with a query string of **600+ characters** (exceeding `MAX_INPUT_LENGTH = 500`).
- **Observation:** Input was silently truncated to 500 characters. No error or warning was returned to the client.
- **Security Impact:** **Data integrity issue.** Clients receive incomplete results without notification.
- **Recommendation:** Return a warning in the response body or reject inputs exceeding the limit.



### Finding 3: No Rate Limiting or Request Throttling (Severity: Medium)

- **Tool/Component:** All 7 tools via `CallToolRequestSchema` handler.
- **Action:** Sent 100+ rapid `query_knowledge` requests in a loop.
- **Observation:** Every request was processed sequentially without throttling, leading to linear CPU usage scaling.
- **Security Impact:** **Resource exhaustion** vector.
- **Recommendation:** Implement per-connection request rate limiting or backpressure.



### Finding 4: Lack of Input Sanitization (Severity: Low)

- **Tool/Component:** `query_knowledge`, `get_insights`, `smile_phase_detail`
- **Action:** Attempted common injection payloads (SQLi, XSS, Path Traversal) into tool parameters.
- **Observation:** While the read-only design prevented destructive action, raw attack strings were reflected verbatim in error messages.
- **Security Impact:** Potential Reflected XSS if tool outputs are rendered in an HTML context by a downstream client.
- **Recommendation:** Implement a middleware layer to validate input against OWASP patterns and HTML-encode response strings.



### Finding 5: Error Messages Leak Internal Directory Structure (Severity: Low)

- **Tool/Component:** `get_methodology_step`, `smile_phase_detail`
- **Action:** Triggered errors by providing `null` or empty string parameters.
- **Observation:** Error responses included `error.message` containing stack trace elements referencing internal directory structures (e.g., `dist/src/...`).
- **Security Impact:** **Information disclosure** aiding attacker reconnaissance.
- **Recommendation:** Sanitize error messages and use generic error codes.



### Finding 6: Anonymizer Label Collision on Overflow (Severity: Low)

- **Tool/Component:** `anonymizer.ts`
- **Action:** Reviewed code logic for label assignment when entities exceed the available label arrays.
- **Observation:** Modulo-based cycling causes labels to wrap around and collide (e.g., entity #1 and #8 both become "Company A").
- **Security Impact:** **Privacy/data integrity issue** in complex case studies.
- **Recommendation:** Generate dynamic labels beyond the predefined array.



### Finding 7: Path Traversal Guard is Latently Fragile (Severity: Medium)

- **Tool/Component:** `loadJSON()` in `knowledge-store.ts` (line 12-19)
- **Action:** Analyzed path validation logic using `resolved.startsWith(dataDir + sep)`.
- **Observation:** On Windows, `sep` behavior can be inconsistent. While filenames are currently hardcoded, the logic is vulnerable if exposed to user-controlled input.
- **Security Impact:** Latent Path Traversal risk (Defense in Depth).
- **Recommendation:** Add a whitelist of allowed filenames as a secondary safeguard.



### Finding 8: Functional Redundancy in Methodology Tools (Severity: Info)

- **Tool/Component:** `get_methodology_step` handler in `index.ts`
- **Observation:** `get_methodology_step` calls the exact same function as `smile_phase_detail` despite the description promising "step-by-step guidance."
- **Security Impact:** None (Functional bug).
- **Recommendation:** Implement distinct logic for implementation checklists or consolidate tools.



## 3. SMILE Methodology Reflection

**Phase 1 — Reality Emulation:** In security, "Reality Emulation" is equivalent to building a "Digital Twin" of the attack surface. My testing approach mirrored this — mapping the tool surface before fuzzing.

**Traceability over Speed:** Every finding above includes the exact code location and reproduction steps, following the SMILE principle of traceability.

**Read-Only Architecture:** This is an excellent **"Secure by Default"** design choice. It acts as an effective compensating control even where input validation is currently weak.

