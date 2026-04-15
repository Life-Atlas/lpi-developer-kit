# How I Did It - Level 2

### What I did, step by step
First, I cloned my fork and ran `npm install` followed by `npm run build` to get the TypeScript environment set up. Then I ran `npm run test-client` to make sure all tests are passing and not throwing errors. After that setup the Ollama local model(`qwen2.5:1.5b`), and prompted it about the framework to generate the LLM output for my submission.

### What problems I hit and how I solved them
I did a mistake right at the beginning because I typed `node -version` instead of `node -v` or `--version` and briefly thought my Node installation was broken. After getting past that, the build ran smoothly. Later, I realized I needed to make sure the Ollama app was actively running in the background before trying to run the model in the terminal, otherwise it just hangs.

### What I learned that I didn't know before
In normal software projects, my brain usually goes straight to setting up the backend logic and figuring out API routes. Reading up on the SMILE framework made me realize that for digital twins, you have to think about the entire lifecycle and predictive simulation first. It was a good lesson that building AI agents isn't just about fetching data, but designing a system that can actually anticipate future scenarios over time.