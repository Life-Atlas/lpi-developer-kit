"""
Shared security utilities for the Level 4 Secure Agent Mesh.

Covers:
  - Prompt injection detection (OWASP LLM01)
  - Input length caps (DoS prevention)
  - Inter-agent schema validation (privilege escalation prevention)
"""

import re

MAX_INPUT_LEN = 500

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+",
    r"new\s+(system|role|persona|instructions?)",
    r"<\|system\|>",
    r"\[INST\]",
    r"###\s*system",
    r"\bdisregard\b",
    r"do\s+not\s+follow",
    r"\boverride\b",
    r"forget\s+(everything|all|previous)",
    r"act\s+as\s+(if\s+you\s+are|a\s+)",
    r"jailbreak",
    r"DAN\s+mode",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def sanitize(text: str, field: str = "input") -> str:
    """
    Validate and clean a user-supplied string.
    Raises ValueError on injection attempt or excessive length.
    """
    if not isinstance(text, str):
        raise ValueError(f"{field} must be a string")
    if len(text) > MAX_INPUT_LEN:
        raise ValueError(
            f"{field} exceeds {MAX_INPUT_LEN} chars (got {len(text)}). "
            "Truncate your input."
        )
    for pattern in _COMPILED:
        if pattern.search(text):
            raise ValueError(
                f"[SECURITY] Rejected: potential prompt injection detected in '{field}'"
            )
    return text.strip()


def validate_plan_schema(data: dict) -> None:
    """
    Validate that an inter-agent plan message has the required structure.
    Prevents Agent B from accepting arbitrary/malicious payloads from Agent A.
    """
    if not isinstance(data, dict):
        raise ValueError("Plan must be a JSON object")

    required = {"project", "phases", "tools_used"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Plan schema missing required fields: {missing}")

    project = data["project"]
    for field in ("industry", "usecase", "constraints"):
        if field not in project or not isinstance(project[field], str):
            raise ValueError(f"plan.project.{field} must be a non-empty string")

    if not isinstance(data["phases"], list) or len(data["phases"]) == 0:
        raise ValueError("plan.phases must be a non-empty list")

    for i, phase in enumerate(data["phases"]):
        if not isinstance(phase, dict):
            raise ValueError(f"plan.phases[{i}] must be an object")
        if "phase" not in phase:
            raise ValueError(f"plan.phases[{i}] missing 'phase' field")

    if not isinstance(data["tools_used"], list):
        raise ValueError("plan.tools_used must be a list")


def validate_critique_schema(data: dict) -> None:
    """Validate that a critique response has the required structure."""
    if not isinstance(data, dict):
        raise ValueError("Critique must be a JSON object")

    required = {"verdict", "risk_score", "critiques", "tools_used"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Critique schema missing required fields: {missing}")

    valid_verdicts = {"proceed", "proceed_with_caution", "reconsider"}
    if data["verdict"] not in valid_verdicts:
        raise ValueError(f"verdict must be one of {valid_verdicts}")

    if not isinstance(data["risk_score"], (int, float)):
        raise ValueError("risk_score must be numeric")
    if not (1 <= data["risk_score"] <= 10):
        raise ValueError("risk_score must be between 1 and 10")

    if not isinstance(data["critiques"], list):
        raise ValueError("critiques must be a list")
