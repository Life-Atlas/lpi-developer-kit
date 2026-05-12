#!/usr/bin/env python3
"""
agent_b.py — SMILE analysis server

- takes a query
- runs SMILE + LPI analysis (via Ollama)
- returns structured JSON

runs on port 8001
"""

import json
import os

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from security import RateLimiter, sanitize_output, validate_input, verify_token


PORT = 8001
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

AGENT_CARD = {
    "name": "Agent B (SMILE Analyzer)",
    "version": "1.0.0",
    "description": "does SMILE + LPI analysis using local LLM",
    "capabilities": ["smile_analysis", "lpi_detection", "intent_classification"],
    "endpoint": f"http://localhost:{PORT}/analyze",
}

ALLOWED_OUTPUT_FIELDS = [
    "agent", "query", "smile", "lpi", "intent", "confidence", "summary",
]


app = FastAPI(title="Agent B")

rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


class AnalyzeRequest(BaseModel):
    query: str


# discovery endpoint
@app.get("/.well-known/agent.json", include_in_schema=False)
async def discovery():
    return JSONResponse(AGENT_CARD)


@app.post("/analyze")
async def analyze(request: Request, body: AnalyzeRequest):

    # basic auth check
    if not verify_token(request.headers.get("Authorization", "")):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # rate limit per IP
    if not rate_limiter.is_allowed(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests")

    # input validation
    ok, result = validate_input(body.query)
    if not ok:
        raise HTTPException(status_code=400, detail=result)

    clean_query = result

    # run analysis
    data = await run_analysis(clean_query)

    # only allow safe fields
    return JSONResponse(sanitize_output(data, ALLOWED_OUTPUT_FIELDS))


# main LLM call
async def run_analysis(query: str):

    prompt = f"""
Analyze this query using SMILE + LPI.

Query: "{query}"

Return ONLY valid JSON:

{{
  "smile": {{
    "structure": "...",
    "meaning": "...",
    "intent": "..."
  }},
  "lpi": {{
    "patterns": [],
    "complexity": "...",
    "sentiment": "...",
    "domain": "..."
  }},
  "intent": "...",
  "confidence": 0.0,
  "summary": "..."
}}
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            resp.raise_for_status()

            raw = resp.json().get("response", "{}")
            data = json.loads(raw)

    except Exception:
        # ollama failed or gave bad output
        print("[agent b] fallback used")
        data = fallback(query)

    data["agent"] = AGENT_CARD["name"]
    data["query"] = query

    return data


# simple fallback if LLM fails
def fallback(query: str):

    words = query.split()

    is_question = query.endswith("?") or (
        words and words[0].lower() in [
            "what", "why", "how", "when", "where", "who",
            "is", "are", "can", "do"
        ]
    )

    return {
        "smile": {
            "structure": "interrogative" if is_question else "declarative",
            "meaning": f"about: {query[:80]}",
            "intent": "info_request" if is_question else "statement",
        },
        "lpi": {
            "patterns": ["basic_pattern"],
            "complexity": "medium" if len(words) > 8 else "low",
            "sentiment": "neutral",
            "domain": "general",
        },
        "intent": "info_request" if is_question else "statement",
        "confidence": 0.4,
        "summary": "basic fallback analysis (LLM not available)",
    }


if __name__ == "__main__":
    print(f"[agent b] running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
