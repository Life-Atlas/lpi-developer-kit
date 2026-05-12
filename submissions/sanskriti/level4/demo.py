#!/usr/bin/env python3
"""Runs a local end-to-end demo of the secure agent mesh."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MESH_TOKEN = "level4-shared-token"


def wait_for_health(url: str, timeout_seconds: int = 15) -> None:
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Service did not become healthy: {url}")


def start_proc(args):
    return subprocess.Popen(
        [sys.executable] + args,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    smile = start_proc(
        [
            "specialist_agent.py",
            "--agent-id",
            "smile-agent",
            "--specialty",
            "smile",
            "--port",
            "8101",
            "--card",
            "agent_cards/smile-agent.json",
            "--mesh-token",
            MESH_TOKEN,
        ]
    )
    case = start_proc(
        [
            "specialist_agent.py",
            "--agent-id",
            "case-agent",
            "--specialty",
            "case",
            "--port",
            "8102",
            "--card",
            "agent_cards/case-agent.json",
            "--mesh-token",
            MESH_TOKEN,
        ]
    )
    orchestrator = start_proc(
        [
            "orchestrator_agent.py",
            "--port",
            "8100",
            "--card",
            "agent_cards/orchestrator-agent.json",
            "--mesh-token",
            MESH_TOKEN,
            "--specialists",
            "http://127.0.0.1:8101",
            "http://127.0.0.1:8102",
        ]
    )

    processes = [smile, case, orchestrator]
    try:
        wait_for_health("http://127.0.0.1:8101/healthz")
        wait_for_health("http://127.0.0.1:8102/healthz")
        wait_for_health("http://127.0.0.1:8100/healthz")

        payload = {
            "request_id": "demo-request-001",
            "question": "How should a manufacturing team start a digital twin rollout with low risk?",
        }
        result = post_json("http://127.0.0.1:8100/recommend", payload)

        print("=== DEMO RESULT ===")
        print(json.dumps(result, indent=2))
        print("=== END DEMO ===")
    finally:
        for proc in processes:
            proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
