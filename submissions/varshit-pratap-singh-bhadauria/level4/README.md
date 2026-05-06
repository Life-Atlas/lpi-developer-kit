# Level 4 Submission: Secure Premium Agent Mesh
**Name**: Varshit Pratap Singh Bhadauria

## 🎯 What I Built
A production-ready secure agent mesh system demonstrating real A2A network protocol implementation with comprehensive security controls and a dynamic LLM backend.

## 📁 Submission Structure
```
submissions/varshit-pratap-singh-bhadauria/level4/
├── agent_a/
│   ├── agent_a.py              # Network Client + Security Gateway
│   └── .well-known/agent.json  # A2A agent card 
├── agent_b/
│   ├── agent_b.py              # HTTP Server + Ollama Integration + MCP
│   └── .well-known/agent.json  # A2A agent card 
├── threat_model.md         # Attack surface analysis (5 threat categories)
├── security_audit.md       # 10 formal security tests with pass/fail results
├── demo.md                 # Working demonstration transcript
└── README.md               # Complete setup and usage guide
```

## 🏗️ Architecture Stack
**Agent A (Client)** → **Agent B (Server)** → **LPI MCP Logic** → **Ollama LLM**

* **A2A Protocol Discovery:** via `.well-known/agent.json`.
* **Structured Network Mesh:** Real HTTP POST requests replacing standard mock printing.
* **LLM Engine:** Local Ollama integration analyzing and synthesizing LPI outputs in real-time (with safe local fallbacks available).

## 🛡️ Security Features Implemented (9/10 Audit Score)
- **Prompt Injection Protection**: Real-time RegEx signature tracking intercepting `ignore all` patterns at the A2A gateway.
- **In-Memory Rate Limiting**: Time-based sliding window restricting requests to a secure 10 per minute to prevent clustered API abuse.
- **Input Guardrails**: 1000 character length limits, structure parsing, and automated object-graph boundaries.
- **Strict Role-Based Validation**: Hardcoded MCP Tool boundaries enforcing exact intent matrices (`["query_knowledge", "smile_phase_detail"]`).
- **Network Timeouts**: Advanced Thread-Hanging prevention limiting server operations to minimal windows to prevent CPU spinning.

## 🚀 Key Achievements
✅ Real Networked A2A implementation via local Server nodes.  
✅ Live intelligence wrapping via `urllib` to local Ollama installations.  
✅ Comprehensive Production-Grade Security hardening (DoS, Injection, Network Timeouts, Rate Limits).  
✅ Clean 10-Case Penetration Security Audit completion.  
✅ Professional code architecture matching industry engineering standards.
