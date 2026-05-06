#!/usr/bin/env python3
"""
agent_a.py — orchestrator (client + combiner)

- discovers agents
- sends query to both
- merges output
- prints nicely

run:
  python agent_a.py "your query"
"""

import asyncio
import json
import sys
import textwrap
from datetime import datetime

import httpx

from security import auth_headers, validate_input

AGENT_B_URL = "http://localhost:8001"
CASE_AGENT_URL = "http://localhost:8002"


# try to fetch agent card
async def discover_agent(client, base_url):
    try:
        resp = await client.get(
            f"{base_url}/.well-known/agent.json",
            headers=auth_headers(),
            timeout=5.0,
        )
        resp.raise_for_status()
        card = resp.json()
        print(f"  → Found agent: {card.get('name', base_url)}")
        return card
    except Exception as e:
        print(f"  → Couldn't reach {base_url} ({e})")
        return None


async def discover_all(client):
    print("\n[Agent A] starting discovery...")
    print("-" * 40)

    a, b = await asyncio.gather(
        discover_agent(client, AGENT_B_URL),
        discover_agent(client, CASE_AGENT_URL),
    )
    return a, b


# call smile agent (agent b)
async def call_agent_b(client, query):
    try:
        resp = await client.post(
            f"{AGENT_B_URL}/analyze",
            json={"query": query},
            headers={**auth_headers(), "Content-Type": "application/json"},
            timeout=40.0,  # LPI can be slow sometimes
        )
        resp.raise_for_status()
        return {"ok": True, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}  # might refine later


# call case agent
async def call_case_agent(client, query):
    try:
        resp = await client.post(
            f"{CASE_AGENT_URL}/cases",
            json={"query": query},
            headers={**auth_headers(), "Content-Type": "application/json"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return {"ok": True, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# combine both responses
def combine_responses(query, smile_result, case_result):

    combined = {
        "meta": {
            "orchestrator": "Agent A",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "query": query,
        },
        "analysis": None,
        "cases": None,
        "synthesis": "",
        "errors": [],
    }

    # smile agent part
    if smile_result["ok"]:
        d = smile_result["data"]
        combined["analysis"] = {
            "intent": d.get("intent", "unknown"),
            "confidence": d.get("confidence", 0.0),
            "summary": d.get("summary", ""),
            "smile": d.get("smile", {}),
            "lpi": d.get("lpi", {}),
        }
    else:
        combined["errors"].append(f"agent b error: {smile_result['error']}")

    # case agent part
    if case_result["ok"]:
        d = case_result["data"]
        combined["cases"] = {
            "domain": d.get("domain_hint", "general"),
            "items": d.get("cases", []),
        }
    else:
        combined["errors"].append(f"case agent error: {case_result['error']}")

    combined["synthesis"] = build_synthesis(combined)

    return combined


def build_synthesis(combined):
    parts = []

    a = combined.get("analysis")
    c = combined.get("cases")

    if a:
        intent = a.get("intent", "unknown")
        conf = a.get("confidence", 0.0)
        meaning = a.get("smile", {}).get("meaning", "")

        parts.append(
            f"Seems like this is about '{intent}' ({conf:.0%} confidence). "
            f"Basically: {meaning}"
        )

    if c:
        items = c.get("items", [])
        if items:
            titles = ", ".join(x["title"] for x in items[:2])
            parts.append(f"Similar real-world cases include {titles}.")
        else:
            parts.append("Didn't find strong real-world matches.")

    if combined.get("errors"):
        parts.append("Some parts of the system didn’t respond properly.")

    # small human touch
    parts.append("Try applying one idea consistently for a few days and see what changes.")

    return " ".join(parts)


# just prints nicely
def print_report(data):

    print("\n" + "=" * 50)
    print("Combined agent output")
    print("=" * 50)

    print(f"Query: {data['meta']['query']}")
    print(f"Time : {data['meta']['timestamp']}")

    print("\n--- Analysis ---")
    if data["analysis"]:
        a = data["analysis"]
        print(f"Intent     : {a['intent']}")
        print(f"Confidence : {a['confidence']:.0%}")
        print(f"Summary    : {a['summary']}")
    else:
        print("no response from agent b")

    print("\n--- Cases ---")
    if data["cases"]:
        for i, case in enumerate(data["cases"]["items"], 1):
            print(f"{i}. {case['title']} ({case['year']})")
            print(f"   {case['summary']}")
    else:
        print("no cases found")

    print("\n--- Final ---")
    print(textwrap.fill(data["synthesis"], width=60))

    if data["errors"]:
        print("\nissues:")
        for e in data["errors"]:
            print("-", e)

    print("=" * 50 + "\n")


async def run(query):

    print(f"\n[Agent A] got query: {query}")

    ok, clean = validate_input(query)
    if not ok:
        print("input rejected:", clean)
        return

    async with httpx.AsyncClient() as client:

        await discover_all(client)

        print("\n[Agent A] sending to both agents...\n")

        r1, r2 = await asyncio.gather(
            call_agent_b(client, clean),
            call_case_agent(client, clean),
        )

        print("  → smile agent replied")
        print("  → case agent replied")

        combined = combine_responses(clean, r1, r2)

        print_report(combined)

        print("raw json:")
        print(json.dumps(combined, indent=2))


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("enter query (ctrl+c to exit)")
        try:
            query = input("> ")
        except KeyboardInterrupt:
            print("\nbye")
            return

    if not query:
        print("empty input")
        return

    asyncio.run(run(query))


if __name__ == "__main__":
    main()
