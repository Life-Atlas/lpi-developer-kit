# Level 3 Submission - Bhavesh Pal

## Agent Repository
https://github.com/bhavesh4323/lpi-agent-bhavesh

## What My Agent Does
My agent takes a user question and uses LPI tools to generate comprehensive answers by combining knowledge from multiple sources. It demonstrates explainable AI by showing which tools were used to generate the answer.

## Tools Used
- `query_knowledge` - Searches the LPI knowledge base for relevant information
- `get_insights` - Provides scenario-based recommendations and insights

## How to Run

### Prerequisites
Start the LPI sandbox/server first:
```bash
npm start
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Agent

**Basic usage (with default server URL):**
```bash
python agent.py "Explain digital twins in simple terms"
```

**With custom server URL:**
```bash
python agent.py "Explain digital twins in simple terms" --base-url http://localhost:3333
```

**Using environment variable:**
```bash
export LPI_BASE_URL=http://localhost:3333
python agent.py "Explain digital twins in simple terms"
```

## How It Works

1. **Accepts user input** - Takes a natural language question from the user
2. **Queries knowledge base** - Calls `query_knowledge` to retrieve relevant information from LPI knowledge base
3. **Gets insights** - Calls `get_insights` to obtain scenario-based recommendations
4. **Combines results** - Merges both responses into a structured, comprehensive answer
5. **Shows sources** - Displays which tools were used (explainability feature)

## Example Run

**Input:**
```
Explain digital twins in simple terms
```

**Output:**
```
=== LPI Agent ===
User Query: Explain digital twins in simple terms

[1] Querying Knowledge Base...
Found knowledge about: Digital twin definitions, use cases, benefits

[2] Getting Insights...
Insights for the scenario: Implementation steps, industry applications, best practices

=== Combined Answer ===
Digital twins are virtual digital representations of physical objects, systems, or processes...
[Full comprehensive answer combining both tools]

=== Tools Used ===
✓ query_knowledge - Retrieved foundational knowledge
✓ get_insights - Provided scenario-based recommendations

=== Sources ===
- LPI Knowledge Base
- Digital Twin Case Studies
```

## Requirements Checklist

- [x] Accepts user input
- [x] Uses at least 2 LPI tools (query_knowledge, get_insights)
- [x] Processes and combines results into cohesive answer
- [x] Shows sources (explainable AI)
- [x] Separate GitHub repository created
- [x] Clear documentation and examples
- [x] Easy setup and installation instructions

## Why This Agent?

This agent demonstrates:
- **Practical AI Application**: Using LPI tools to build a working AI system
- **Explainability**: Always showing which tools and sources were used
- **Real-world Usability**: Can answer questions about digital twins, SMILE methodology, and LPI concepts
- **Scalability**: Easy to extend with more tools and use cases

## Notes

The agent demonstrates how LPI tools can be combined together to build a simple yet powerful explainable AI system. It serves as a foundation for more complex multi-agent systems.

## Installation Troubleshooting

- Ensure Python 3.8+ is installed
- Verify the LPI server is running on the correct port
- Check that all dependencies in requirements.txt are installed
- Use `--base-url` flag if server runs on non-default port

Signed-off-by: Bhavesh Pal <bhaveshpal2672004@gmail.com>
