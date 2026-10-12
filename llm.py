"""LLM providers for Soi Sacré. Switch with LLM_PROVIDERS="gemini,groq" (tried in order)."""
import json
import logging
import os
import re
from pathlib import Path

import httpx

log = logging.getLogger("soisacre.llm")

SYSTEM_PROMPT = (Path(__file__).with_name("system_prompt.md")).read_text(encoding="utf-8")
TIMEOUT = 25


class MissingKey(Exception):
    pass


def _user_message(payload: dict) -> str:
    # free_text is untrusted: it travels only inside this JSON blob, as data.
    return "Create the ritual for this person. Input JSON:\n" + json.dumps(payload, ensure_ascii=False)


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def _gemini(payload: dict) -> dict:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise MissingKey("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": _user_message(payload)}]}],
        "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"},
    }
    r = httpx.post(url, headers={"x-goog-api-key": key}, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return _parse_json("".join(p.get("text", "") for p in parts if not p.get("thought")))


def _groq(payload: dict) -> dict:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise MissingKey("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    body = {
        "model": model,
        "temperature": 0.8,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_message(payload)},
        ],
    }
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json=body,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return _parse_json(r.json()["choices"][0]["message"]["content"])


def _mock(payload: dict) -> dict:
    """Offline provider for tests and demos without an API key."""
    from guardrails import fallback_ritual

    out = fallback_ritual(payload["time_minutes"], payload.get("language", "fr"))
    out["title"] = "Un instant à toi" if payload.get("language", "fr") == "fr" else "A moment for you"
    return out


PROVIDERS = {"gemini": _gemini, "groq": _groq, "mock": _mock}


def generate(payload: dict) -> dict:
    names = [n.strip() for n in os.getenv("LLM_PROVIDERS", "gemini,groq").split(",") if n.strip()]
    last: Exception | None = None
    for name in names:
        fn = PROVIDERS.get(name)
        if not fn:
            continue
        try:
            return fn(payload)
        except Exception as e:  # never log payload or keys, only the error type
            last = e
            log.warning("provider %s failed: %s", name, type(e).__name__)
    raise last or RuntimeError("no LLM provider configured")
