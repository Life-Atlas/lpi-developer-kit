"""
security.py — Shared security middleware for the Level 4 agent mesh.

Defends against four attack surfaces:
  1. Prompt injection  — malicious inputs that try to override agent instructions
  2. Data exfiltration — inputs designed to leak system prompts or internal data
  3. Denial of service — inputs that cause infinite loops or resource exhaustion
  4. Privilege escalation — one agent making another do something out of scope

Every agent instantiates SecurityGuard with its own name and allowed tool list.
"""

import re
import signal
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# ── Attack 1: Prompt Injection Patterns ──────────────────────────────────────
# Classic patterns used to override system instructions.
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above|prior)\s+instructions",
    r"disregard\s+(your|the)\s+(instructions|system\s+prompt|guidelines)",
    r"you\s+are\s+now\s+(a\s+)?(?!an?\s+AI)",   # "you are now [something else]"
    r"override\s+(your|all|the)\s+(instructions|restrictions|guidelines)",
    r"jailbreak",
    r"DAN\b",                                    # "Do Anything Now" jailbreak
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if\s+you\s+are|a\s+)",
    r"forget\s+(your|all|the)\s+(instructions|system|training)",
    r"sudo\s+",
    r"</?(system|user|assistant|human)\s*>",     # XML prompt injection tags
    r"\[\s*SYSTEM\s*\]",
    r"new\s+instruction[s]?\s*:",
]

# ── Attack 2: Exfiltration Triggers ─────────────────────────────────────────
# Phrases that probe agents to reveal internal configuration.
EXFIL_PATTERNS = [
    r"(repeat|print|show|reveal|tell\s+me)\s+(your|the)\s+system\s+prompt",
    r"what\s+(are\s+your|is\s+your)\s+(instructions|system\s+prompt|config)",
    r"(show|print|output)\s+(your\s+)?(full\s+)?(prompt|instructions|config)",
    r"(leak|dump|expose)\s+(the\s+)?(system|internal|hidden)",
]

# ── Attack 2: Output Leak Guard ──────────────────────────────────────────────
# These strings must never appear in agent output — they would signal the
# system prompt or internal architecture was leaked.
FORBIDDEN_OUTPUT_SUBSTRINGS = [
    "system prompt",
    "you are agent",
    "you are a specialized",
    "allowed_tools",
    "SecurityGuard",
    "REPO_ROOT",
    "LPI_CMD",
]

# ── Limits (DoS prevention) ──────────────────────────────────────────────────
MAX_INPUT_CHARS   = 600    # hard limit on user/inter-agent input length
MAX_TOKENS        = 300    # passed to Ollama; prevents runaway generation
TIMEOUT_SECONDS   = 120    # per LLM call


class SecurityGuard:
    """
    One instance per agent. Holds the agent's identity and its allowed tool list.
    All public methods raise SecurityError on violation — callers must catch it.
    """

    def __init__(self, agent_name: str, allowed_tools: list[str]):
        self.agent_name   = agent_name
        self.allowed_tools = set(allowed_tools)   # privilege list

    # ── 1. Input sanitization ────────────────────────────────────────────────

    def sanitize_input(self, text: str) -> str:
        """
        Strip injection and exfiltration attempts from user/inter-agent input.
        Raises SecurityError if a pattern is detected so the caller can return
        a safe 400-style error without ever touching the LLM.
        """
        if len(text) > MAX_INPUT_CHARS:
            raise SecurityError(
                f"Input too long ({len(text)} chars, max {MAX_INPUT_CHARS}). "
                "Possible DoS attempt."
            )

        lowered = text.lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE):
                logger.warning(
                    "[%s] Prompt injection blocked. Pattern: %s | Input: %.80s",
                    self.agent_name, pattern, text
                )
                raise SecurityError("Prompt injection attempt detected and blocked.")

        for pattern in EXFIL_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE):
                logger.warning(
                    "[%s] Exfiltration probe blocked. Pattern: %s | Input: %.80s",
                    self.agent_name, pattern, text
                )
                raise SecurityError("Data exfiltration attempt detected and blocked.")

        # Sanitize angle brackets to prevent XML-based injection surviving into prompts
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        return text

    # ── 2. Output leak detection ─────────────────────────────────────────────

    def scrub_output(self, output: str) -> str:
        """
        Check LLM output for internal configuration leaks.
        Redacts the offending line rather than crashing the whole response.
        """
        lines = output.split("\n")
        clean = []
        for line in lines:
            if any(s.lower() in line.lower() for s in FORBIDDEN_OUTPUT_SUBSTRINGS):
                logger.warning(
                    "[%s] Output leak detected and redacted: %.80s",
                    self.agent_name, line
                )
                clean.append("[REDACTED — internal configuration]")
            else:
                clean.append(line)
        return "\n".join(clean)

    # ── 3. Tool privilege check ──────────────────────────────────────────────

    def check_tool_permission(self, tool_name: str) -> None:
        """
        Each agent has a fixed set of tools it may call.
        Raises SecurityError if the requested tool is outside that set.
        Prevents privilege escalation between agents.
        """
        if tool_name not in self.allowed_tools:
            logger.warning(
                "[%s] Privilege escalation blocked — tool '%s' not in allowed set %s",
                self.agent_name, tool_name, self.allowed_tools
            )
            raise SecurityError(
                f"Tool '{tool_name}' is not permitted for agent '{self.agent_name}'."
            )

    # ── 4. Timeout decorator (DoS prevention) ───────────────────────────────

    def with_timeout(self, func, *args, timeout: int = TIMEOUT_SECONDS, **kwargs):
        """
        Runs func(*args, **kwargs) with a hard timeout.
        Works on Unix via SIGALRM; on Windows uses threading fallback.
        """
        try:
            # Unix path — SIGALRM is the cleanest option
            def _handler(signum, frame):
                raise TimeoutError(f"LLM call timed out after {timeout}s.")

            signal.signal(signal.SIGALRM, _handler)
            signal.alarm(timeout)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)   # cancel alarm
            return result

        except AttributeError:
            # Windows: SIGALRM not available — using threading.Timer
            import threading
            result_holder = [None]
            error_holder  = [None]

            def _run():
                try:
                    result_holder[0] = func(*args, **kwargs)
                except Exception as e:
                    error_holder[0] = e

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout)
            if t.is_alive():
                raise TimeoutError(f"LLM call timed out after {timeout}s (Windows).")
            if error_holder[0]:
                raise error_holder[0]
            return result_holder[0]


class SecurityError(Exception):
    """Raised by SecurityGuard when a security violation is detected."""
    pass
