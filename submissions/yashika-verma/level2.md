# Level 2 Submission — Yashika Verma

## ✅ LPI Sandbox Test Output

I successfully ran the LPI sandbox locally using the provided setup instructions.

Steps performed:
- Cloned my forked repository
- Installed dependencies using `npm install`
- Built the project using `npm run build`
- Ran the test client using `npm run test-client`

Result:
All 7 tools passed successfully, confirming that the LPI environment is working correctly.


---

## 🤖 Local LLM Execution (Ollama)

I installed and ran a local LLM using Ollama.

Steps:
- Installed Ollama on Windows
- Resolved PATH issue by restarting VS Code
- Ran the model using:
  ```bash
  ollama run llama3

Explain APIs in simple terms with an example

Output:
The model successfully explained APIs using a real-world analogy (restaurant ordering system), showing that it can generate meaningful responses locally without relying on cloud APIs.

🧠 What Surprised Me (SMILE Reflection)

I was surprised by how structured and modular the LPI tools are, making it easy to understand how different components interact. The SMILE approach made me realize that even simple tools can be combined to build more complex systems. I also didn’t expect a local LLM to run this smoothly and produce useful responses without needing any external API.

📌 Key Learnings
How to set up and run a local development environment using Node.js
How structured tool-based systems like LPI enable modular AI workflows
How to run and interact with a local LLM using Ollama
Importance of environment setup (PATH issues, terminal restarts, etc.)
🚀 Summary

This level helped me understand how:

LPI tools work together in a sandbox environment
Local LLMs can be integrated into workflows
Proper setup and debugging are critical for development

The experience gave me a strong foundation to build an AI agent in Level 3.