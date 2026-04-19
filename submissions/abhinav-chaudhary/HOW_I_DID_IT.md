# HOW I DID IT (Level 2)

## Steps I followed
- First, I cloned the repository and installed all dependencies using npm install.
- Then I built the project and ran the test-client to check if everything was working properly.
- After confirming that all tools passed, I installed Ollama to try running a local LLM.
- I ran the llama3 model and asked it about SMILE to understand how it works.

## Problems I faced
- At first, I wasn’t very clear on how to run a local LLM since I hadn’t done it before.
- Also, the model download took quite a bit of time, which made me think something might be wrong.

## How I solved them
- I carefully followed the Ollama setup instructions and verified each step.
- For the download issue, I just waited patiently and let it complete, and then everything worked fine.

## What I learned
- I learned how to set up and run a local LLM using Ollama, which was new for me.
- I also understood that SMILE focuses a lot on explainability, not just giving answers.
- Overall, I got a better idea of how LPI combines multiple tools to generate more reliable outputs.

# HOW I DID IT (Level 3)

## Steps I followed
- I first read the Level 3 requirements and looked at the example agent to understand what was expected.
- Instead of copying it directly, I decided to build something simpler that I could actually understand and explain.
- I planned a basic flow — take a question, decide which tools to use, call them, and combine the results.
- Then I figured out how MCP works and implemented tool calls using JSON-RPC.
- After that, I added a simple keyword-based logic to select tools.
- Finally, I focused on making the output clear — showing reasoning, answer, and sources.

---

## Problems I faced
- At the start, MCP was confusing. I didn’t understand how the requests and responses actually work.
- The structure of tool outputs (content blocks, text extraction) was also not very clear.
- My earlier version worked, but it didn’t clearly show that tools were being used, which affected the evaluation.

---

## How I solved them
- I broke the example agent into small parts and tried to understand each step instead of copying everything.
- I simplified the logic a lot and avoided adding anything I didn’t fully understand.
- I added clear prints/logs so it’s obvious when a tool is being called and what it returns.
- I also added basic error handling so the agent doesn’t crash on bad input.

---

## What I learned
- How MCP actually works and how tools are called using JSON-RPC
- How to combine outputs from multiple tools into a single response
- That explainability is important — not just the answer, but how you got it
- Keeping things simple is better than overcomplicating, especially when learning something new
