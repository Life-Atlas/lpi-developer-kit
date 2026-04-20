# WHAT I DID
First I read and understood the requirements for Level 3 which were:
- Collect user input
- Call atleast 2 LPI(LifeAtlas Platform Interface) tools
- Process the output
- Cite the sources used
  
Then the examples folder of agent.py was referred to understood how MCP(Model Context Protocol) is connected.
Through this it was decided that:
- Agent will be in Python
- Use Node wrapper to call the LPI tools
- Python to Node call through subprocess
  
The architecture was as follows:
- Node wrapper (lpi-wrapper.js)
- MCP server
- query_knowledge + get_case_studies
- JSON response
- Python will parse and print clean output

The workflow:
- Input taken in agent.py
- Question passed to Node wrapper
- Wrapper called 2 tools
- Returned JSON
- Python extracted text from nested JSON
- Output printed in sections
  -- User Question
  -- Knowledge Inisghts
  -- Case Studies
  -- Sources Used
---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PROBLEMS I FACED
1. Module not found  
   The path for Node wrapper was wrong and it was not able to find the file.
2. queryKnowledge is not a function
   Tried importing the function directly but realized that MCP tools dont expose like direct functions.
3. JSONDecodeError in Python
   Node was printing some extra logs in stdout. Python was crashing while executing json.loads. This was a cross language issue.
4. Encoding issue :
   Weird symbols in Powershell like â€” and â†’ which was a UTF-8 encoding issue.
5. Git untracked files :
   Files were in local but were not getting pushed , using git status found that they were untracked.
   ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SOLUTIONS TO THE ABOVE PROBLEMS
1. Module not found :
   Ensured file in same directory and ran Node through the correct path.
2. queryKnowledge is not a function :
   Learned how to call tool through MCP client and not through direct function and understood correct SDK usage.
3. JSONDecodeError in Python :
   Ensured that wrapper prints JSON in stdout only and errors redirected to stderr.
4. Encoding issue :
   Ran chcp 65001 in powershell which enabled UTF-8.
5. Git untracked files :
   git add agent.py lpi-wrapper.js
   git commit
   git push
   Files appeared in remote repository.
---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# WHAT I LEARNED
This was my first time building an AI agent and understood that AI agent is not just LLM's or GPT's or chatbots but rather it is a system which takes user input,calls tools, structures response,processes it and gives an explainable output. Also explainable AI is not just the model explaining but the user being aware of what tools are being used and from what data the answer has been framed.
Discovered for the first time that AI model doesnt call a function directly but rather sends a structured request through protocol. Used Python and Node together first time and understood JSON structure.
Integrating this kind of architecture in healthcare will engage user trust while also ensuring that the responses received are cited and valid. 
