# HOW_I_DID_IT

## Overview
I built a Digital Twin Advisor Agent that helps users understand how digital twin systems can be implemented using the SMILE methodology.

## Steps I Followed

1. I cloned the LPI Developer Kit repository.

2. Installed dependencies and verified the sandbox:

npm install  
npm run build  
npm run test-client  

3. I created a simple AI agent that accepts a digital twin question from the user.

4. The agent queries three LPI tools:

- query_knowledge  
- get_case_studies  
- get_insights  

5. These tools return knowledge entries, case studies, and implementation insights.

6. The agent combines these outputs and generates a recommendation using the SMILE methodology.

## Challenges

Understanding how to structure the workflow between multiple LPI tools while keeping the agent explainable was the main challenge.

## Design Choices

Instead of building a generic chatbot, I focused on a Digital Twin Advisor use case.  
This allowed the agent to combine knowledge, case studies, and insights to generate practical recommendations.

## What I Would Do Differently

If I extended the project further I would:

- integrate directly with the MCP server  
- return structured JSON outputs  
- add automated tests
