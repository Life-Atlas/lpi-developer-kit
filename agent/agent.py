#!/usr/bin/env python3
"""
SMILE Digital Twin Advisor — Level 3 Agent Submission
Author: Shishir Chaudhary (@Shishir-DS28)

An intelligent AI agent that connects to the LPI MCP server, dynamically
selects relevant tools based on user questions, synthesizes results through
a local LLM (Ollama), and returns explainable answers with full provenance.

Architecture:
  User Question → Question Router → Dynamic Tool Selection (2-5 tools)
  → MCP Server Queries → Provenance-Tagged Context → LLM Synthesis
  → Structured Answer with Inline Citations + Source Table

Requirements:
  - Node.js 18+ (for the LPI MCP server)
  - npm run build (compile the LPI server first)
  - Ollama running locally: ollama serve
  - A pulled model: ollama pull qwen2.5:1.5b
  - Python 3.10+
  - requests: pip install requests

Usage:
  cd lpi-developer-kit
  npm run build
  python agent/agent.py                           # Interactive mode
  python agent/agent.py "Your question here"      # Single question mode
"""

import json
import subprocess
import sys
import os
import time
import re

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── Configuration ───────────────────────────────────────────────────────────
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LPI_SERVER_CMD = ["node", os.path.join(REPO_ROOT, "dist", "src", "index.js")]
LPI_SERVER_CWD = REPO_ROOT

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

VERSION = "1.0.0"
AGENT_NAME = "SMILE Digital Twin Advisor"


# ─── Question Routing ───────────────────────────────────────────────────────

# Keywords mapped to tool selection strategies
ROUTE_PATTERNS = {
    "methodology": {
        "keywords": ["smile", "methodology", "phases", "phase", "framework", "overview",
                     "principle", "philosophy", "what is smile", "explain smile"],
        "tools": [
            ("smile_overview", {}),
        ],
        "dynamic": True,  # Will add phase-specific tools if a phase is mentioned
    },
    "phase_detail": {
        "keywords": ["reality emulation", "concurrent engineering", "collective intelligence",
                     "contextual intelligence", "continuous intelligence", "perpetual wisdom",
                     "phase 1", "phase 2", "phase 3", "phase 4", "phase 5", "phase 6",
                     "mvt", "minimal viable twin", "reality canvas", "ontology factory"],
        "tools": [],  # Dynamically determined based on which phase is mentioned
        "dynamic": True,
    },
    "industry": {
        "keywords": ["case study", "case studies", "industry", "healthcare", "manufacturing",
                     "energy", "maritime", "smart building", "agriculture", "hospital",
                     "example", "real world", "implementation example", "use case"],
        "tools": [
            ("get_case_studies", {}),
        ],
        "dynamic": True,
    },
    "howto": {
        "keywords": ["how to", "how do i", "implement", "start", "begin", "step by step",
                     "guide", "practical", "getting started", "build", "create", "deploy"],
        "tools": [],
        "dynamic": True,
    },
    "knowledge": {
        "keywords": ["knowledge", "interoperability", "ontology", "edge", "security",
                     "ai journey", "sensor", "data", "architecture", "standard",
                     "explainable", "digital twin"],
        "tools": [],
        "dynamic": True,
    },
}

PHASE_MAP = {
    "reality emulation": "reality-emulation",
    "phase 1": "reality-emulation",
    "concurrent engineering": "concurrent-engineering",
    "phase 2": "concurrent-engineering",
    "collective intelligence": "collective-intelligence",
    "phase 3": "collective-intelligence",
    "contextual intelligence": "contextual-intelligence",
    "phase 4": "contextual-intelligence",
    "continuous intelligence": "continuous-intelligence",
    "phase 5": "continuous-intelligence",
    "perpetual wisdom": "perpetual-wisdom",
    "phase 6": "perpetual-wisdom",
}


