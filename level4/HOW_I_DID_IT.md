# HOW I DID IT - Level 4

## Approach
For Level 4, I built a simple multi-agent system where two agents communicate with each other. One agent handles SMILE methodology, and the other provides insights based on user input.

## Step-by-Step Implementation
1. First, I completed Level 3 and understood how LPI tools work.
2. Then I created a new folder called level4 in my repo.
3. I built Agent A to call the smile_overview tool.
4. I built Agent B to call the get_insights tool.
5. I created a main.py file where both agents are called.
6. I combined outputs from both agents to generate a final response.
7. I added JSON agent cards to describe each agent’s capability.

## Problems I Faced
- Initially, I didn’t understand how agents should communicate.
- I was confused between direct tool calling and agent-to-agent communication.
- I also faced issues handling errors when input was empty.

## How I Solved Them
- I separated responsibilities between two agents.
- I used structured JSON to pass data between agents.
- I added try-except blocks to prevent crashes.

## What I Learned
- Difference between single-agent and multi-agent systems
- Importance of structured data communication
- How LPI tools can be used in real workflows
- Basic security concepts like input validation

## What I Would Do Differently
- I would design a better communication protocol between agents
- I would add more security features like input filtering
- I would improve the final response using better reasoning logic
