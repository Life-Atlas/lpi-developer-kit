"""
case_agent.py — simple case example server

returns a few real-world examples based on keywords
runs on port 8002
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from security import RateLimiter, sanitize_output, validate_input, verify_token


PORT = 8002

AGENT_CARD = {
    "name": "Case Agent",
    "version": "1.0",
    "description": "returns simple real-world examples",
    "endpoint": f"http://localhost:{PORT}/cases",
}

ALLOWED_OUTPUT_FIELDS = ["agent", "query", "cases"]


# small dataset (kept intentionally simple)
CASE_DB = [
    {
        "title": "Prompt Injection in LLM Apps",
        "summary": "Attackers manipulate AI using crafted inputs.",
        "keywords": ["prompt", "ai", "llm", "injection"],
    },
    {
        "title": "Uber MFA Fatigue Attack",
        "summary": "Repeated login prompts tricked user into approving access.",
        "keywords": ["mfa", "login", "security", "attack"],
    },
    {
        "title": "AutoGPT Multi-Agent System",
        "summary": "Multiple agents working together to complete tasks.",
        "keywords": ["agent", "multi-agent", "ai", "task"],
    },
    {
        "title": "Twitter Rate Limit Bypass",
        "summary": "API misuse allowed large-scale data scraping.",
        "keywords": ["api", "rate", "data", "security"],
    },
]


def find_cases(query):
    q = query.lower()
    results = []

    for case in CASE_DB:
        for kw in case["keywords"]:
            if kw in q:
                results.append({
                    "title": case["title"],
                    "summary": case["summary"],
                })
                break

    # fallback if nothing matches
    if not results:
        results = CASE_DB[:2]

    return results


app = FastAPI(title="Case Agent")

rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


class CaseRequest(BaseModel):
    query: str


@app.get("/.well-known/agent.json", include_in_schema=False)
async def discovery():
    return JSONResponse(AGENT_CARD)


@app.post("/cases")
async def get_cases(request: Request, body: CaseRequest):

    # auth
    if not verify_token(request.headers.get("Authorization", "")):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # rate limit
    if not rate_limiter.is_allowed(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests")

    # input validation
    ok, result = validate_input(body.query)
    if not ok:
        raise HTTPException(status_code=400, detail=result)

    query = result

    cases = find_cases(query)

    response = {
        "agent": AGENT_CARD["name"],
        "query": query,
        "cases": cases,
    }

    return JSONResponse(sanitize_output(response, ALLOWED_OUTPUT_FIELDS))


if __name__ == "__main__":
    print("[case agent] running on 8002")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
