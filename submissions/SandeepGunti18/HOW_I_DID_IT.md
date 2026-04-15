# How I Did Level 2 — Track A

## Step-by-Step Process

1. I cloned the LPI developer kit and ran `npm install && npm run build`
2. I verified all 7 tools pass by running `npm run test-client`
3. I installed Ollama from ollama.com
4. I downloaded the qwen2.5:1.5b model using `ollama pull qwen2.5:1.5b`
5. I ran the example agent with a question about the SMILE methodology
6. The agent queried three LPI tools (smile_overview, query_knowledge, get_case_studies) and sent the results to the local LLM
7. I captured the LLM output showing how it synthesized the tool results into a coherent answer

## Problems I Hit and How I Solved Them

When I first tried to run `ollama serve`, I got a "bind" error saying the port was already in use. I realized Ollama was already running in the background from the installation, so I just skipped that step and proceeded directly to running the agent. This taught me that Ollama auto-starts on Windows.

The agent initially failed because I didn't have the `requests` library installed. I fixed this by running `pip install requests`, which gave the agent the HTTP capabilities it needed to communicate with the LPI sandbox.

## What I Learned

I learned that the MCP (Model Context Protocol) is a powerful standard for agents to discover and call tools reliably. The fact that I could write a simple query in English and the agent automatically figured out which tools to use was impressive. I also gained appreciation for how important it is to cite sources in AI — the agent explicitly showed which tool provided which information, making it explainable rather than a black box. Finally, I realized that running LLMs locally with Ollama is practical and fast, opening possibilities for building agents without cloud dependencies.
