"""
security.py — shared utilities for the agent mesh

handles:
- input validation
- simple injection checks
- token auth
- rate limiting
- output filtering
"""

import os
import re
import time
from collections import defaultdict


AGENT_TOKEN = os.getenv("AGENT_TOKEN", "mesh-secret-token-2024")
MAX_INPUT_LENGTH = 500


# quick patterns for obvious injection attempts (not exhaustive)
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+(a\s+)?",
    r"\bsystem\s*:",
    r"<\s*script[\s>]",
    r"\bjailbreak\b",
    r"forget\s+(your|all)\s+",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if\s+you\s+are|a\s+)",
    r"do\s+anything\s+now",
    r"developer\s+mode",
]

_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


# basic input validation
def validate_input(text: str):
    if not text or not isinstance(text, str):
        return False, "invalid input"

    text = text.strip()

    if not text:
        return False, "empty input"

    if len(text) > MAX_INPUT_LENGTH:
        return False, "input too long"

    # remove weird control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", text).strip()

    if not cleaned:
        return False, "invalid characters"

    # check injection patterns
    for p in _patterns:
        if p.search(cleaned):
            return False, "blocked: suspicious input"

    return True, cleaned


# simple bearer token check
def verify_token(auth_header: str):
    if not auth_header:
        return False

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False

    return parts[1] == AGENT_TOKEN


def auth_headers():
    return {"Authorization": f"Bearer {AGENT_TOKEN}"}


# remove any fields we don't want to expose
def sanitize_output(data, allowed_fields):
    return {k: v for k, v in data.items() if k in allowed_fields}


# very simple in-memory rate limiter
class RateLimiter:

    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._log = defaultdict(list)

    def is_allowed(self, client_ip):

        now = time.monotonic()
        cutoff = now - self.window

        # remove old entries
        self._log[client_ip] = [
            t for t in self._log[client_ip] if t > cutoff
        ]

        if len(self._log[client_ip]) >= self.max_requests:
            return False

        self._log[client_ip].append(now)
        return True
