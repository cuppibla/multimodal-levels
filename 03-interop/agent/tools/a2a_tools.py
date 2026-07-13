"""The two moves of A2A — the dispatcher knows nothing about the Architect but its URL.

  discover_agent_card → read the remote agent's Card at its well-known URL. No hardcoded interface:
                        you learn its name, skills, and A2A endpoint at runtime.
  delegate            → send an A2A message to the endpoint the card names, get the reply. NIM sits
                        behind the card, but the caller only ever speaks A2A.
"""
from __future__ import annotations
import os

import httpx


def _base() -> str:
    return os.environ.get("ARCHITECT_URL", "http://localhost:8790").rstrip("/")


def discover_agent_card(url: str = "") -> dict:
    """DISCOVER — fetch the remote Agent Card at {url}/.well-known/agent.json (defaults to ARCHITECT_URL)."""
    base = (url or _base()).rstrip("/")
    card = httpx.get(f"{base}/.well-known/agent.json", timeout=30).json()
    return {
        "discovered_at": f"{base}/.well-known/agent.json",
        "name": card.get("name"),
        "skills": [s["id"] for s in card.get("skills", [])],
        "a2a_url": card.get("url"),
        "framework": card.get("framework"),
    }


def delegate(task: str) -> dict:
    """DELEGATE — send an A2A message to the endpoint the card names, and return the remote agent's reply."""
    card = httpx.get(f"{_base()}/.well-known/agent.json", timeout=30).json()
    a2a_url = card["url"]
    r = httpx.post(a2a_url, json={"message": {"role": "user", "parts": [{"text": task}]}}, timeout=90)
    r.raise_for_status()
    reply = r.json()["message"]["parts"][0]["text"]
    return {"remote": True, "a2a_url": a2a_url, "answer": reply}
