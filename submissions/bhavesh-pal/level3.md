# Level 3 Submission - Bhavesh Pal

## Agent Repo
https://github.com/bhavesh4323/lpi-agent-bhavesh

## What my agent does
My agent takes a user question and uses LPI tools to generate answers.

## Tools used
- query_knowledge
- get_insights
## How to run
Start the LPI sandbox/server first.

Then run:
python agent.py "Explain digital twins in simple terms"
If your server is not on the default URL, run:
python agent.py "Explain digital twins in simple terms" --base-url http://localhost:3333
You can also set an environment variable:
export LPI_BASE_URL=http://localhost:3333
python agent.py "Explain digital twins in simple terms"

## Example

The agent:

Accepts a user question
Calls query_knowledge
Calls get_insights
Prints both results
Shows the sources used

Important truth: your agent cannot be “run by anyone” with zero setup if it depends on a local LPI server. What you can do is make it easy for anyone to run by clearly documenting:
- they must start the LPI sandbox
- how to install dependencies
- how to pass the server URL


## Install dependencies
`bash
pip install -r requirements.txt
run:
``bash
pip install -r requirements.txt
python agent.py

## How it works
1. Takes input
2. Calls tools
3. Combines results
4. Shows sources

## Example
Input: Explain digital twins

Output:
- knowledge result
- insights result
- sources shown

## Notes
The agent demonstrates explainable AI by clearly showing which tools were used.
