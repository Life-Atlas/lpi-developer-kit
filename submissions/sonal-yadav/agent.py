#!/usr/bin/env python3
"""
SMILE Compass — An Intelligent LPI Navigator
Author: Sonal Yadav (@sonalydav789)
Version: 2.0.0

A multi-mode AI agent that connects to the LPI MCP server and offers:
  1. Smart Q&A     — Ask anything about SMILE / digital twins
  2. Compare Mode  — Compare industries, phases, or approaches side-by-side
  3. Maturity Scan  — Assess where you are on the SMILE journey
  4. Deep Dive     — Exhaustive analysis using ALL relevant tools

The agent uses conversation memory, multi-tool orchestration with dependency
resolution, and full provenance tracking with inline citations.

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
  python submissions/sonal-yadav/agent.py                      # Interactive mode
  python submissions/sonal-yadav/agent.py "Your question here"  # Single question
"""

import json
import subprocess
import sys
import os
import time
import textwrap
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── Configuration ───────────────────────────────────────────────────────────

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LPI_SERVER_CMD = ["node", os.path.join(REPO_ROOT, "dist", "src", "index.js")]
LPI_SERVER_CWD = REPO_ROOT

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

VERSION = "2.0.0"
AGENT_NAME = "SMILE Compass"

# Max chars to keep from each tool response to fit context window
MAX_SOURCE_CHARS = 1800

# ─── SMILE Phase Registry ───────────────────────────────────────────────────

PHASES = {
    "reality-emulation":       {"order": 1, "short": "RE",  "name": "Reality Emulation"},
    "concurrent-engineering":  {"order": 2, "short": "CE",  "name": "Concurrent Engineering"},
    "collective-intelligence": {"order": 3, "short": "CI3", "name": "Collective Intelligence"},
    "contextual-intelligence": {"order": 4, "short": "CI4", "name": "Contextual Intelligence"},
    "continuous-intelligence": {"order": 5, "short": "CI5", "name": "Continuous Intelligence"},
    "perpetual-wisdom":        {"order": 6, "short": "PW",  "name": "Perpetual Wisdom"},
}

PHASE_ALIASES = {}
for pid, info in PHASES.items():
    PHASE_ALIASES[pid] = pid
    PHASE_ALIASES[info["name"].lower()] = pid
    PHASE_ALIASES[info["short"].lower()] = pid
    PHASE_ALIASES[f"phase {info['order']}"] = pid
    PHASE_ALIASES[f"phase{info['order']}"] = pid

INDUSTRY_KEYWORDS = [
    "healthcare", "manufacturing", "energy", "maritime", "smart building",
    "agriculture", "hospital", "horse", "equine", "pharmaceutical",
    "automotive", "construction", "logistics", "retail", "education",
]


# ─── MCP Connection ─────────────────────────────────────────────────────────

class MCPConnection:
    """Manages lifecycle of the LPI MCP server subprocess."""

    def __init__(self):
        self.process = None
        self._req_id = 0

    def start(self) -> bool:
        """Launch the MCP server and complete the JSON-RPC handshake."""
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
            return False

        # Initialize
        self._req_id += 1
        self._write({
            "jsonrpc": "2.0", "id": self._req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smile-compass", "version": VERSION},
            },
        })
        resp = self._read()
        if not resp:
            return False

        # Confirm initialized
        self._write({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return True

    def call(self, tool: str, args: dict | None = None) -> str:
        """Call an LPI tool and return its text content."""
        if not self.process or self.process.poll() is not None:
            return "[ERROR] Server not running"
        self._req_id += 1
        self._write({
            "jsonrpc": "2.0", "id": self._req_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": args or {}},
        })
        resp = self._read()
        if not resp:
            return f"[ERROR] No response for {tool}"
        if "result" in resp and "content" in resp["result"]:
            return resp["result"]["content"][0].get("text", "")
        if "error" in resp:
            return f"[ERROR] {resp['error'].get('message', 'unknown')}"
        return "[ERROR] Unexpected format"

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def _write(self, data: dict):
        self.process.stdin.write(json.dumps(data) + "\n")
        self.process.stdin.flush()

    def _read(self) -> dict | None:
        try:
            line = self.process.stdout.readline()
            return json.loads(line) if line else None
        except Exception:
            return None


# ─── Ollama LLM ─────────────────────────────────────────────────────────────

def ollama_available() -> bool:
    if not HAS_REQUESTS:
        return False
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code != 200:
            return False
        models = [m["name"] for m in r.json().get("models", [])]
        return any(OLLAMA_MODEL.split(":")[0] in m for m in models)
    except Exception:
        return False


def ask_llm(prompt: str) -> str:
    if not HAS_REQUESTS:
        return "[ERROR] requests library missing"
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 1024},
            },
            timeout=180,
        )
        r.raise_for_status()
        return r.json().get("response", "[No response]")
    except requests.ConnectionError:
        return "[ERROR] Ollama not reachable — run 'ollama serve'"
    except requests.Timeout:
        return "[ERROR] Ollama timed out"
    except Exception as e:
        return f"[ERROR] {e}"


