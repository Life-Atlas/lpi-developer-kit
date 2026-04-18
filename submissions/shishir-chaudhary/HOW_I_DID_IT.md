# How I Did It — Level 3

## What I did, step by step

1. **Development environment setup**:
   - I cloned the lpi-developer-kit repository that I forked earlier,
   - Then, I ran the `npm install` and `npm run build` command to build the TypeScript MCP server, followed by `npm run test-client`, to ensure that all 7 tools work.

2. **Learned about the LPI server implementation**:
   - Prior to writing the code, I analyzed the source code of the MCP server (`src/index.ts`, `src/tools/*.ts`), as well as the data files(`data/smile-framework.json`, `data/knowledge-base.json`, `data/case-studies.json`) to learn about what each tool outputs.

3. **Created the Question Routing Mechanism**: Rather than making fixed calls to the same set of tools in every case like the sample agent, I implemented a keyword-based classification mechanism that determines which 2–5 tools are suitable for the specific user query. For instance, a question regarding "healthcare digital twins" will trigger `get_case_studies` + `query_knowledge` + `get_insights`, whereas a question on "SMILE definition" will call `smile_overview` + `query_knowledge`.

4. **Implemented the MCP Connection Layer**: Implemented the `MCPConnection` class to manage the subprocess creation and destruction cycle, JSON-RPC handshake, request ID sequencing, and graceful termination of processes.

5. **Implemented provenance tracking**: Each tool result gets tagged as `[Source N]`. The LLM prompt instructs the model to cite these sources inline. After every answer, a source table shows exactly which tools were called, what arguments were used, and how much data came back.

6. **Integration with Ollama in case of failure**: The agent utilizes Ollama (qwen2.5:1.5b) for synthesizing answers from multiple sources. In the event Ollama does not function, the agent will show the structured tool output directly. 

7. **Development of an interactive CLI** : The agent can work either on a single question input (`python agent.py "question"`) basis or in interactive mode, supporting /help, /tools, and /quit commands.

---

## Problems I hit and how I solved them

-**MCP handshake time synchronization**: The server requires an `initialize` command and a `notifications/initialized` event to accept tool commands. My first mistake was overlooking the notification part and experiencing silent failures. Careful reading of the MCP specification and the client example resolved this issue.

- **Context window constraints**: The qwen2.5:1.5b model has limited context window capabilities. Sending all outputs without any truncation led to timeouts or incomplete responses. To address this problem, I trimmed down each source to 2000 characters and set the output limit to 1024 tokens for the model.

- **Accuracy of tool routing**: The initial classifier that I had used was overly broad because it would route a lot of tools for basic questions. This was fixed by fine-tuning the keywords and using a ranking scheme.

---

## What I learned

- **SMILE puts impact first and data last**: The typical development process begins with gathering data. With SMILE, you first define your intended outcome and work backwards - Outcome -> Action -> Insight -> Information -> Data. That's the opposite of the process I usually take.

- **MCP protocol turns out to be easier than expected**: JSON-RPC over stdio. No HTTP and no WebSocket; it's just stdin and stdout using a subprocess. Initialization is the most complex part here; after that, requests and responses.

- **Explainability as a design principle**: It isn't enough to merely add source citations. Rather, one needs to restructure their prompt to accommodate citations because the LLM must be provided with information sources. In line with SMILE, this demonstrates that explainability becomes easier if based on tangible information.

- **Ontology Factories come before AI Factories**: My takeaway from the knowledge base - you have to represent information structures before creating an AI reasoning system about it. This relates to phase 3 of SMILE - Collective Intelligence.