def classify_question(question: str) -> list:
    """
    Analyze the user's question and return a list of (tool_name, arguments) tuples.
    Uses keyword matching to determine which LPI tools are most relevant.
    Always returns at least 2 tools (requirement).
    """
    q_lower = question.lower().strip()
    selected_tools = []
    matched_routes = set()

    # Check each route pattern
    for route_name, route_config in ROUTE_PATTERNS.items():
        for keyword in route_config["keywords"]:
            if keyword in q_lower:
                matched_routes.add(route_name)
                break

    # If no specific route matched, default to broad search
    if not matched_routes:
        matched_routes = {"methodology", "knowledge"}

    # Build tool list based on matched routes
    for route in matched_routes:
        config = ROUTE_PATTERNS[route]
        for tool in config["tools"]:
            if tool not in selected_tools:
                selected_tools.append(tool)

    # Add phase-specific tools if a phase is mentioned
    for phase_keyword, phase_id in PHASE_MAP.items():
        if phase_keyword in q_lower:
            phase_tool = ("smile_phase_detail", {"phase": phase_id})
            if phase_tool not in selected_tools:
                selected_tools.append(phase_tool)
            step_tool = ("get_methodology_step", {"phase": phase_id})
            if step_tool not in selected_tools:
                selected_tools.append(step_tool)

    # Add query_knowledge for most questions (uses user's question as search)
    knowledge_tool = ("query_knowledge", {"query": question[:100]})
    if knowledge_tool not in selected_tools:
        selected_tools.append(knowledge_tool)

    # Add get_insights for how-to and implementation questions
    if "howto" in matched_routes or "industry" in matched_routes:
        insight_tool = ("get_insights", {"scenario": question[:200]})
        if insight_tool not in selected_tools:
            selected_tools.append(insight_tool)

    # Add case studies for industry questions
    if "industry" in matched_routes:
        # Try to extract industry from question for targeted search
        industries = ["healthcare", "manufacturing", "energy", "maritime",
                      "smart building", "agriculture", "hospital", "horse"]
        for ind in industries:
            if ind in q_lower:
                cs_tool = ("get_case_studies", {"query": ind})
                # Replace the generic get_case_studies if present
                selected_tools = [t for t in selected_tools
                                  if t[0] != "get_case_studies"]
                selected_tools.append(cs_tool)
                break

    # Ensure we always have at least 2 tools (Level 3 requirement)
    if len(selected_tools) < 2:
        fallbacks = [
            ("smile_overview", {}),
            ("query_knowledge", {"query": question[:100]}),
            ("list_topics", {}),
        ]
        for fb in fallbacks:
            if fb not in selected_tools:
                selected_tools.append(fb)
            if len(selected_tools) >= 2:
                break

    return selected_tools


# ─── MCP Connection ─────────────────────────────────────────────────────────

class MCPConnection:
    """Manages the MCP server subprocess and JSON-RPC communication."""

    def __init__(self):
        self.process = None
        self.request_id = 0

    def connect(self) -> bool:
        """Start the MCP server and perform the initialization handshake."""
        try:
            self.process = subprocess.Popen(
                LPI_SERVER_CMD,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=LPI_SERVER_CWD,
            )
        except FileNotFoundError:
            print("[ERROR] Could not start LPI server.")
            print("        Make sure you've run: npm run build")
            print(f"        Looking for: {LPI_SERVER_CMD}")
            return False

        # MCP initialization handshake
        init_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "shishir-smile-advisor", "version": VERSION},
            },
        }
        self._send(init_req)
        resp = self._receive()
        if not resp:
            print("[ERROR] No response from MCP server during initialization.")
            return False

        # Send initialized notification
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        self._send(notif)

        return True

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Send a tool call request and return the text result."""
        if not self.process or self.process.poll() is not None:
            return f"[ERROR] MCP server is not running"

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        try:
            self._send(request)
            resp = self._receive()

            if not resp:
                return f"[ERROR] No response from MCP server for {tool_name}"

            if "result" in resp and "content" in resp["result"]:
                return resp["result"]["content"][0].get("text", "")
            if "error" in resp:
                return f"[ERROR] {resp['error'].get('message', 'Unknown error')}"

            return "[ERROR] Unexpected response format"
        except Exception as e:
            return f"[ERROR] Tool call failed: {e}"

    def disconnect(self):
        """Cleanly shut down the MCP server."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()

    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def _send(self, data: dict):
        self.process.stdin.write(json.dumps(data) + "\n")
        self.process.stdin.flush()

    def _receive(self) -> dict | None:
        try:
            line = self.process.stdout.readline()
            if not line:
                return None
            return json.loads(line)
        except (json.JSONDecodeError, Exception):
            return None


# ─── LLM Integration ────────────────────────────────────────────────────────

def check_ollama() -> bool:
    """Check if Ollama is running and the model is available."""
    if not HAS_REQUESTS:
        return False
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            # Check if our model (or a variant) is available
            for m in models:
                if OLLAMA_MODEL.split(":")[0] in m:
                    return True
            if models:
                print(f"  [INFO] Available models: {', '.join(models)}")
                print(f"  [INFO] Expected: {OLLAMA_MODEL}")
            return False
        return False
    except Exception:
        return False


