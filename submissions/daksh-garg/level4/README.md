# Secure Agent Mesh - Level 4 Submission

A secure agent-to-agent communication system implementing A2A protocol with MCP integration and comprehensive security hardening.

## What System Does
- **Agent A**: Client agent that handles user input and discovers Agent B
- **Agent B**: Server agent that analyzes problems using SMILE methodology via LPI tools
- **Security**: Comprehensive protection against injection, DoS, and data exfiltration
- **Communication**: Structured JSON-based agent-to-agent communication

## Architecture
```
User → Agent A (Client) → Agent B (Server) → LPI MCP Server → Ollama LLM
```

## How to Run

### Prerequisites
- Python 3.10+, Flask, requests
- Node.js 18+ (for LPI MCP server)
- Ollama with qwen2.5:1.5b model
- LPI developer kit built (`npm run build`)

### Step 1: Install Dependencies
```bash
pip install flask requests
```

### Step 2: Start Ollama
```bash
ollama serve
ollama pull qwen2.5:1.5b
```

### Step 3: Start Agent B (Server)
```bash
python agent_b.py
```
Expected: Server starts on http://localhost:8000

### Step 4: Start Agent A (Client)
```bash
python agent_a.py
```
Expected: Agent discovers Agent B and waits for user input

### Step 5: Use the System
```
Enter your problem: I feel distracted and unproductive
```

## Security Features
- **Prompt Injection Protection**: Pattern-based detection and blocking
- **Rate Limiting**: 10 requests per minute per client
- **Input Validation**: Length limits, character sanitization
- **Output Sanitization**: Field whitelisting, data leakage prevention
- **Timeout Protection**: Prevents resource exhaustion

## A2A Protocol Implementation
- Agent discovery via `.well-known/agent.json`
- Structured JSON communication
- Capability description and validation
- Security feature disclosure

## Files
- `agent_a.py` - Client agent with security validation
- `agent_b.py` - Server agent with MCP integration
- `.well-known/agent.json` - A2A agent card
- `threat_model.md` - Attack surface and threat analysis
- `security_audit.md` - Security testing results
- `demo.md` - Working demonstration transcript

This system demonstrates production-ready agent-to-agent communication with comprehensive security controls and real-world applicability.
