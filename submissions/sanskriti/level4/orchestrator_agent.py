#!/usr/bin/env python3
"""Orchestrator agent: discovers specialist agents and fuses their outputs."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

from mesh_common import (
    MAX_HOPS,
    auth_ok,
    check_rate_limit,
    default_rate_table,
    error_payload,
    json_response,
    new_request_id,
    read_json_request,
    sanitize_question,
)


def _http_json_get(url: str, timeout: int = 3) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_json_post(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int = 12) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for key, value in headers.items():
        req.add_header(key, value)

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def discover_agents(base_urls: List[str]) -> Dict[str, Dict[str, Any]]:
    discovered: Dict[str, Dict[str, Any]] = {}
    for base in base_urls:
        card_url = f"{base}/.well-known/agent.json"
        try:
            card = _http_json_get(card_url)
            agent_id = card.get("name")
            if not isinstance(agent_id, str):
                continue
            discovered[agent_id] = {"base_url": base, "card": card}
        except Exception:
            continue
    return discovered


def build_handler(
    orchestrator_id: str,
    card_path: Path,
    specialist_urls: List[str],
    mesh_token: str,
    allowed_callers: Dict[str, str],
):
    rate_table = default_rate_table()
    with card_path.open("r", encoding="utf-8") as f:
        card = json.load(f)

    class OrchestratorHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/.well-known/agent.json":
                json_response(self, 200, card)
                return
            if self.path == "/healthz":
                peers = discover_agents(specialist_urls)
                json_response(self, 200, {"status": "ok", "agent": orchestrator_id, "peers": list(peers.keys())})
                return
            json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:
            if self.path == "/a2a/recommend":
                auth_check = auth_ok(self.headers, allowed_callers)
                if not auth_check.ok:
                    json_response(self, 403, error_payload(orchestrator_id, "unknown", auth_check.reason))
                    return
            elif self.path != "/recommend":
                json_response(self, 404, {"error": "not_found"})
                return

            rate_check = check_rate_limit(rate_table, self.client_address[0])
            if not rate_check.ok:
                json_response(self, 429, error_payload(orchestrator_id, "unknown", rate_check.reason))
                return

            body_ok, body = read_json_request(self)
            if not body_ok.ok:
                json_response(self, 400, error_payload(orchestrator_id, "unknown", body_ok.reason))
                return

            request_id = str(body.get("request_id", new_request_id()))
            question_ok, question = sanitize_question(body.get("question"))
            if not question_ok.ok:
                json_response(self, 400, error_payload(orchestrator_id, request_id, question_ok.reason))
                return

            peers = discover_agents(specialist_urls)
            required = ["smile-agent", "case-agent"]
            missing = [peer for peer in required if peer not in peers]
            if missing:
                json_response(self, 503, error_payload(orchestrator_id, request_id, f"missing_peers:{missing}"))
                return

            specialist_calls = [
                {
                    "peer_id": "smile-agent",
                    "intent": "smile_analysis",
                },
                {
                    "peer_id": "case-agent",
                    "intent": "case_analysis",
                },
            ]

            specialist_responses = []
            for call in specialist_calls:
                peer = peers[call["peer_id"]]
                envelope = {
                    "request_id": request_id,
                    "from_agent": orchestrator_id,
                    "to_agent": call["peer_id"],
                    "intent": call["intent"],
                    "payload": {"question": question},
                    "trace": {"hop_count": 1, "max_hops": MAX_HOPS},
                }
                try:
                    result = _http_json_post(
                        f"{peer['base_url']}/a2a/query",
                        envelope,
                        headers={
                            "X-Agent-Id": orchestrator_id,
                            "X-Agent-Token": mesh_token,
                        },
                    )
                    specialist_responses.append(result)
                except urllib.error.HTTPError as exc:
                    specialist_responses.append(
                        {
                            "request_id": request_id,
                            "from_agent": call["peer_id"],
                            "status": "error",
                            "error": {"code": f"http_error_{exc.code}"},
                        }
                    )
                except Exception as exc:
                    specialist_responses.append(
                        {
                            "request_id": request_id,
                            "from_agent": call["peer_id"],
                            "status": "error",
                            "error": {"code": f"network_error:{exc}"},
                        }
                    )

            smile_data = next((x.get("data", {}) for x in specialist_responses if x.get("from_agent") == "smile-agent"), {})
            case_data = next((x.get("data", {}) for x in specialist_responses if x.get("from_agent") == "case-agent"), {})

            actions = []
            for point in smile_data.get("highlights", [])[:2]:
                actions.append(f"Methodology action: {point}")
            for point in case_data.get("highlights", [])[:2]:
                actions.append(f"Case-grounded action: {point}")

            recommendation = {
                "summary": "Blend SMILE framework steps with case-study patterns to reduce implementation risk.",
                "actions": actions[:4],
                "confidence": "medium",
            }

            response = {
                "request_id": request_id,
                "from_agent": orchestrator_id,
                "status": "ok",
                "data": {
                    "question": question,
                    "discovered_agents": list(peers.keys()),
                    "specialist_responses": specialist_responses,
                    "recommendation": recommendation,
                },
                "security": {
                    "blocked": False,
                    "policy": [
                        "peer_discovery_via_agent_cards",
                        "strict_payload_schema",
                        "authenticated_a2a_calls",
                        "hop_limit_enforced",
                    ],
                },
            }
            json_response(self, 200, response)

    return OrchestratorHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run orchestrator agent")
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--card", required=True)
    parser.add_argument(
        "--specialists",
        nargs="+",
        default=["http://127.0.0.1:8101", "http://127.0.0.1:8102"],
    )
    parser.add_argument("--mesh-token", default="level4-shared-token")
    args = parser.parse_args()

    handler_cls = build_handler(
        orchestrator_id="orchestrator-agent",
        card_path=Path(args.card),
        specialist_urls=args.specialists,
        mesh_token=args.mesh_token,
        allowed_callers={"demo-client": args.mesh_token},
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_cls)
    print(f"orchestrator-agent listening on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
