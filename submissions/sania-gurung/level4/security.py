"""
Shared security utilities for the Level 4 Secure Agent Mesh.

Covers:
  - Prompt injection detection (OWASP LLM01)
  - Data exfiltration probe detection (OWASP LLM06)
  - Input length caps (DoS prevention, OWASP LLM04)
  - Inter-agent schema validation (privilege escalation prevention, OWASP LLM08)
  - Inter-agent string re-sanitization (compromised-agent defence)
"""

import re

MAX_USER_INPUT_LEN = 400
MAX_FINDING_LEN = 150
VALID_DIMENSIONS = {"data_maturity", "stakeholder_alignment", "technical_infrastructure"}
VALID_GAP_SEVERITY = {"low", "medium", "high"}

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
    r"\bjailbreak\b",
    r"DAN\s+mode",
    r"developer\s+mode",
    r"repeat\s+(your|the)\s+(system|prompt|instructions)",
    r"print\s+(your|the)\s+(system|prompt)",
    r"what\s+(are|is)\s+your\s+(instructions|system|prompt)",
    r"\breveal\s+(your|the)\b",
    r"/etc/passwd",
    r"\.\./",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


class SecurityError(ValueError):
    pass


def sanitize_input(text: str, field: str = "input", max_len: int = MAX_USER_INPUT_LEN) -> str:
    """
    Validate and clean a string.
    Raises SecurityError on injection attempt or excessive length.
    """
    if not isinstance(text, str):
        raise SecurityError(f"{field} must be a string")
    if len(text) > max_len:
        raise SecurityError(
            f"[BLOCKED] {field} exceeds {max_len} chars (got {len(text)}). Shorten your input."
        )
    for pattern in _COMPILED:
        if pattern.search(text):
            raise SecurityError(
                f"[BLOCKED] Input rejected: potential prompt injection detected in '{field}'"
            )
    return text.strip()


def sanitize_interagent_strings(data: dict, fields: list) -> dict:
    """
    Re-sanitize specific string fields inside an inter-agent payload.
    Defends against a compromised Agent A passing injection via the schema.
    Uses MAX_FINDING_LEN for sub-fields and MAX_USER_INPUT_LEN for description.
    """
    for field_path in fields:
        parts = field_path.split(".")
        obj = data
        try:
            for part in parts[:-1]:
                if part.isdigit():
                    obj = obj[int(part)]
                else:
                    obj = obj[part]
            key = parts[-1]
            if key.isdigit():
                idx = int(key)
                if isinstance(obj[idx], str):
                    limit = MAX_USER_INPUT_LEN if "description" in field_path else MAX_FINDING_LEN
                    obj[idx] = sanitize_input(obj[idx], field=field_path, max_len=limit)
            elif isinstance(obj.get(key), str):
                limit = MAX_USER_INPUT_LEN if "description" in field_path else MAX_FINDING_LEN
                obj[key] = sanitize_input(obj[key], field=field_path, max_len=limit)
        except (KeyError, IndexError, TypeError):
            pass
    return data


def validate_readiness_schema(data: dict) -> None:
    """
    Validate a ReadinessReport before Agent B processes it.
    Prevents Agent B accepting arbitrary/malicious payloads.
    """
    if not isinstance(data, dict):
        raise SecurityError("ReadinessReport must be a JSON object")

    required = {"schema_version", "request_id", "project", "readiness_dimensions",
                "overall_readiness_score", "top_gaps", "recommended_starting_phase", "tools_used"}
    missing = required - set(data.keys())
    if missing:
        raise SecurityError(f"ReadinessReport missing required fields: {missing}")

    project = data["project"]
    if not isinstance(project, dict) or "description" not in project:
        raise SecurityError("ReadinessReport.project must have a 'description' field")

    dims = data["readiness_dimensions"]
    if not isinstance(dims, list) or len(dims) == 0:
        raise SecurityError("readiness_dimensions must be a non-empty list")
    if len(dims) > 5:
        raise SecurityError("readiness_dimensions must have at most 5 entries")

    for i, dim in enumerate(dims):
        if not isinstance(dim, dict):
            raise SecurityError(f"readiness_dimensions[{i}] must be an object")
        for req_field in ("dimension", "score", "finding", "evidence_source", "gap_severity"):
            if req_field not in dim:
                raise SecurityError(f"readiness_dimensions[{i}] missing '{req_field}'")
        if dim["dimension"] not in VALID_DIMENSIONS:
            raise SecurityError(f"readiness_dimensions[{i}].dimension must be one of {VALID_DIMENSIONS}")
        if not isinstance(dim["score"], int) or not (1 <= dim["score"] <= 5):
            raise SecurityError(f"readiness_dimensions[{i}].score must be int 1-5")
        if not isinstance(dim["finding"], str) or len(dim["finding"]) > MAX_FINDING_LEN:
            raise SecurityError(f"readiness_dimensions[{i}].finding must be str <= {MAX_FINDING_LEN} chars")
        if dim["gap_severity"] not in VALID_GAP_SEVERITY:
            raise SecurityError(f"readiness_dimensions[{i}].gap_severity must be one of {VALID_GAP_SEVERITY}")

    overall = data["overall_readiness_score"]
    if not isinstance(overall, int) or not (1 <= overall <= 5):
        raise SecurityError("overall_readiness_score must be int 1-5")

    if not isinstance(data["top_gaps"], list):
        raise SecurityError("top_gaps must be a list")
    if not isinstance(data["tools_used"], list):
        raise SecurityError("tools_used must be a list")


def validate_roadmap_schema(data: dict) -> None:
    """Validate a SMILERoadmap output before the orchestrator renders it."""
    if not isinstance(data, dict):
        raise SecurityError("SMILERoadmap must be a JSON object")

    required = {"schema_version", "request_id", "gap_addressed", "phases",
                "first_week_actions", "tools_used"}
    missing = required - set(data.keys())
    if missing:
        raise SecurityError(f"SMILERoadmap missing required fields: {missing}")

    if not isinstance(data["phases"], list) or len(data["phases"]) == 0:
        raise SecurityError("phases must be a non-empty list")

    for i, phase in enumerate(data["phases"]):
        if not isinstance(phase, dict):
            raise SecurityError(f"phases[{i}] must be an object")
        for req_field in ("phase_slug", "phase_name", "priority", "addresses_gap",
                          "immediate_actions", "evidence_source"):
            if req_field not in phase:
                raise SecurityError(f"phases[{i}] missing '{req_field}'")
        if not isinstance(phase["priority"], int):
            raise SecurityError(f"phases[{i}].priority must be int")

    if not isinstance(data["first_week_actions"], list):
        raise SecurityError("first_week_actions must be a list")
    if not isinstance(data["tools_used"], list):
        raise SecurityError("tools_used must be a list")
