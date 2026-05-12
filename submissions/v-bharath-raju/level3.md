# Level 3 - Security Audit Report
## Repository

https://github.com/bharathraju03/lpi-developer-kit
## Vulnerability 1: SQL Injection
- Location: /api/query
- OWASP: Injection
- Description: User input is directly used in SQL query without sanitization.
- Impact: Attackers can manipulate database queries and corrupt data.
- Fix: Use parameterized queries.

## Vulnerability 2: Command Injection
- Location: /api/run
- OWASP: Injection
- Description: System commands are executed using user input with shell=True.
- Impact: Remote code execution and full system compromise.
- Fix: Remove shell=True and restrict allowed commands.

## Vulnerability 3: Hardcoded Secrets
- Location: Source code
- OWASP: Sensitive Data Exposure
- Description: API key and admin password are hardcoded.
- Impact: Unauthorized access to protected endpoints.
- Fix: Store secrets in environment variables.

## Vulnerability 4: Debug Information Exposure
- Location: /api/query response
- OWASP: Security Misconfiguration
- Description: Debug mode exposes server path, environment variables, and API key.
- Impact: Sensitive data leakage.
- Fix: Disable debug mode and remove sensitive output.

## Vulnerability 5: Broken Authentication
- Location: /api/admin
- OWASP: Broken Authentication
- Description: Plain text password comparison is used.
- Impact: Easy unauthorized admin access.
- Fix: Use hashed passwords and proper authentication.

## Vulnerability 6: Cross-Site Scripting (XSS)
- Location: /api/user/<id>
- OWASP: XSS
- Description: User input is rendered in HTML without sanitization.
- Impact: Execution of malicious scripts in browser.
- Fix: Escape user input before rendering.

## Vulnerability 7: Broken Access Control
- Location: /api/user/<id>
- OWASP: Broken Access Control
- Description: No authentication required to access user data.
- Impact: Unauthorized data access.
- Fix: Implement access control checks.

## Vulnerability 8: Information Disclosure
- Location: /api/query
- OWASP: Security Misconfiguration
- Description: Detailed error messages and stack traces are exposed.
- Impact: Attackers gain insight into internal system structure.
- Fix: Disable debug mode and return generic error messages.

## LPI Sandbox Audit (src/)
- Reviewed the sandbox server code.
- No critical vulnerabilities found.
- Input handling appears safe and controlled.
## LPI Tool Usage

I used the LPI sandbox tools during my analysis:

- query_knowledge("explainable AI")  
  → Returned knowledge entries related to explainable AI in digital twin systems.

- get_insights("personal health digital twin")  
  → Provided insights into healthcare digital twin implementations and modeling.

These helped me understand expected system behavior and compare it with the vulnerable API.
## Proof of Exploitation

### SQL Injection
Request:
http://127.0.0.1:5001/api/query?q=' OR 1=1 --

Observation:
Application throws SQL error, confirming unsanitized input handling.

### Command Injection
Request:
http://127.0.0.1:5001/api/run?cmd=whoami

Output:
Shows system username → confirms remote command execution.

### XSS
Request:
http://127.0.0.1:5001/api/user/1?name=<script>alert(1)</script>

Observation:
Script executes in browser → confirms XSS vulnerability.
## Conclusion
The API contains multiple critical vulnerabilities including injection attacks, exposed secrets, and missing authentication. Immediate fixes are required before deployment.
<!-- level 3 final submission -->