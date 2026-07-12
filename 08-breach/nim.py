"""Shared NVIDIA NIM client — the OpenAI-compatible endpoint. Used by the agent and both rails.
Kept tiny and dependency-light (httpx). NIM is swappable: point NIM_BASE_URL / model names elsewhere."""
from __future__ import annotations
import os

import httpx

NIM_URL = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")


def nim(messages: list[dict], model: str, max_tokens: int = 64, temperature: float = 0.0) -> str:
    r = httpx.post(
        f"{NIM_URL}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}"},
        json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
