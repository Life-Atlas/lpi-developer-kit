Level 2 Submission: Track A (Agent Builders)

1. LPI Sandbox Test ResultsI successfully ran the test client, and all tools passed validation.
[PASS] query_knowledge({"query":"explainable AI"})
[PASS] get_case_studies({})
[PASS] get_case_studies({"query":"smart buildings"})
[PASS] get_insights({"scenario":"personal health digital twin","tier":"free"})
[PASS] get_methodology_step({"phase":"concurrent-engineering"})

=== Results ===
Passed: 8/8
Failed: 0/8

All tools working. Your LPI Sandbox is ready.





2. Local LLM Output (Ollama)Model used: qwen2.5:1.5b 
User: "What is an AI agent and how can it use tools?"
Response:An AI agent is an autonomous system that uses a Large Language Model (LLM) as its "brain" to perceive its environment, reason about tasks, and take actions to achieve specific goals. It uses tools through protocols like MCP (Model Context Protocol) to bridge the gap between static knowledge and real-world data, allowing it to perform actions like searching databases, writing files, or calling APIs.




4. How I Did It (Process)
Step 1: Forked the repository and cloned it to my local machine.
Step 2: Installed dependencies using npm install and compiled the project using npm run build.
Step 3: Verified the environment by running npm run test-client and confirmed all 8 tools passed.
Step 4: Set up Ollama locally and pulled the qwen2.5:1.5b model to verify local agent capabilities.


Bugs/Issues: Initialized the project on Windows using PowerShell as recommended to avoid pathing issues with the built files.
