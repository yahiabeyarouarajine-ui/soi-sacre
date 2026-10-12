"""Soi Sacré – Rituel du jour: API.  Run: uvicorn main:app --reload"""
import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()

import guardrails  # noqa: E402
import llm  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("soisacre")

app = FastAPI(title="Soi Sacré – Rituel du jour", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class RitualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    energy: Literal["epuisee", "fatiguee", "ca_va", "pleine_energie"]
    time_minutes: Literal[2, 5, 10]
    weighs: List[Literal[
        "surcharge_mentale", "manque_de_temps", "culpabilite_de_me_poser",
        "fatigue_physique", "autre",
    ]] = Field(default_factory=list, max_length=5)
    free_text: Optional[str] = Field(default=None, max_length=150)
    desire: Literal["douceur_beaute", "respiration_calme", "recentrage", "energie_motivation"]
    language: Literal["fr", "en"] = "fr"


# ------------------------------------------------------------ simple rate limit
_hits: dict[str, deque] = defaultdict(deque)


def _rate_limit(request: Request) -> None:
    limit = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status_code=429, detail="Prends un instant, puis réessaie dans une minute.")
    q.append(now)


# ------------------------------------------------------------ friendly errors
@app.exception_handler(RequestValidationError)
async def _validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Quelque chose n'a pas pu être lu. Peux-tu réessayer ?"},
    )


@app.exception_handler(HTTPException)
async def _http_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "message": str(exc.detail)})


# ------------------------------------------------------------ routes
@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/ritual")
def create_ritual(req: RitualRequest, request: Request):
    _rate_limit(request)
    data = req.model_dump()
    lang = data["language"]

    # Layer 2: distress pre-check, before any LLM call
    if guardrails.check_distress(data.get("free_text")):
        log.info("status=care source=precheck")
        return JSONResponse(guardrails.care_response(lang), headers={"X-Source": "precheck"})

    # Layers 3-4: LLM + output validation, one retry
    for attempt in (1, 2):
        try:
            out = llm.generate(data)
        except Exception as e:
            log.warning("attempt=%s llm error: %s", attempt, type(e).__name__)
            continue
        if isinstance(out, dict) and out.get("status") == "care":
            log.info("status=care source=llm")
            return JSONResponse(guardrails.care_response(lang), headers={"X-Source": "llm"})
        problems = guardrails.validate_ritual(out, data["time_minutes"])
        if not problems:
            log.info("status=ritual source=llm attempt=%s", attempt)
            return JSONResponse(out, headers={"X-Source": "llm"})
        log.warning("attempt=%s invalid output: %s", attempt, "; ".join(problems))

    # Layer 5: pre-written fallback, never a technical error
    log.info("status=ritual source=fallback")
    return JSONResponse(guardrails.fallback_ritual(data["time_minutes"], lang), headers={"X-Source": "fallback"})


# Plan B test page (added later): served from ./static/index.html
_static = Path(__file__).with_name("static") / "index.html"


@app.get("/")
def home():
    if _static.exists():
        return FileResponse(_static)
    return {"app": "Soi Sacré – Rituel du jour", "docs": "/docs"}
