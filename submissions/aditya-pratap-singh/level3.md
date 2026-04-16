## Submission Level
Level: level-3

## Project
Digital Twin Advisor Agent

## Repository
https://github.com/psinghaditya/digital-twin-advisor-agent-Adi

## What I Built
This agent accepts a digital twin question and queries LPI knowledge tools to provide implementation guidance.

The agent retrieves knowledge, case studies, and insights about digital twin systems and processes the information using the SMILE methodology to produce practical recommendations.

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

## LPI Tools Used

The agent queries the LPI knowledge base using the following tools:

- query_knowledge
- get_case_studies
- get_insights

These tools retrieve knowledge entries, real-world case studies, and implementation insights for digital twin systems.

## Explainability

The agent clearly shows which LPI tools were used when generating the response.  
This makes the reasoning process transparent so the user can trace how the recommendation was produced.

## Error Handling

The Digital Twin Advisor Agent validates user input before processing a query.

If the user provides empty or invalid input, the agent returns a helpful message instead of failing.

Example:

User Input: (empty question)

Agent Response:
"Please provide a valid digital twin question."



### Update
Architecture diagram and documentation improved.



