#!/usr/bin/env python3
"""Common protocol and security helpers for the Level 4 secure agent mesh."""

from __future__ import annotations

import json
import re
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Tuple

MAX_BODY_BYTES = 8 * 1024
MAX_QUESTION_CHARS = 320
MAX_HOPS = 3
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20

BLOCK_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"show\s+hidden\s+instructions", re.IGNORECASE),
    re.compile(r"/etc/passwd", re.IGNORECASE),
    re.compile(r"api[_\-]?key", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
]


@dataclass
class ValidationResult:
    ok: bool
    reason: str = ""


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_request_id() -> str:
    return str(uuid.uuid4())


def _looks_malicious(text: str) -> bool:
    return any(pattern.search(text) for pattern in BLOCK_PATTERNS)


def sanitize_question(raw: Any) -> Tuple[ValidationResult, str]:
    if not isinstance(raw, str):
        return ValidationResult(False, "question_must_be_string"), ""

    question = " ".join(raw.strip().split())
    if not question:
        return ValidationResult(False, "empty_question"), ""

    if len(question) > MAX_QUESTION_CHARS:
        return ValidationResult(False, "question_too_long"), ""

    if _looks_malicious(question):
        return ValidationResult(False, "prompt_injection_or_exfiltration_attempt"), ""

    return ValidationResult(True, ""), question


def check_rate_limit(rate_table: Dict[str, Deque[float]], client_key: str) -> ValidationResult:
    now = time.time()
    queue = rate_table[client_key]

    while queue and (now - queue[0]) > RATE_LIMIT_WINDOW_SECONDS:
        queue.popleft()

    if len(queue) >= RATE_LIMIT_MAX_REQUESTS:
        return ValidationResult(False, "rate_limit_exceeded")

    queue.append(now)
    return ValidationResult(True, "")


def default_rate_table() -> Dict[str, Deque[float]]:
    return defaultdict(deque)


def read_json_request(handler: Any) -> Tuple[ValidationResult, Dict[str, Any]]:
    content_length_raw = handler.headers.get("Content-Length", "0")
    try:
        content_length = int(content_length_raw)
    except ValueError:
        return ValidationResult(False, "invalid_content_length"), {}

    if content_length <= 0 or content_length > MAX_BODY_BYTES:
        return ValidationResult(False, "invalid_body_size"), {}

    raw = handler.rfile.read(content_length)
    try:
        body = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return ValidationResult(False, "invalid_json"), {}

    if not isinstance(body, dict):
        return ValidationResult(False, "json_must_be_object"), {}

    return ValidationResult(True, ""), body


def validate_trace(trace: Any) -> ValidationResult:
    if not isinstance(trace, dict):
        return ValidationResult(False, "trace_must_be_object")

    hop_count = trace.get("hop_count")
    max_hops = trace.get("max_hops", MAX_HOPS)

    if not isinstance(hop_count, int) or not isinstance(max_hops, int):
        return ValidationResult(False, "trace_hops_must_be_int")

    if max_hops < 1 or max_hops > MAX_HOPS:
        return ValidationResult(False, "max_hops_out_of_policy")

    if hop_count < 0 or hop_count > max_hops:
        return ValidationResult(False, "hop_limit_exceeded")

    return ValidationResult(True, "")


def validate_a2a_envelope(envelope: Dict[str, Any], expected_to_agent: str) -> ValidationResult:
    required_keys = {"request_id", "from_agent", "to_agent", "intent", "payload", "trace"}
    missing = required_keys - set(envelope.keys())
    if missing:
        return ValidationResult(False, f"missing_keys:{sorted(missing)}")

    if envelope["to_agent"] != expected_to_agent:
        return ValidationResult(False, "wrong_recipient")

    if not isinstance(envelope["request_id"], str) or not envelope["request_id"]:
        return ValidationResult(False, "invalid_request_id")

    if not isinstance(envelope["from_agent"], str) or not envelope["from_agent"]:
        return ValidationResult(False, "invalid_from_agent")

    if not isinstance(envelope["intent"], str) or not envelope["intent"]:
        return ValidationResult(False, "invalid_intent")

    if not isinstance(envelope["payload"], dict):
        return ValidationResult(False, "payload_must_be_object")

    return validate_trace(envelope["trace"])


def auth_ok(headers: Any, allowed_callers: Dict[str, str]) -> ValidationResult:
    caller = headers.get("X-Agent-Id", "")
    token = headers.get("X-Agent-Token", "")

    if caller not in allowed_callers:
        return ValidationResult(False, "caller_not_allowed")

    if token != allowed_callers[caller]:
        return ValidationResult(False, "invalid_agent_token")

    return ValidationResult(True, "")


def json_response(handler: Any, code: int, payload: Dict[str, Any]) -> None:
    encoded = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def error_payload(agent_id: str, request_id: str, reason: str) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "from_agent": agent_id,
        "status": "error",
        "error": {"code": reason, "timestamp": utc_timestamp()},
        "security": {"blocked": True, "reason": reason},
    }
