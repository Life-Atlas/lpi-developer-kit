# HOW_I_DID_IT — Level 3 (Rahul Bijarnia)

## What I did

I started by understanding the requirement of building an AI agent that connects to LPI tools.

Then I cloned the repository and explored the provided agent.py to understand how tool calling works.

I set up the environment and installed required dependencies. After that, I installed Ollama to run a local LLM.

I modified the agent so that it calls multiple tools like smile_overview, query_knowledge, and get_case_studies for a single query.

Then I combined all the tool outputs and passed them to the LLM to generate a final answer.

Finally, I tested the agent with different queries and verified that it was using multiple tools and generating explainable outputs.

## Problems I faced

Initially, PowerShell blocked npm scripts, which caused issues in setup.

I also faced errors because Ollama was not installed, so the agent could not connect to any model.

There were also missing Python dependencies like requests.

## How I solved them

I fixed the PowerShell issue by changing execution policy.

Then I installed Ollama properly and made sure the server was running before executing the agent.

I installed required Python packages using pip.

## What I learned

I learned how AI agents work by combining multiple tools instead of relying only on a single model.

I also understood how important it is to provide explainable outputs using structured data.

This was my first time building an agent that actually integrates tools and LLM together.