# ─── Question Analyzer ─────────────────────────────────────────────────────

def detect_mode(text: str) -> str:
    """Detect which agent mode best fits the user's input."""
    t = text.lower()

    compare_signals = ["compare", "vs", "versus", "difference between",
                       "how does .* differ", "which is better", "contrast"]
    for sig in compare_signals:
        if sig in t:
            return "compare"

    maturity_signals = ["assess", "maturity", "readiness", "where am i",
                        "evaluate my", "how ready", "how mature", "which phase am i"]
    for sig in maturity_signals:
        if sig in t:
            return "maturity"

    deep_signals = ["deep dive", "everything about", "tell me all",
                    "comprehensive", "exhaustive", "full analysis"]
    for sig in deep_signals:
        if sig in t:
            return "deep"

    return "qa"


def resolve_phases(text: str) -> list:
    """Extract SMILE phase IDs mentioned in text."""
    t = text.lower()
    found = []
    for alias, pid in PHASE_ALIASES.items():
        if alias in t and pid not in found:
            found.append(pid)
    return found


def resolve_industries(text: str) -> list:
    t = text.lower()
    return [ind for ind in INDUSTRY_KEYWORDS if ind in t]


def build_tool_plan(question: str, mode: str) -> list:
    """
    Return a list of (tool_name, args_dict, reason_str) tuples.
    Always returns at least 2 tools (Level 3 requirement).
    """
    q = question.lower()
    phases = resolve_phases(question)
    industries = resolve_industries(question)
    plan = []

    def add(tool, args=None, reason=""):
        entry = (tool, args or {}, reason)
        if entry not in plan:
            plan.append(entry)

    if mode == "compare":
        # Get overview for baseline
        add("smile_overview", {}, "baseline methodology context")
        # Get details for each phase mentioned
        for pid in phases:
            add("smile_phase_detail", {"phase": pid},
                f"detail for {PHASES[pid]['name']}")
        # Industry case studies
        for ind in industries:
            add("get_case_studies", {"query": ind},
                f"case studies for {ind}")
        if not industries:
            add("get_case_studies", {}, "all case studies for comparison")
        add("query_knowledge", {"query": question[:100]},
            "knowledge base search")

    elif mode == "maturity":
        add("smile_overview", {}, "full methodology for maturity mapping")
        add("list_topics", {}, "all available topics")
        for pid in phases:
            add("get_methodology_step", {"phase": pid},
                f"implementation steps for {PHASES[pid]['name']}")
        if not phases:
            # Get first two phases for default maturity context
            add("get_methodology_step", {"phase": "reality-emulation"},
                "Phase 1 steps for maturity baseline")
            add("smile_phase_detail", {"phase": "reality-emulation"},
                "Phase 1 detail")
        add("query_knowledge", {"query": question[:100]},
            "related knowledge")

    elif mode == "deep":
        add("smile_overview", {}, "full methodology overview")
        for pid in phases:
            add("smile_phase_detail", {"phase": pid},
                f"deep dive into {PHASES[pid]['name']}")
            add("get_methodology_step", {"phase": pid},
                f"implementation steps for {PHASES[pid]['name']}")
        add("query_knowledge", {"query": question[:100]},
            "knowledge base search")
        for ind in industries:
            add("get_case_studies", {"query": ind},
                f"case studies for {ind}")
        add("get_insights", {"scenario": question[:200]},
            "implementation insights")
        if not phases and not industries:
            add("list_topics", {}, "browse all available topics")

    else:  # qa — default smart routing
        # Always search knowledge
        add("query_knowledge", {"query": question[:100]},
            "knowledge base search")

        # Phase-specific tools
        for pid in phases:
            add("smile_phase_detail", {"phase": pid},
                f"detail for {PHASES[pid]['name']}")

        # Industry case studies
        if industries:
            for ind in industries:
                add("get_case_studies", {"query": ind},
                    f"case studies for {ind}")
        elif any(w in q for w in ["case stud", "example", "real world"]):
            add("get_case_studies", {}, "browse case studies")

        # How-to / implementation
        if any(w in q for w in ["how to", "implement", "start", "build",
                                "deploy", "step", "guide", "getting started"]):
            add("get_insights", {"scenario": question[:200]},
                "implementation advice")
            if phases:
                for pid in phases:
                    add("get_methodology_step", {"phase": pid},
                        f"steps for {PHASES[pid]['name']}")

        # Methodology overview
        if any(w in q for w in ["smile", "methodology", "overview",
                                "framework", "what is", "explain"]):
            add("smile_overview", {}, "methodology overview")

        # Topics
        if any(w in q for w in ["topic", "list", "browse", "available",
                                "what can"]):
            add("list_topics", {}, "available topics")

    # Guarantee ≥2 tools
    if len(plan) < 2:
        fallbacks = [
            ("smile_overview", {}, "methodology context"),
            ("query_knowledge", {"query": question[:100]}, "knowledge search"),
            ("list_topics", {}, "topic listing"),
        ]
        for fb in fallbacks:
            if fb not in plan:
                plan.append(fb)
            if len(plan) >= 2:
                break

    return plan


