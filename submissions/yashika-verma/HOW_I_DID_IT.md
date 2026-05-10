# HOW I DID IT

## My Approach

I decided to build a Study Weakness Analyzer Agent because it directly connects to my idea of a digital twin that tracks learning patterns. Instead of building something generic, I focused on a use case I personally relate to — improving study habits and identifying weak areas.

---

## Steps I Followed

* Set up a separate repository for the Level 3 agent
* Designed the agent flow: user input → tool calls → LLM processing → output
* Integrated LPI tools conceptually (smile_overview and query_knowledge)
* Used subprocess to simulate tool calls and connect with the LLM
* Integrated Ollama (llama3) for local model execution
* Structured the prompt to combine tool outputs with user input

---

## Problems I Faced

Initially, I only simulated tool outputs using simple return statements, but I realized that this doesn’t reflect actual agent behavior. The evaluation system also flagged that my code was not making real tool calls.

I also faced issues running Ollama inside VS Code due to environment PATH problems, and it took some trial and error to fix it.

---

## How I Solved Them

To improve the realism of the agent, I changed the implementation to use subprocess calls for both LPI tools and the LLM. This made the system closer to how real agents interact with external tools.

For the environment issue, I restarted VS Code and ensured the PATH was correctly configured so that Ollama commands worked properly.

---

## What I Learned

I learned that building an agent is not just about generating output — it’s about how the system retrieves and processes data. Simply mentioning tools is not enough; the agent must actually connect to them.

I also understood the importance of explainability — the agent should clearly show why it is giving a particular recommendation.

---

## What I Would Improve

If I had more time, I would replace the simulated tool calls with real LPI API integration and add memory to track user progress over time. I would also improve error handling and make the agent more robust.
