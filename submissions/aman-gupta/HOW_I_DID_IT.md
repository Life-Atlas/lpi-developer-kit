\# HOW I DID IT



For Level 2, I first installed Node.js because node and npm were missing on my laptop. After installing it, I checked the versions in PowerShell.



Then I cloned my forked GitHub repository to my laptop and opened the project folder. After that, I ran `npm install` to install all required packages.



Next, I used `npm run build` and then `npm run test-client`. All tests passed successfully, which confirmed that the LPI sandbox was working properly.



After completing the sandbox setup, I installed Ollama and downloaded the qwen2.5:1.5b model. I ran the model locally and asked it about the SMILE methodology.



\## Problems I Faced



At the beginning, node and npm were not installed. After installing Node.js, npm was still blocked in PowerShell because of script execution policy. I fixed it by updating the execution policy and then everything worked.



\## What I Learned



I learned how to set up a project from GitHub, run commands in PowerShell, test MCP tools, and use a local AI model on my laptop. I also learned that the SMILE methodology can be applied in many real-world use cases.