# ─── Provenance Engine ──────────────────────────────────────────────────────

class ProvenanceEngine:
    """Tracks every tool call and its results for citation."""

    def __init__(self):
        self.sources = []  # List of {id, tool, args, reason, text, chars, ok}

    def record(self, tool: str, args: dict, reason: str, text: str):
        sid = len(self.sources) + 1
        self.sources.append({
            "id": sid,
            "tool": tool,
            "args": args,
            "reason": reason,
            "text": text,
            "chars": len(text),
            "ok": not text.startswith("[ERROR]"),
        })

    def build_context(self) -> str:
        """Build the numbered source context for the LLM prompt."""
        blocks = []
        for s in self.sources:
            if not s["ok"]:
                continue
            truncated = s["text"][:MAX_SOURCE_CHARS]
            args_s = json.dumps(s["args"]) if s["args"] else "(none)"
            blocks.append(
                f'--- [Source {s["id"]}]: {s["tool"]}({args_s}) ---\n'
                f'Reason queried: {s["reason"]}\n'
                f'{truncated}'
            )
        return "\n\n".join(blocks)

    def format_table(self) -> str:
        """Format a provenance table for display."""
        lines = [
            "",
            "+" + "-" * 58 + "+",
            "|  PROVENANCE -- Tools Queried" + " " * 30 + "|",
            "+" + "-" * 58 + "+",
        ]
        for s in self.sources:
            status = "OK" if s["ok"] else "FAIL"
            args_s = json.dumps(s["args"]) if s["args"] else "{}"
            tool_line = f"|  [{s['id']}] {status} {s['tool']}"
            tool_line = tool_line.ljust(59) + "|"
            lines.append(tool_line)
            args_line = f"|      args: {args_s}"
            args_line = args_line[:59].ljust(59) + "|"
            lines.append(args_line)
            meta_line = f"|      why:  {s['reason'][:40]}"
            meta_line = meta_line[:59].ljust(59) + "|"
            lines.append(meta_line)
            chars_line = f"|      -> {s['chars']} chars returned"
            chars_line = chars_line.ljust(59) + "|"
            lines.append(chars_line)
            lines.append("+" + "-" * 58 + "+")

        return "\n".join(lines)


# ─── Conversation Memory ───────────────────────────────────────────────────

class Memory:
    """Simple conversation memory for context across questions."""

    def __init__(self):
        self.history = []  # list of (question, mode, tool_count, timestamp)

    def add(self, question: str, mode: str, tool_count: int):
        self.history.append({
            "q": question,
            "mode": mode,
            "tools": tool_count,
            "time": datetime.now().strftime("%H:%M:%S"),
        })

    def summary(self) -> str:
        if not self.history:
            return "No prior questions in this session."
        lines = []
        for i, h in enumerate(self.history, 1):
            lines.append(f"  {i}. [{h['time']}] ({h['mode']}) {h['q'][:60]}")
        return "\n".join(lines)

    def context_hint(self) -> str:
        """Return last question as context hint for the LLM."""
        if not self.history:
            return ""
        last = self.history[-1]
        return f"\n(Previous question in this session: \"{last['q'][:80]}\")\n"


# ─── Synthesis ──────────────────────────────────────────────────────────────

