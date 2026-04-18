
# Level 3 — Vineet Sharma

## What I built
I built a Decision Tradeoff Agent that helps users to compare options and make better decisions. Instead of just giving advice, the agent asks the user what matters most and then provides a structured tradeoff analysis.

## How it works
The agent takes user input and calls two LPI tools: query_knowledge and get_insights. It combines the results and generates a response based on user priority.

## Problems I faced
Initially, I was unsure how to structure the decision logic and how to meaningfully combine outputs from different tools.

## How I solved them
Simplified the approach by focusing on a clear flow: input → tool calls → structured output. I ensured the agent uses at least two tools and provides understandable output.

I improved the agent by adding structured comparison and priority-based reasoning instead of just returning raw tool outputs. This helped make the agent more useful and closer to real decision-making.

## What I learned
Learned how to connect multiple tools to create a simple AI agent and how structured knowledge systems can help in decision-making.