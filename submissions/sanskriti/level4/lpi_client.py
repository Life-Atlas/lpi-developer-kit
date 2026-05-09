#!/usr/bin/env python3
"""Minimal MCP stdio client for calling LPI tools safely."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[3]
LPI_SERVER_JS = REPO_ROOT / "dist" / "src" / "index.js"


class LPIClientError(Exception):
    pass


def _extract_text(result_obj: Dict) -> str:
    content = result_obj.get("content", [])
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            return str(first.get("text", ""))
    return ""


def call_tools(tool_calls: List[Dict], timeout_seconds: int = 20) -> List[Dict]:
    """
    Execute a sequence of MCP tool calls in one server session.

    Each entry in tool_calls must look like:
    {"name": "query_knowledge", "arguments": {"query": "..."}}
    """
    if not LPI_SERVER_JS.exists():
        raise LPIClientError(
            f"LPI build not found at {LPI_SERVER_JS}. Run 'npm run build' from repo root first."
        )

    proc = subprocess.Popen(
        ["node", str(LPI_SERVER_JS)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(REPO_ROOT),
    )

    responses: List[Dict] = []
    try:
        # initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "level4-secure-mesh", "version": "1.0.0"},
            },
        }
        assert proc.stdin is not None
        assert proc.stdout is not None

        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        _ = proc.stdout.readline()

        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()

        request_id = 1
        for item in tool_calls:
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": item["name"],
                    "arguments": item.get("arguments", {}),
                },
            }
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()

            line = proc.stdout.readline()
            if not line:
                raise LPIClientError(f"No response for tool '{item['name']}'")

            msg = json.loads(line)
            if "error" in msg:
                responses.append(
                    {
                        "tool": item["name"],
                        "ok": False,
                        "error": str(msg["error"].get("message", "unknown_error")),
                    }
                )
            else:
                result = msg.get("result", {})
                responses.append(
                    {
                        "tool": item["name"],
                        "ok": True,
                        "text": _extract_text(result),
                    }
                )
            request_id += 1

        proc.terminate()
        proc.wait(timeout=timeout_seconds)
        return responses

    except subprocess.TimeoutExpired as exc:
        proc.kill()
        raise LPIClientError("LPI MCP process timeout") from exc
    except json.JSONDecodeError as exc:
        proc.kill()
        raise LPIClientError("Invalid JSON from LPI MCP process") from exc
    except OSError as exc:
        proc.kill()
        raise LPIClientError(f"OS error while talking to LPI MCP: {exc}") from exc
    finally:
        if proc.poll() is None:
            proc.kill()
