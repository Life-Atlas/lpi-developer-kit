# How I Did It - Level 2

### What I did, step by step

I cloned the project and opened it in VS Code. I ran `npm install` to set up all dependencies, followed by `npm run build` to compile the project. After that, I ran `npm run test-client` to verify that everything was working, and it executed successfully.

For the LLM part, I installed Ollama and tried running `llama3` first, but it failed due to insufficient memory on my system. After that, I switched to `tinyllama`, which ran without issues. I tested it with a simple prompt to confirm that it was working properly.

I also went through the SMILE framework data out of curiosity to understand what the system is actually trying to model.

---

### What problems I hit and how I solved them

The main issue I faced was while running the LLM. The `llama3` model required more RAM than my system could handle, which caused it to fail. Initially, I wasn’t sure whether it was a setup issue or something else, but the error message made it clear that it was a memory limitation.

I resolved this by switching to a smaller model (`tinyllama`), which worked smoothly on my system.

---

### What I learned that I didn't know before

This task helped me understand how a project setup works end-to-end, from installing dependencies to building and testing it.

I also got my first experience running a local LLM. I learned that model size directly impacts whether it can run on a system, and that smaller models can still be useful when resources are limited.

I also learned about the SMILE methodology and how it focuses on understanding the “why” behind data instead of just collecting it.

Overall, it gave me a clearer idea of how local development environments and AI tools can be combined in practical workflows.