def query_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and return the response."""
    if not HAS_REQUESTS:
        return "[ERROR] 'requests' library not installed. Run: pip install requests"

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 1024},
            },
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json().get("response", "[No response from model]")
    except requests.ConnectionError:
        return "[ERROR] Cannot connect to Ollama. Is it running? (ollama serve)"
    except requests.Timeout:
        return "[ERROR] Ollama request timed out (180s). Try a smaller model."
    except Exception as e:
        return f"[ERROR] Ollama error: {e}"


# ─── Provenance & Synthesis ─────────────────────────────────────────────────

def build_provenance_prompt(question: str, sources: list) -> str:
    """
    Build a prompt that includes all tool results as numbered sources,
    instructing the LLM to cite them inline.
    """
    source_blocks = []
    for i, (tool_name, args, result) in enumerate(sources, 1):
        args_str = json.dumps(args) if args else "(no args)"
        # Truncate very long results to stay within context window
        truncated = result[:2000] if len(result) > 2000 else result
        source_blocks.append(
            f"--- [Source {i}]: {tool_name}({args_str}) ---\n{truncated}"
        )

    sources_text = "\n\n".join(source_blocks)

    return f"""You are the SMILE Digital Twin Advisor, an expert on the SMILE methodology
(Sustainable Methodology for Impact Lifecycle Enablement) and digital twin implementations.

Answer the user's question using ONLY the sources provided below. For each claim or fact
in your answer, cite the source using [Source N] notation. Be concise and structured.

{sources_text}

--- User Question ---
{question}

Instructions:
1. Answer the question directly and concisely
2. Cite [Source N] after each key fact or claim
3. If sources don't contain enough information, say so honestly
4. End with a "Sources Used" section listing which sources contributed what
5. Use markdown formatting for readability
"""


def format_source_table(sources: list) -> str:
    """Format a clean provenance table showing all tools queried."""
    lines = [
        "",
        "=" * 60,
        "  PROVENANCE -- Tools Queried",
        "=" * 60,
    ]
    for i, (tool_name, args, result) in enumerate(sources, 1):
        args_str = json.dumps(args) if args else "(no args)"
        status = "OK" if not result.startswith("[ERROR]") else "FAIL"
        chars = len(result)
        lines.append(f"  [{i}] {status} {tool_name} {args_str}")
        lines.append(f"      -> {chars} chars returned")
    lines.append("=" * 60)
    return "\n".join(lines)


def fallback_synthesis(question: str, sources: list) -> str:
    """
    When Ollama is not available, produce a structured summary by
    extracting key sections from tool results.
    """
    output_parts = [
        "",
        "=" * 60,
        f"  ANSWER (Direct Tool Output -- LLM unavailable)",
        "=" * 60,
        "",
        f"Question: {question}",
        "",
    ]

    for i, (tool_name, args, result) in enumerate(sources, 1):
        if result.startswith("[ERROR]"):
            continue
        output_parts.append(f"--- From [Source {i}]: {tool_name} ---")
        # Show first 800 chars of each result
        preview = result[:800]
        if len(result) > 800:
            preview += "\n  ... (truncated)"
        output_parts.append(preview)
        output_parts.append("")

    output_parts.append("-" * 60)
    output_parts.append("NOTE: Install Ollama and run 'ollama serve' for AI-synthesized answers.")
    output_parts.append(f"      Model needed: {OLLAMA_MODEL}")

    return "\n".join(output_parts)


# ─── Main Agent Logic ────────────────────────────────────────────────────────

def process_question(question: str, mcp: MCPConnection, use_llm: bool) -> None:
    """Process a single question: route → query tools → synthesize → display."""

    # Step 1: Classify and route
    tool_plan = classify_question(question)
    tool_names = [t[0] for t in tool_plan]
    print(f"\n  [PLAN] Tool plan: {', '.join(tool_names)} ({len(tool_plan)} tools)")

    # Step 2: Query each tool
    sources = []
    for idx, (tool_name, args) in enumerate(tool_plan, 1):
        args_display = json.dumps(args) if args else "{}"
        print(f"  [{idx}/{len(tool_plan)}] Querying {tool_name}({args_display})...")
        result = mcp.call_tool(tool_name, args)
        sources.append((tool_name, args, result))

        if result.startswith("[ERROR]"):
            print(f"         [!] {result}")

    # Step 3: Synthesize
    if use_llm:
        print(f"\n  [LLM] Sending to {OLLAMA_MODEL} for synthesis...")
        prompt = build_provenance_prompt(question, sources)
        answer = query_ollama(prompt)

        print(f"\n{'=' * 60}")
        print("  ANSWER")
        print(f"{'=' * 60}\n")
        print(answer)
    else:
        print(fallback_synthesis(question, sources))

    # Step 4: Show provenance
    print(format_source_table(sources))


def print_banner():
    """Print the agent welcome banner."""
    print(f"""
