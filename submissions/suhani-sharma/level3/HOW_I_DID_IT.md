# How I Did It - Level 3

### What I did, step by step

I first went through the Level 3 requirements to understand what exactly needed to be built. The main goal was to create an AI agent that connects to the LPI Sandbox and uses its tools.

I created a Python file (agent.py) and made the agent take user input about study habits like study time and distractions. Based on this input, it forms a query related to improving focus using the SMILE methodology.

Then I connected the agent to the LPI MCP server using subprocess and initialized it properly using JSON-RPC.

After that, I used two LPI tools:

query_knowledge to get relevant information
get_insights to get practical suggestions

Finally, I combined the outputs and displayed them in a simple format with Advice, Suggestions, and Sources.

I also tried integrating a local LLM using Ollama to make the responses better.

---

### What problems I hit and how I solved them

Initially, I had trouble understanding how to connect to the MCP server and how to format the requests correctly. I solved this by referring to the example agent and fixing my code step by step.

Another issue was with the LLM. Some models were either too slow or gave very generic answers. Because of this, I added a simple fixed response logic so that the agent still gives clear output even if the LLM doesn’t work properly.

I also faced some path and setup issues while running the agent from a different folder, which I fixed by correcting the file paths.

---

### What I learned that I didn't know before

I learned how to build an AI agent that actually connects to external tools instead of just giving answers.

I also understood that LLMs are not always reliable, especially when running locally, so combining them with simple logic makes the system more stable.

I got a better idea of how the SMILE methodology works and how it focuses on useful insights rather than just data.

Overall, this task helped me understand how different components like tools, AI models, and code come together to build something practical.