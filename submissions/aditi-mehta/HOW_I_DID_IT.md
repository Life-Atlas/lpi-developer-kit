# How I Did It - Level 2

### What I did, step by step
First, I cloned my fork and ran `npm install` followed by `npm run build` to get the TypeScript environment set up. Then I ran `npm run test-client` to make sure all tests are passing and not throwing errors. After that setup the Ollama local model(`qwen2.5:1.5b`), and prompted it about the framework to generate the LLM output for my submission.

### What problems I hit and how I solved them
I did a mistake right at the beginning because I typed `node -version` instead of `node -v` or `--version` and briefly thought my Node installation was broken. After getting past that, the build ran smoothly. Later, I realized I needed to make sure the Ollama app was actively running in the background before trying to run the model in the terminal, otherwise it just hangs.

### What I learned that I didn't know before
In normal software projects, my brain usually goes straight to setting up the backend logic and figuring out API routes. Reading up on the SMILE framework made me realize that for digital twins, you have to think about the entire lifecycle and predictive simulation first. It was a good lesson that building AI agents isn't just about fetching data, but designing a system that can actually anticipate future scenarios over time.


# How I Did It - Level 3

### What I did, step by step

1. I decided to skip LangChain and all those big libraries and just wrote this in raw Python. I wanted to see how the messages actually move between the script and the MCP server without a framework hiding everything.

2. Connecting to the server: I used subprocess to launch the Node server and kept the connection open. It basically lets my Python script talk directly to the Node backend.

3. Cleaning the input: I added a regex filter at the start. It just sanitizes the user's input from unwanted characters so no one can try to break the logic or run a terminal exploit.

4. Getting the data: My script sends a request to the smile_overview and get_insights tools, grabs the raw data they send back, and stores it as a string.

5. The AI part: I took that string and pushed it into a local Ollama model (qwen2.5:1.5b). I told the model it has to be a "citation engine," meaning it’s not allowed to give an answer without saying exactly which tool the info came from.

6. Agent Card: I created the agent.json file so the agent is officially "discoverable" according to the A2A rules.

### What problems I hit and how I solved them

I spent way too much time trying to figure out why the script kept hanging. It would send a request and then just freeze.

It turns out the Node server won't process a message unless it sees a newline character (\n) at the very end to signal the end of the JSON block. Once I added that and forced the buffer to flush, it worked instantly. I also had to get really strict with the LLM prompt because it kept trying to summarize everything without citing the tools, which would have failed the "Explainable AI" requirement.

### What I learned that I didn't know before

I’m used to using web APIs (REST) where everything happens over the internet, so I never really had to think about how two programs talk to each other on the same machine. This project taught me about stdio pipes, which is basically a direct line between my Python script and the Node server.

I learned the hard way that programs are very literal—if you don't send a "newline" character (\n) at the end of a message, the other program thinks you're still typing and just waits forever. Solving that "hanging" bug taught me a lot about how to manage data streams and how to "flush" a message to make sure it actually moves from one program to the other.

It made me realize that for local tools, you don't need a website or a server. Piping data directly is way faster and more secure because the info never even leaves your computer's memory.
