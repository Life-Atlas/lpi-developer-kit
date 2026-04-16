At level 3, I build an AI agent using Python to communicate with the LPI (Learning Pathways Interface) Sandbox and provide answers through the use of a local SLM (Small Language Model) that is a locally-based Language Learning Model.

My first step was to start the LPI server using command-line commands (e.g., cd Notebooks). From there, I created this server process using the subprocess module so that the LPI server could talk to my agent via standard input/output. I also wrote a JSON-RPC function so that I could call the various LPI tools and get their results.

There are three tools that the agent will call for each end-user question input:

1. The smile_overview tool provides a brief overview of how the LPI tools generate answers to end-user questions.
2. The query_knowledge tool returns specific details regarding the input query itself.
3. The get_case_studies tool returns examples from the actual world of healthcare based on the other two tools’ outputs.

After I received the responses back from the tools, I put together the prompts in a structured format. Additionally, I cut down the size of each tool’s response to provide to the LLM in my request for a final LLM-generated answer, in order to conserve as much processing resources as possible.

Finally, I make an API call to a local LLM (Ollama using the phi model) with the data returned from all three tools as structured prompts and generated and formatted the final response with the tools used to obtain the generated responses.

Once the agent has completed execution, I do ensure that I kill off and terminate the LPI server process properly.