# HOW I DID IT

## What I Built
I built an AI agent in Python that connects to the LPI MCP server 
and answers questions using the SMILE methodology knowledge base.
The agent accepts a user question, queries multiple LPI tools, 
combines the results, and returns an explainable answer that 
cites exactly which tools provided which information.
 
## Step by Step Process

### Step 1 - Understanding the LPI Tools
I first ran the LPI sandbox locally using npm run build and 
npm run test-client to see all 7 tools and understand what 
each one returns. I tested smile_overview, query_knowledge, 
and get_case_studies manually before writing any agent code.

### Step 2 - Building the Agent
I started with a simple function that calls one tool, then 
expanded it to call multiple tools. I used subprocess to 
communicate with the Node.js LPI server via JSON-RPC protocol.
The agent accepts a command line question, passes it to the 
tools, and combines their outputs into a final answer.

### Step 3 - Adding Explainability
I made the agent print which tool each piece of information 
came from. This way the user can trace every part of the 
answer back to its source. The output clearly labels 
[Source: smile_overview] and [Source: query_knowledge] 
so nothing is a black box.

### Step 4 - Adding Error Handling
After the first submission I realized my code had no error 
handling. I added try/except blocks around every tool call 
to handle timeouts, bad JSON responses, FileNotFoundError 
if Node.js is missing, and general exceptions. I also added 
input validation so the agent does not crash on empty input.
I added graceful fallback so if one tool fails the agent 
continues with the other tool instead of stopping completely.

## Problems I Hit

### Problem 1 - JSON-RPC Format
I did not know the exact format the LPI server expected. 
I had to read the MCP protocol documentation and look at 
the example agent.py to understand the jsonrpc 2.0 format.

### Problem 2 - Path Issues
The path to the LPI server dist/src/index.js kept failing 
because I was running the agent from the wrong directory. 
I fixed this by using an absolute path.

### Problem 3 - Empty Responses
Sometimes the tool returned empty stdout. I added a check 
for result.stdout.strip() being empty before trying to 
parse it as JSON, which fixed silent failures.

## What I Learned
- How MCP protocol works with JSON-RPC over subprocess
- How to build an agent that cites its sources
- Why error handling must come first not last
- How the SMILE methodology structures digital twin thinking
- That explainability means showing your work, not just results

## What I Would Do Differently
I would write error handling from the very first commit. 
I would also add a logging module to save errors to a file 
instead of just printing them, because in production nobody 
watches the terminal. I would also add unit tests for each 
tool call so regressions are caught automatically.
