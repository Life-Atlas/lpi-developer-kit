# LPI Smart Agent

A simple intelligent agent that processes user queries and dynamically selects relevant LPI tools to generate a structured response.

## How It Works

- `how` / `implement` -> `get_methodology_step` + `get_insights`
- `example` / `case` -> `get_case_studies`
- `what` / `explain` / `overview` -> `smile_overview`
- `get_insights` is always included

## Features

- Dynamic tool selection based on query intent
- Multi-tool orchestration
- Structured JSON output

## Example

Input: How to implement digital twin with examples?

Tools used:
- get_methodology_step
- get_case_studies
- get_insights

## Insights

Tool-based architectures are more reliable than raw LLM prompting for domain-specific tasks.
