# Level 2 — Vineet Sharma

## What I did
I first forked and cloned the repository. then installed dependencies using npm install, I tried running the test client but faced issues because of being in the wrong folder. After correcting the directory, I ran npm run test-client and verified that all LPI tools were working

Then, I installed Ollama. I faced an issue where the command was not recognized, which I fixed by properly installing Ollama and restarting the terminal. After that, I ran the llama3 model locally and tested with prompts related to SMILE methodology.

## Problems I faced
The main issue I faced was running the test client from the wrong directory, which caused errors. I also had issues with Ollama not being recognized initially due to PATH issues.

## How I solved them
I re-cloned the repository and ensured I was in the correct folder. I installed Ollama properly and restarted the terminal, which solved the problem

## What I learned
I learned how to set up and interact with a local LLM using Ollama and how to connect to structured tools using the LPI sandbox. I also understood how systems like SMILE organize knowledge and tools in a modular way, which can be useful for building scalable AI agents.


# Level 3 — Vineet Sharma

## What I built
I built a Decision Tradeoff Agent that helps users to compare options and make better decisions. Instead of just giving advice, the agent asks the user what matters most and then provides a structured tradeoff analysis.

## How it works
The agent takes user input and calls two LPI tools: query_knowledge and get_insights. It combines the results and generates a response based on user priority.

## Problems I faced
Initially, I was unsure how to structure the decision logic and how to meaningfully combine outputs from different tools.

## How I solved them
Simplified the approach by focusing on a clear flow: input → tool calls → structured output. I ensured the agent uses at least two tools and provides understandable output.

I improved the agent by adding structured comparison and priority-based reasoning instead of just returning raw tool outputs. This helped make the agent more useful and closer to real decision-making.

## What I learned
Learned how to connect multiple tools to create a simple AI agent and how structured knowledge systems can help in decision-making.