+=========================================================+
|  {AGENT_NAME}  v{VERSION}               |
|  Author: Shishir Chaudhary (@Shishir-DS28)              |
|                                                          |
|  An explainable AI agent powered by the LPI MCP Server   |
|  and the SMILE methodology for digital twins.            |
+=========================================================+
""")


def print_help():
    """Print available commands."""
    print("""
  Available Commands:
  ------------------
  /help     -- Show this help message
  /tools    -- List available LPI tools
  /quit     -- Exit the agent
  /exit     -- Exit the agent

  Or just type any question about digital twins, SMILE,
  or implementation guidance!

  Example questions:
    "What is the SMILE methodology?"
    "How do I implement a digital twin for healthcare?"
    "Explain the Reality Emulation phase"
    "Show me case studies for smart buildings"
    "What is edge-native intelligence?"
""")


def run_interactive(mcp: MCPConnection, use_llm: bool):
    """Run the agent in interactive conversation mode."""
    print_banner()

    mode = "LLM-assisted" if use_llm else "Direct output (no LLM)"
    print(f"  Mode: {mode}")
    if use_llm:
        print(f"  Model: {OLLAMA_MODEL}")
    print(f"  Type /help for commands, or ask a question.\n")

    while True:
        try:
            question = input("  You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye!")
            break

        if not question:
            continue

        if question.lower() in ("/quit", "/exit"):
            print("\n  Goodbye!")
            break

        if question.lower() == "/help":
            print_help()
            continue

        if question.lower() == "/tools":
            print("\n  Available LPI Tools:")
            print("  ─────────────────────")
            tools = [
                ("smile_overview", "Full overview of the SMILE methodology"),
                ("smile_phase_detail", "Deep dive into a specific SMILE phase"),
                ("query_knowledge", "Search the knowledge base (63 entries)"),
                ("get_case_studies", "Browse 10 anonymized case studies"),
                ("get_insights", "Scenario-specific implementation advice"),
                ("list_topics", "Browse all available topics"),
                ("get_methodology_step", "Step-by-step phase guidance"),
            ]
            for name, desc in tools:
                print(f"    • {name}: {desc}")
            print()
            continue

        process_question(question, mcp, use_llm)
        print()


def run_single(question: str, mcp: MCPConnection, use_llm: bool):
    """Process a single question and exit."""
    print(f"\n{'=' * 60}")
    print(f"  {AGENT_NAME}")
    print(f"  Question: {question}")
    print(f"{'=' * 60}")

    process_question(question, mcp, use_llm)


def main():
    """Entry point: set up MCP connection, check LLM, run agent."""

    # Parse command-line arguments
    single_question = None
    if len(sys.argv) > 1:
        single_question = " ".join(sys.argv[1:])

    # Connect to MCP server
    print("\n  [*] Connecting to LPI MCP server...")
    mcp = MCPConnection()
    if not mcp.connect():
        print("\n  [FATAL] Could not connect to the LPI MCP server.")
        print("  Make sure you've run: npm run build")
        sys.exit(1)
    print("  [OK] Connected to LPI MCP server")

    # Check Ollama availability
    print("  [*] Checking Ollama LLM...")
    use_llm = check_ollama()
    if use_llm:
        print(f"  [OK] Ollama ready with model {OLLAMA_MODEL}")
    else:
        print(f"  [WARN] Ollama not available -- running in fallback mode (no LLM)")
        print(f"    To enable: ollama serve & ollama pull {OLLAMA_MODEL}")

    try:
        if single_question:
            run_single(single_question, mcp, use_llm)
        else:
            run_interactive(mcp, use_llm)
    finally:
        mcp.disconnect()
        print("  [*] Disconnected from LPI server.\n")


if __name__ == "__main__":
    main()
