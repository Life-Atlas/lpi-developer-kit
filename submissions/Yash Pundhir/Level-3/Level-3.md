# Level 3 Submission — Yash Pundhir

**My Agent Repository -** https://github.com/Yash-04-create/lpi-developer-kit

**Agent Capabilities :-** 
I built a Python-based LPI agent that interacts with the LPI Sandbox using a local Node.js server via subprocess.Popen. The agent takes a user query, calls multiple LPI tools, and generates a final answer using a local LLM (Ollama – phi model).

**Tools Used :-**
smile_overview → methodology basics
query_knowledge → detailed explanations
get_case_studies → real-world examples
get_insights → contextual recommendations

**Explainability :-** 
The agent combines outputs from multiple tools into a structured prompt and ensures responses are based only on retrieved data. It also clearly shows which tools were used, improving transparency.

**Workflow :-**
Start LPI server
Call tools using JSON-RPC
Combine results into prompt
Send to LLM
Display final answer