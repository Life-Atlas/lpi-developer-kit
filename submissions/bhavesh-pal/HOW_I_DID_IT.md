# How I Did It - Level 2

## What I did, step by step

I cloned the project and opened it on my system. I ran `npm install` to install all dependencies, then used `npm run build` to compile the project. After that, I ran `npm run test-client` and verified that all 8 tools passed successfully.

For the LLM part, I installed Ollama and first tried running `llama3`, but it failed because my system did not have enough available memory. Then I switched to `gemma:2b`, which worked properly. I tested it with a simple prompt to confirm that the local model was running successfully.

I also explored the SMILE framework content to understand how the system organizes digital twin workflows and implementation steps.

## What problems I hit and how I solved them

The biggest issue I faced was while running the local LLM. The `llama3` model required more memory than my system had available, so it failed to start. I checked the error message, understood that it was a RAM limitation, and switched to a smaller Ollama model, `gemma:2b`.

Another issue was understanding how to structure the Level 2 submission in GitHub. I reviewed example submissions and organized my work into separate markdown files inside the `submissions` folder.

## What I learned that I didn't know before

I learned how to run a local LLM using Ollama and how model size affects whether it can run on limited hardware. I also learned how the SMILE methodology breaks down complex systems into practical phases, which makes implementation easier to understand.
