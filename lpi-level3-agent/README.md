# LPI Digital Twin Agent - Track A Level 3

## Overview
This is a robust Python AI Agent built for the Life-Atlas MCP server. It connects securely to the local MCP, extracts insights from multiple tools, and processes them through an LLM.

## Setup Instructions
1. Clone this repository.
2. Ensure you have the main `lpi-developer-kit` running locally (for the MCP server).
3. If using the Web UI, install requirements: `pip install flask requests`.
4. Run the web server: `python app.py`
5. Alternatively, run the CLI: `python agent.py "What is Reality Emulation?"`

## Features & Error Handling
- **MCP Compatibility:** Connects via `stdio` directly.
- **Fail-Safe Fallback:** If the local LLM (`qwen2.5:1.5b`) is unavailable, times out, or fails to connect, the agent gracefully intercepts the error, stops the crash, and instantly returns raw synthesis data.
- **Web UI:** Includes a beautiful Flask + Glassmorphism frontend interface.
- **A2A Support:** Includes an `agent.json` indicating agent routing discovery properties.
