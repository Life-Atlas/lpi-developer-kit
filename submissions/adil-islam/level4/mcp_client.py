"""
mcp_client.py — Reusable MCP stdio client for Level 4 agents.

Wraps the JSON-RPC handshake and tool-call pattern from the existing
ai-learning-coach-agent into a class so both Agent A and Agent B
can share it without code duplication.

Usage:
    client = MCPClient(repo_root, guard)
    client.start()
    result = client.call_tool("smile_overview", {})
    client.stop()
"""

import json
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

MAX_CHARS = 1200  # trim per tool response to avoid model overload


class MCPClient:
    """
    Manages a single MCP server subprocess (the LPI node server).
    One instance per agent invocation — start(), call tools, stop().
    """

    def __init__(self, repo_root: str, guard):
        """
        repo_root : absolute path to the lpi-developer-kit repo root
        guard     : SecurityGuard instance — enforces allowed tool list
        """
        self.repo_root = repo_root
        self.guard = guard
        self.proc = None
        self._cmd = ["node", os.path.join(repo_root, "dist", "src", "index.js")]

    def start(self):
        """Spawn the LPI MCP server process and complete the initialize handshake."""
        self.proc = subprocess.Popen(
            self._cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.repo_root,
        )

        # Send initialize request (required by MCP protocol before any tool calls)
        init_msg = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": self.guard.agent_name,
                    "version": "1.0.0",
                },
            },
        }
        self._send(init_msg)
        self.proc.stdout.readline()  # consume initialize response

        # Send initialized notification to complete handshake
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        logger.info("[%s] MCP server started", self.guard.agent_name)

    def call_tool(self, tool_name: str, args: dict) -> str:
        """
        Call a named LPI tool via MCP JSON-RPC.

        Security check: SecurityGuard.check_tool_permission() is called first
        to prevent privilege escalation (an agent calling a tool outside its
        allowed set).

        Returns the text content of the tool response, trimmed to MAX_CHARS.
        """
        # ── Privilege escalation guard ────────────────────────────────────────
        self.guard.check_tool_permission(tool_name)

        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args},
        }
        self._send(req)
        line = self.proc.stdout.readline()

        if not line:
            return f"[no response from {tool_name}]"

        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            return f"[malformed response from {tool_name}]"

        if "result" in resp and "content" in resp["result"]:
            raw = resp["result"]["content"][0].get("text", "")
            return raw[:MAX_CHARS]

        if "error" in resp:
            return f"[error: {resp['error'].get('message', 'unknown')}]"

        return "[unexpected response format]"

    def stop(self):
        """Terminate the MCP server subprocess cleanly."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
            self.proc = None
            logger.info("[%s] MCP server stopped", self.guard.agent_name)

    # ── Internal helper ───────────────────────────────────────────────────────

    def _send(self, msg: dict):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