MODE_PROMPTS = {
    "qa": """You are SMILE Compass -- an expert advisor on the SMILE methodology
(Sustainable Methodology for Impact Lifecycle Enablement) and digital twin
implementations. Answer the user's question using ONLY the sources below.
Cite [Source N] after each claim. Be concise and structured.""",

    "compare": """You are SMILE Compass in COMPARISON MODE. The user wants you to
compare concepts, phases, industries, or approaches. Structure your answer as a
clear comparison with categories. Use a table if appropriate. Cite [Source N]
for each fact.""",

    "maturity": """You are SMILE Compass in MATURITY ASSESSMENT MODE. Based on the
sources below, help the user understand where they might be on the SMILE journey.
Reference specific phase characteristics and activities. Suggest concrete next
steps. Cite [Source N].""",

    "deep": """You are SMILE Compass in DEEP DIVE MODE. Provide a comprehensive,
detailed analysis using all available sources. Cover background, key concepts,
implementation details, and practical guidance. Cite [Source N] for every claim.
Organize with clear headings.""",
}


def synthesize(question: str, mode: str, provenance: ProvenanceEngine,
               memory: Memory, use_llm: bool) -> str:
    """Synthesize an answer from collected sources."""
    context = provenance.build_context()
    mem_hint = memory.context_hint()

    if not use_llm:
        return _fallback_synthesis(question, provenance)

    sys_prompt = MODE_PROMPTS.get(mode, MODE_PROMPTS["qa"])
    prompt = f"""{sys_prompt}

{context}
{mem_hint}
--- User Question ---
{question}

Instructions:
1. Answer directly and concisely
2. Cite [Source N] after each key fact
3. If sources lack information, say so
4. End with a "Sources Used" summary
5. Use markdown formatting
"""
    return ask_llm(prompt)


def _fallback_synthesis(question: str, provenance: ProvenanceEngine) -> str:
    """When no LLM is available, present structured tool output."""
    parts = [
        "",
        "=" * 60,
        "  ANSWER (Direct Tool Output -- LLM unavailable)",
        "=" * 60,
        "",
        f"  Question: {question}",
        "",
    ]
    for s in provenance.sources:
        if not s["ok"]:
            continue
        parts.append(f"  --- From [Source {s['id']}]: {s['tool']} ---")
        parts.append(f"  (Reason: {s['reason']})")
        preview = s["text"][:1000]
        if len(s["text"]) > 1000:
            preview += "\n  ... (truncated)"
        parts.append(preview)
        parts.append("")
    parts.append("-" * 60)
    parts.append("  TIP: Install Ollama for AI-synthesized answers.")
    parts.append(f"       ollama serve && ollama pull {OLLAMA_MODEL}")
    return "\n".join(parts)


# ─── Main Agent Loop ────────────────────────────────────────────────────────

def process_question(question: str, mcp: MCPConnection, use_llm: bool,
                     memory: Memory) -> None:
    """Full pipeline: analyze -> plan -> query -> synthesize -> display."""

    # Step 1: Detect mode
    mode = detect_mode(question)
    mode_labels = {"qa": "Smart Q&A", "compare": "Compare",
                   "maturity": "Maturity Scan", "deep": "Deep Dive"}
    print(f"\n  >> Mode: {mode_labels[mode]}")

    # Step 2: Build tool plan
    plan = build_tool_plan(question, mode)
    tool_names = [f"{t[0]}" for t in plan]
    print(f"  >> Tools: {', '.join(tool_names)} ({len(plan)} tools)")

    # Step 3: Execute tools
    prov = ProvenanceEngine()
    for idx, (tool, args, reason) in enumerate(plan, 1):
        args_display = json.dumps(args) if args else "{}"
        print(f"  [{idx}/{len(plan)}] {tool}({args_display}) -- {reason}")
        result = mcp.call(tool, args)
        prov.record(tool, args, reason, result)
        if result.startswith("[ERROR]"):
            print(f"         [!] {result}")

    # Step 4: Synthesize
    if use_llm:
        print(f"\n  >> Synthesizing with {OLLAMA_MODEL}...")
    answer = synthesize(question, mode, prov, memory, use_llm)

    # Step 5: Display
    print(f"\n{'=' * 60}")
    print(f"  ANSWER")
    print(f"{'=' * 60}\n")
    print(answer)
    print(prov.format_table())

    # Step 6: Update memory
    memory.add(question, mode, len(plan))


# ─── CLI Interface ──────────────────────────────────────────────────────────

