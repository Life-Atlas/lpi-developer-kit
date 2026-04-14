Security audit report

I ran the vulnerable API locally and tested the endpoints manually and then reviewed the code to confirm the issues I found.

I found several security problems.

1. Hardcoded secrets

The API key and admin password are written directly in the code.

OWASP category: A07:2021 – Identification and Authentication Failures

Impact:
If someone gets access to the code they get those secrets straight away. The admin password is also very weak so it would be easy to guess.

Fix:
Secrets should not be hardcoded. They should be stored in environment variables or a secret manager instead. The password should also be replaced with a much stronger one.

2. Debug information leakage

The /api/query endpoint returns debug information when debug mode is enabled including environment variables, the server path, and the API key.

OWASP category: A05:2021 – Security Misconfiguration

Impact:
This reveals a lot of internal information that normal users should not be able to see. That kind of detail could help an attacker understand the system better and make it easier to find more weaknesses.

Fix:
Debug information should not be included in API responses. Environment variables, file paths, and secrets should never be exposed to users.

3. SQL injection risk

In /api/query, user input is placed directly into an SQL statement using an f-string.

OWASP category: A03:2021 – Injection

Impact:
This creates a risk of SQL injection. In a real system that could let someone break the query or interact with the database in ways they should not be able to.

Fix:
The SQL statement should use parameterized queries instead of string formatting.

4. Command injection

The /api/run endpoint takes user input and runs it as a system command using shell=True.

OWASP category: A03:2021 – Injection

Impact:
This is the most serious problem in the file. If an attacker can control that input they may be able to run commands directly on the server. That could lead to full control depending on what the process is allowed to do.

Fix:
The best fix would be to remove this endpoint completely. If something like it really has to exist it should only allow a very small set of safe commands and should not use shell=True.

5. Weak admin authentication

The /api/admin endpoint checks a password passed in the URL.

OWASP category: A07:2021 – Identification and Authentication Failures

Impact:
Passwords should not be sent in the URL because they can end up in browser history, logs, and proxies. There is also no real login flow and no protection against repeated guesses.

Fix:
This should use proper authentication instead of a password in the query string. It should also have better access control and some protection against brute force attempts.

6. Reflected XSS

The /api/user/<user_id> endpoint puts user-controlled input directly into HTML without escaping it.

OWASP category: A03:2021 – Injection

Impact:
This means an attacker may be able to inject JavaScript into the page. In a real application that could be used to run code in another user’s browser, steal session data, or trick users into doing something they did not mean to do.

Fix:
User input should be escaped before being added to HTML. A safer option would be to use a template engine with auto-escaping instead of building HTML manually.

7. Sensitive information printed to console

When the app starts it prints the API key directly to the console.

OWASP category: A05:2021 – Security Misconfiguration

Impact:
Even if it is only printed to the console it is still a bad idea. Console output can end up in logs, screenshots, or shared terminals.

Fix:
Secrets should never be printed to the console or logs.
