import re


# ---- 1. PROMPT INJECTION DEFENSE ----
def sanitize_input(text):
    blocked_patterns = [
        "ignore previous instructions",
        "system prompt",
        "reveal hidden",
        "bypass",
        "override",
        "act as",
        "jailbreak"
    ]

    text_lower = text.lower()

    for pattern in blocked_patterns:
        if pattern in text_lower:
            raise ValueError(f"Blocked malicious pattern: {pattern}")

    return text


# ---- 2. DATA EXFILTRATION DEFENSE ----
def prevent_data_leak(text):
    sensitive_keywords = [
        "system prompt",
        "internal instructions",
        "hidden policy",
        "tool schema"
    ]

    text_lower = text.lower()

    for keyword in sensitive_keywords:
        if keyword in text_lower:
            return "[REDACTED: Sensitive content blocked]"

    return text


# ---- 3. DOS DEFENSE ----
def validate_length(text, max_length=500):
    if len(text) > max_length:
        raise ValueError("Input too long — possible DoS attack")
    return text


# ---- 4. PRIVILEGE ESCALATION DEFENSE ----
def validate_agent_call(data):
    if "grounding_data" not in data:
        raise ValueError("Missing grounding data")

    if not isinstance(data["grounding_data"], dict):
        raise ValueError("Invalid grounding data format")

    return True
