Level 3 Submission - Gunti Sandeep

Track
Track A: Agent Builders

Project Name
AI Career & University Decision Agent

Repository Link
https://github.com/SandeepGunti18/lifeatlas-level3-agent

Overview

This project is an AI-driven decision agent designed to assist students in selecting optimal universities and academic paths based on personalized inputs.

The agent processes user inputs such as:

Interests
Preferred course
Budget
Study preference (Domestic / International)

It dynamically generates structured and explainable recommendations by leveraging external decision tools and predefined criteria.

Agent Workflow
Input Processing – Extracts user intent and constraints
Tool Selection – Determines which tools to invoke
Data Retrieval – Fetches relevant academic and financial insights
Decision Engine – Evaluates options based on multiple criteria
Output Generation – Produces ranked and explainable recommendations
LPI Tools Used

1. query_knowledge

Retrieves evaluation criteria such as:
Curriculum quality
Internship opportunities
Placement outcomes
University rankings
ROI

2. get_insights

Generates personalized recommendations based on:
Budget constraints
Geographic preference
Career alignment
Example Use Case

Input:

Interest: Software Development
Course: BTech CSE
Budget: ₹30,00,000
Preference: International

Output:

Recommended Countries: USA, UK, Singapore
Suggested Direction:
Focus on universities with strong CS placement records
Consider mid-tier universities for better ROI within budget
Next Steps:
Shortlist universities
Explore scholarships
Apply before deadlines
Explainability

The agent ensures transparency by explicitly showing:

Which tools were used (query_knowledge, get_insights)
How each factor (budget, interest, location) influenced the decision
Tech Stack
JavaScript
Node.js
Status

Working prototype successfully implemented and deployed on GitHub.
