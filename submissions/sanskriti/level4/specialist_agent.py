#!/usr/bin/env python3
"""Specialist agent server for SMILE and case-study analysis."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

from lpi_client import LPIClientError, call_tools
from mesh_common import (
    auth_ok,
    check_rate_limit,
    default_rate_table,
    error_payload,
    json_response,
    read_json_request,
    sanitize_question,
    validate_a2a_envelope,
)


def _extract_points(text: str, max_points: int = 3) -> List[str]:
    lines = [ln.strip(" -\t") for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ["No concise points were extracted."]
    return lines[:max_points]


def build_handler(agent_id: str, specialty: str, card_path: Path, allowed_callers: Dict[str, str]):
    rate_table = default_rate_table()

    if specialty not in {"smile", "case"}:
        raise ValueError("specialty must be one of: smile, case")

    with card_path.open("r", encoding="utf-8") as f:
        agent_card = json.load(f)

    class SpecialistHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/.well-known/agent.json":
                json_response(self, 200, agent_card)
                return
            if self.path == "/healthz":
                json_response(self, 200, {"status": "ok", "agent": agent_id})
                return
            json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:
            if self.path != "/a2a/query":
                json_response(self, 404, {"error": "not_found"})
                return

            rate_check = check_rate_limit(rate_table, self.client_address[0])
            if not rate_check.ok:
                json_response(self, 429, error_payload(agent_id, "unknown", rate_check.reason))
                return

            auth_check = auth_ok(self.headers, allowed_callers)
            if not auth_check.ok:
                json_response(self, 403, error_payload(agent_id, "unknown", auth_check.reason))
                return

            body_ok, body = read_json_request(self)
            if not body_ok.ok:
                json_response(self, 400, error_payload(agent_id, "unknown", body_ok.reason))
                return

            request_id = str(body.get("request_id", "unknown"))

            env_ok = validate_a2a_envelope(body, expected_to_agent=agent_id)
            if not env_ok.ok:
                json_response(self, 400, error_payload(agent_id, request_id, env_ok.reason))
                return

            intent = body["intent"]
            allowed_intent = "smile_analysis" if specialty == "smile" else "case_analysis"
            if intent != allowed_intent:
                json_response(self, 403, error_payload(agent_id, request_id, "intent_not_allowed"))
                return

            question_ok, question = sanitize_question(body["payload"].get("question"))
            if not question_ok.ok:
                json_response(self, 400, error_payload(agent_id, request_id, question_ok.reason))
                return

            try:
                if specialty == "smile":
                    tool_calls = [
                        {"name": "smile_overview", "arguments": {}},
                        {"name": "query_knowledge", "arguments": {"query": question}},
                    ]
                else:
                    tool_calls = [
                        {"name": "get_case_studies", "arguments": {}},
                        {"name": "query_knowledge", "arguments": {"query": question}},
                    ]

                tool_results = call_tools(tool_calls)
                excerpts = []
                highlights = []
                for result in tool_results:
                    snippet = str(result.get("text", ""))[:320]
                    excerpts.append({"tool": result["tool"], "ok": result.get("ok", False), "excerpt": snippet})
                    if snippet:
                        highlights.extend(_extract_points(snippet, max_points=2))

                response_payload = {
                    "request_id": request_id,
                    "from_agent": agent_id,
                    "status": "ok",
                    "data": {
                        "specialty": specialty,
                        "question": question,
                        "highlights": highlights[:5],
                        "evidence": excerpts,
                    },
                    "security": {
                        "blocked": False,
                        "policy": [
                            "strict_intent_allowlist",
                            "input_sanitization",
                            "caller_authentication",
                            "rate_limit",
                        ],
                    },
                }
                json_response(self, 200, response_payload)
            except LPIClientError as exc:
                json_response(self, 502, error_payload(agent_id, request_id, f"lpi_call_failed:{exc}"))

    return SpecialistHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a specialist agent server")
    parser.add_argument("--agent-id", required=True, choices=["smile-agent", "case-agent"])
    parser.add_argument("--specialty", required=True, choices=["smile", "case"])
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--card", required=True)
    parser.add_argument("--mesh-token", default="level4-shared-token")
    args = parser.parse_args()

    allowed_callers = {"orchestrator-agent": args.mesh_token}
    handler_cls = build_handler(
        agent_id=args.agent_id,
        specialty=args.specialty,
        card_path=Path(args.card),
        allowed_callers=allowed_callers,
    )

    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_cls)
    print(f"{args.agent_id} listening on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
