## Submission Level
Level: level-3

## Project
Digital Twin Advisor Agent

## Repository
https://github.com/psinghaditya/digital-twin-advisor-agent-Adi

## What I Built
I built a Digital Twin Advisor Agent that helps users plan digital twin implementations using the SMILE methodology provided by the LPI sandbox.

The agent accepts a user question related to digital twins and retrieves relevant knowledge from the LPI knowledge base. It combines knowledge entries, case studies, and implementation insights to generate practical recommendations.

The goal was to demonstrate how an AI agent can query structured knowledge tools and produce explainable recommendations.

---

## Setup Instructions

To run the Digital Twin Advisor Agent:

1. Clone the repository

git clone https://github.com/psinghaditya/digital-twin-advisor-agent-Adi

2. Navigate into the project folder

cd digital-twin-advisor-agent-Adi

3. Install dependencies

npm install

4. Run the agent

npm start

---

## LPI Tools Used

The agent queries the LPI knowledge base using the following tools:

- query_knowledge  
- get_case_studies  
- get_insights  

These tools provide:

• conceptual knowledge about digital twins  
• real-world case studies  
• scenario-based implementation insights  

The agent combines the outputs from these tools to generate recommendations using the SMILE methodology.

---

## Explainability

The agent explicitly shows which LPI tools were used when generating the response.

This allows the user to trace how the final recommendation was produced and which knowledge sources were used.

Workflow:

User Question  
→ Agent  
→ LPI Tool Calls  
→ Processing using SMILE methodology  
→ Recommendation Output

---

## Error Handling

The Digital Twin Advisor Agent validates user input before processing a query.

If the user provides empty or invalid input, the agent returns a helpful message instead of failing.

Example:

User Input: (empty question)

Agent Response:

"Please provide a valid digital twin question."

---

## Design Choices

One design choice I made was focusing on a Digital Twin Advisor use case that combines knowledge, case studies, and insights into a single workflow.

This allowed the agent to demonstrate explainability and multi-source reasoning instead of only returning static answers.

---

## What I Would Improve Next Time

If I extended this project further, I would:

• integrate the agent directly with the MCP server for real-time LPI tool calls  
• structure outputs as JSON responses  
• add automated tests  
• build a simple web interface for interacting with the agent

---

## Additional Documentation

The development process and challenges are documented in:

HOW_I_DID_IT.md
