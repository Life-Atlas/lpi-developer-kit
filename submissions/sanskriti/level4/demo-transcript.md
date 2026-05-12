# Demo Transcript - Secure Agent Mesh

This file records sample output from running:

```bash
python3 submissions/sanskriti/level4/demo.py
python3 submissions/sanskriti/level4/security_audit.py
```

## Demo Run (Excerpt)

```text
=== DEMO RESULT ===
{
  "request_id": "demo-request-001",
  "from_agent": "orchestrator-agent",
  "status": "ok",
  "data": {
    "question": "How should a manufacturing team start a digital twin rollout with low risk?",
    "discovered_agents": [
      "smile-agent",
      "case-agent"
    ],
    "specialist_responses": [
      {
        "from_agent": "smile-agent",
        "status": "ok"
      },
      {
        "from_agent": "case-agent",
        "status": "ok"
      }
    ],
    "recommendation": {
      "summary": "Blend SMILE framework steps with case-study patterns to reduce implementation risk.",
      "confidence": "medium"
    }
  }
}
=== END DEMO ===
```

## Security Audit Run (Excerpt)

```text
Security audit passed 6/6 tests
[
  {"name": "safe_query", "pass": true},
  {"name": "prompt_injection_block", "pass": true},
  {"name": "data_exfiltration_block", "pass": true},
  {"name": "dos_size_limit", "pass": true},
  {"name": "privilege_escalation_block", "pass": true},
  {"name": "hop_limit_block", "pass": true}
]
```

If your local run differs, re-run after `npm run build` and ensure ports 8100/8101/8102 are free.
