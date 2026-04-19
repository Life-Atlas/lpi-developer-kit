# How I Did It - Level 2

### What I did, step by step

I forked the repository and cloned it locally, then opened it in VS Code. I ran npm install to set up all dependencies, followed by npm run build to compile the project. After that, I ran npm run test-client to verify everything was working and all 7 tools passed successfully.
For the LLM part, I installed Ollama and pulled the qwen2.5:5b model, which ran without any issues. I tested it with a simple prompt about digital twins to confirm it was responding correctly.
I also read through the SMILE framework output from the test client to understand what the system is actually modelling.
---

### What problems I hit and how I solved them

The main issue I faced was with model sizing. I initially tried a smaller variant but found the token output was too slow for practical use on my system. I resolved this by switching to qwen2.5:5b, which balanced RAM usage and response quality well and it ran smoothly without overwhelming my system resources.
---

### What I learned that I didn't know before

This task helped me understand how a project setup works end to end from installing dependencies to building, compiling, and testing a TypeScript-based MCP server.
It was also my first hands-on experience running a local LLM. I learned that model parameter size directly affects RAM consumption and inference speed, and that choosing the right model for your hardware matters as much as choosing the right model for the task.
I also got introduced to the SMILE methodology, which stood out to me because it emphasises understanding the why behind data not just collecting it, which aligns closely with how I think about building meaningful ML systems.
Overall, this gave me a much clearer picture of how local development environments and AI tooling can fit together in a real workflow.
