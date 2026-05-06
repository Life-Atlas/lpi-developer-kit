# HOW I DID IT

**Naman Anand — Track E: QA & Security**



## What I did, step by step

### Getting started

First thing I did was clone the repo and actually read the README properly. I know that sounds obvious but I've made the mistake before of jumping straight into code and missing important context. The README explained the MCP server architecture, the 7 tools, and the SMILE methodology — I needed that context before I could test anything meaningfully.

Then I ran the setup:

```
npm install
npm run build
npm run test-client
```

All 8 tests passed on the first try, which was a good sign that the environment was solid. I was on Node 18+ on Windows.

### Level 2 — Breaking the sandbox

My approach was basically: start with the edges and work inward.

I started by looking at what happens when the server receives garbage. I ran `node dist/src/index.js` directly and tried typing random stuff into stdin — plain text, SQL injection strings, just hitting enter. The server didn't crash, but it also didn't respond. It just sat there. That was my first finding — the stdio transport hangs on non-JSON input instead of rejecting it cleanly.

After that I went through each of the 7 tools one by one. For each tool I tried:
- Empty/missing required parameters
- Really long strings (600+ characters)
- Special characters (quotes, angle brackets, backslashes)
- Injection payloads (SQLi, XSS, path traversal patterns)

The good news is nothing actually broke in a dangerous way. The read-only architecture saved it every time. But I found a bunch of stuff that wasn't ideal — silent input truncation at 500 chars, error messages leaking file paths, no rate limiting, etc.

One thing I found by reading the code (not by fuzzing) was that `get_methodology_step` and `smile_phase_detail` literally call the same function. Like, identical. Both call `smilePhaseDetail(phase)`. That felt like a bug worth reporting even though it's not a security issue.

I also dug into the anonymizer code in `src/store/anonymizer.ts` and noticed the label arrays are small (7 company labels, 6 person labels) and they wrap around with modulo. So if you have 8 companies, company 1 and company 8 get the same anonymized label. That's a privacy problem.

### Level 3 — Auditing the vulnerable API

This was more straightforward because the vulnerabilities were intentional and pretty blatant (which I think was the point — testing whether you can identify and articulate them).

I opened `examples/vulnerable-api.py` and read through it top to bottom. It's only 88 lines so it didn't take long. I found 7 issues:

1. The `/api/run` endpoint just passes user input straight to `subprocess.check_output` with `shell=True`. That's RCE, game over.
2. SQL injection in `/api/query` — f-string directly in `db.execute()`. Classic.
3. Hardcoded API key and admin password right there in the source, plus `DEBUG_MODE = True` which dumps `os.environ` into every response. So even if the secrets weren't in the source, they'd be leaked through the debug output.
4. The admin endpoint takes the password as a GET query parameter. Passwords in URLs end up in browser history, server logs, proxy logs — everywhere.
5. XSS on the user endpoint — the `name` query parameter gets shoved straight into HTML without escaping.
6. IDOR — you can just iterate through `/api/user/1`, `/api/user/2`, etc. with no auth.
7. The app binds to `0.0.0.0` with debug mode on, so the Werkzeug debugger is accessible from the network. That's basically another RCE.

I didn't actually run the Flask app because honestly I didn't need to — the code speaks for itself. But I did verify each finding against the OWASP Top 10 (2021 edition) to make sure I was categorizing correctly.



## Problems I hit and how I solved them

**The stdio thing was confusing at first.** When I ran the server directly and started typing, nothing happened. No output, no error, nothing. I initially thought I was doing something wrong, maybe the server needed a specific initialization handshake. Then I realized — that *is* the bug. A well-behaved JSON-RPC server should respond with a parse error, not just silently consume input forever.

**Figuring out the 500 char truncation.** I noticed `MAX_INPUT_LENGTH = 500` in `index.ts` and `MAX_QUERY_LENGTH = 500` in `knowledge-store.ts`. So there's actually a double truncation happening — once in `sanitizeInput()` and again in `searchKnowledge()`. I had to trace through the code to understand the flow: user input → `sanitizeInput()` (truncate + strip control chars) → tool function → `searchKnowledge()` (truncate again + split terms). The second truncation is redundant but harmless.

**Windows path separator stuff.** The path traversal guard in `loadJSON()` uses `sep` from the `path` module. On Windows that's `\` not `/`. I had to think about whether `../` would still work or if it needed to be `..\`. Node's `resolve()` handles both, so the guard works either way — but it made me realize the guard is doing string prefix matching which is fragile. A better approach would be a filename whitelist.



## What I learned that I didn't know before

**MCP (Model Context Protocol) was completely new to me.** I'd never worked with it before. The idea of tools that an AI model can call via JSON-RPC over stdio is interesting. It's like function calling but standardized. Reading through the SDK and how the server registers handlers gave me a good mental model of how it works.

**The SMILE methodology.** I didn't know about the "Impact First, Data Last" philosophy before this. It actually makes a lot of sense — I've seen projects (not just digital twin stuff) fail because people started collecting data before defining what they wanted to achieve. The parallel to security is real: you should model your threat surface before you start writing firewall rules.

**`shell=True` in subprocess is even worse than I thought.** I knew it was bad, but I looked up some exploit examples while writing the report and realized you can chain commands, use backticks, pipes, redirects — basically the full shell is at the attacker's disposal. Even "sanitizing" the input wouldn't be enough because there are so many metacharacters. The only real fix is `shell=False` with an argument list, or better yet, not having the endpoint at all.

**The Werkzeug debugger RCE.** I knew running Flask with `debug=True` in production was bad practice, but I didn't realize the debugger actually gives you an interactive Python console in the browser if you can trigger a 500 error. Combined with binding to `0.0.0.0`, that's a second RCE path that's completely separate from the `/api/run` endpoint. Finding 7 was a good reminder that security misconfigurations can be just as dangerous as code-level vulnerabilities.

**Easter egg note:** I queried `query_knowledge` with the phrase "impact first data last" and found that **2** results mention "ontology."



