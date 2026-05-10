# HOW I DID IT

## Steps I followed

1. Ran the LPI sandbox locally
2. Used the provided agent.py as a base
3. Installed Ollama and ran a local LLM
4. Executed the agent with a test query
5. Verified that multiple LPI tools were being called
6. Observed how the LLM combined the results

## Problems I faced

- PowerShell blocked npm scripts initially
- Ollama was not installed and caused connection errors
- Missing Python dependencies like requests

## How I solved them

- Changed execution policy in PowerShell
- Installed Ollama and ran the server
- Installed required Python packages

## What I learned

- How AI agents integrate multiple tools
- Importance of combining structured data with LLMs
- How explainability improves trust in AI systems
