# How I Did It - Level 2

### What I did, step by step
First, I cloned my fork and ran `npm install` followed by `npm run build` to get the TypeScript environment set up. Then I ran `npm run test-client` to make sure all tests are passing and not throwing errors. After that setup the Ollama local model(`qwen2.5:1.5b`), and prompted it about the framework to generate the LLM output for my submission.

### What problems I hit and how I solved them
I did a mistake right at the beginning because I typed `node -version` instead of `node -v` or `--version` and briefly thought my Node installation was broken. After getting past that, the build ran smoothly. Later, I realized I needed to make sure the Ollama app was actively running in the background before trying to run the model in the terminal, otherwise it just hangs.

### What I learned that I didn't know before
In normal software projects, my brain usually goes straight to setting up the backend logic and figuring out API routes. Reading up on the SMILE framework made me realize that for digital twins, you have to think about the entire lifecycle and predictive simulation first. It was a good lesson that building AI agents isn't just about fetching data, but designing a system that can actually anticipate future scenarios over time.

# How I Did It - Level 3

### What I did, step by step

1. I decided not to use big libraries like LangChain. I just used normal Python because I actually wanted to see how the JSON messages were moving back and forth between my script and the Node server. Building it from scratch gave me way more control.

2. Instead of making a normal chatbot that just answers questions, I made a "Gap Analyzer". Basically, it takes a user's project idea and checks it against the SMILE framework to find things people usually forget—like safety hazards or weather problems. I thought that would be way more useful than a basic planner.

3. To connect Python to Node, I used the `subprocess` module. But instead of keeping the connection open the whole time, I made it stateless. Every time it needs a tool, it opens a connection, grabs the data, and immediately closes it. This made the script run way smoother without crashing.

4. Since I'm taking input straight from the terminal, I added a quick regex filter. It just cleans out weird characters so nobody can break the script with bad inputs or basic injection attacks.

5. I used a small local AI model (`qwen2.5:1.5b`), which means it can get confused easily. To fix this, I made a super strict prompt template. I literally forced it to start every sentence with the tool name it used (like `[Tool: query_knowledge]`) so it couldn't fake its sources. This will help it to reduce the hallucinations.

6. Finally, I set up the `agent.json` file. I actually added the skills and rules so other agents could find it and understand what it does.

### What problems I hit and how I solved them

The worst bug I had was a `BrokenPipeError`. At first, I tried keeping one long connection open between Python and Node. But the two programs kept getting out of sync and freezing my terminal. It took me forever to figure out. 

I fixed it by making it a "one-shot" connection instead. Now, it just calls the server, asks for what it needs, and hangs up right away. No more freezing.

The other big headache was the AI ignoring my formatting. It kept trying to be chatty or use bullet points, which would fail the explainability requirement. I ended up basically boxing it in. I gave it a strict "Required Output Format" in the prompt and forced the citations to be the very first word. Once I did that, it stopped messing up.

### What I learned that I didn't know before

I realized you really don't need a massive framework to build this. Building the connection myself taught me way more about how AI tools actually work under the hood than following a tutorial would have.

Lastly, running things locally is much better for privacy. Since everything runs right in my computer's memory, nothing goes out to the internet. It feels a lot safer and made me appreciate local AI a lot more.
