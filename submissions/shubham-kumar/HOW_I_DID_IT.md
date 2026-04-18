# How I Did It - Level 2

### What I did, step by step

I cloned the project and opened it in VS Code. I ran `npm install` to set up all dependencies, then I ran `npm run build` to compile the project. After that, I ran `npm run test-client` to check that everything was working, and it executed successfully.

For the LLM part, I installed Ollama . Then, I switched model to `qwen2.5:1.5b`, which ran without any problems. I tested it with a simple prompt to make sure it was working properly.

I also looked through the SMILE framework data just to understand what the system is actually trying to model.
---

### What problems I hit and how I solved them

The main issue I faced was while running the LLM. The `qwen2.5:1.5b` model required less RAM than my system could handle, which caused it to slow output of tokens.

I resolved this by understanding the flow of how parameters can impact on ram and then boosting it to `qwen3.5:35b`

---

### What I learned that I didn't know before

This task helped me understand how a project setup works from start to finish, from installing dependencies to building and testing it.

I also had my first experience running a local LLM. I learned that the size of the model affects whether it can run on a system. Smaller models can still be useful when resources are limited.

I also learned about the SMILE methodology, which emphasizes understanding the “why” behind data instead of just gathering it.

Overall, it gave me a clearer idea of how local development environments and AI tools can work together in practical workflows.