BANNER = f"""
+=========================================================+
|   {AGENT_NAME}  v{VERSION}                              |
|   An Intelligent LPI Navigator                          |
|   Author: Sonal Yadav (@sonalydav789)                   |
+=========================================================+
|                                                          |
|   Modes:                                                 |
|     - Smart Q&A     -- ask anything about SMILE          |
|     - Compare       -- use "compare" or "vs" in query    |
|     - Maturity Scan -- use "assess" or "maturity"        |
|     - Deep Dive     -- use "deep dive" or "comprehensive"|
|                                                          |
+=========================================================+
"""

HELP_TEXT = """
  Commands:
  ---------
  /help      Show this help
  /tools     List LPI tools
  /history   Show questions asked this session
  /modes     Explain the 4 agent modes
  /quit      Exit

  Just type a question to get started!

  Example questions:
    "What is the SMILE methodology?"
    "Compare healthcare and manufacturing digital twins"
    "Assess my maturity -- I have sensor data but no ontology"
    "Deep dive into Reality Emulation phase"
    "How do I implement a digital twin for smart buildings?"
"""

TOOLS_TEXT = """
  LPI Tools Available:
  --------------------
  1. smile_overview        Full SMILE methodology overview
  2. smile_phase_detail    Deep dive into a specific phase
  3. query_knowledge       Search 63 knowledge base entries
  4. get_case_studies      Browse 10 industry case studies
  5. get_insights          Scenario-specific advice
  6. list_topics           Browse all available topics
  7. get_methodology_step  Step-by-step phase guidance
"""

MODES_TEXT = """
  Agent Modes:
  ------------
  1. Smart Q&A (default)
     Intelligently routes your question to 2-4 relevant tools.
     Trigger: any normal question.

  2. Compare Mode
     Compares industries, phases, or approaches side-by-side.
     Trigger: use words like "compare", "vs", "difference between".

  3. Maturity Scan
     Helps assess where you are on the SMILE journey.
     Trigger: use words like "assess", "maturity", "readiness".

  4. Deep Dive
     Exhaustive analysis pulling from 4-6 tools.
     Trigger: use words like "deep dive", "comprehensive", "everything about".
"""


def run_interactive(mcp: MCPConnection, use_llm: bool):
    """Interactive conversation loop."""
    print(BANNER)
    status = "LLM-assisted" if use_llm else "Direct output (no LLM)"
    print(f"  Status: {status}")
    if use_llm:
        print(f"  Model:  {OLLAMA_MODEL}")
    print("  Type /help for commands.\n")

    memory = Memory()

    while True:
        try:
            q = input("  You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye!")
            break

        if not q:
            continue

        cmd = q.lower()
        if cmd in ("/quit", "/exit", "/q"):
            print("\n  Goodbye!")
            break
        elif cmd == "/help":
            print(HELP_TEXT)
        elif cmd == "/tools":
            print(TOOLS_TEXT)
        elif cmd == "/modes":
            print(MODES_TEXT)
        elif cmd == "/history":
            print(f"\n  Session History:\n{memory.summary()}\n")
        else:
            process_question(q, mcp, use_llm, memory)
            print()


def run_single(question: str, mcp: MCPConnection, use_llm: bool):
    """Process a single question and exit."""
    print(f"\n{'=' * 60}")
    print(f"  {AGENT_NAME} v{VERSION}")
    print(f"  Question: {question}")
    print(f"{'=' * 60}")
    memory = Memory()
    process_question(question, mcp, use_llm, memory)


# ─── Entry Point ────────────────────────────────────────────────────────────

def main():
    single_question = None
    if len(sys.argv) > 1:
        single_question = " ".join(sys.argv[1:])

    # Connect to MCP server
    print("\n  [*] Starting LPI MCP server...")
    mcp = MCPConnection()
    if not mcp.start():
        print("\n  [FATAL] Could not start the LPI MCP server.")
        print("  Make sure you've run:  npm run build")
        print(f"  Looking for: {' '.join(LPI_SERVER_CMD)}")
        sys.exit(1)
    print("  [OK] Connected to LPI MCP server")

    # Check Ollama
    print("  [*] Checking Ollama LLM...")
    use_llm = ollama_available()
    if use_llm:
        print(f"  [OK] Ollama ready ({OLLAMA_MODEL})")
    else:
        print(f"  [!] Ollama not available -- fallback mode (no LLM)")
        print(f"      To enable: ollama serve && ollama pull {OLLAMA_MODEL}")

    try:
        if single_question:
            run_single(single_question, mcp, use_llm)
        else:
            run_interactive(mcp, use_llm)
    finally:
        mcp.stop()
        print("  [*] Disconnected from LPI server.\n")


if __name__ == "__main__":
    main()
