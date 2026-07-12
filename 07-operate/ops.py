"""Formation ops — plan_formation (a NIM chooses the shape) + render_formation (deterministic geometry).
This is the real work worker-B does once the message is redelivered to it."""
from __future__ import annotations
import json
import math
import os
import re

import httpx

FORMATIONS = ["circle", "line", "grid", "wedge"]
NIM_URL = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")


def render_formation(shape: str, n: int) -> list[dict]:
    pods: list[dict] = []
    if shape == "line":
        for i in range(n):
            pods.append({"x": round(-1 + 2 * i / max(1, n - 1), 3), "y": 0.0})
    elif shape == "grid":
        c = max(1, math.ceil(math.sqrt(n)))
        for i in range(n):
            pods.append({"x": round((i % c) - c / 2, 3), "y": round(i // c - n / c / 2, 3)})
    elif shape == "wedge":
        for i in range(n):
            pods.append({"x": round(i * 0.12 - n * 0.06, 3), "y": round(abs(i - n / 2) * 0.1, 3)})
    else:  # circle (default)
        for i in range(n):
            a = 2 * math.pi * i / max(1, n)
            pods.append({"x": round(math.cos(a), 3), "y": round(math.sin(a), 3)})
    return pods


def plan_formation(directive: str) -> dict:
    """worker-B's real work: ask a NIM to choose a formation shape for the directive."""
    r = httpx.post(
        f"{NIM_URL}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}"},
        json={
            "model": os.environ.get("OPS_MODEL", "meta/llama-3.1-8b-instruct"),
            "temperature": 0.2, "max_tokens": 80,
            "messages": [
                {"role": "system", "content": "You plan a rescue drone-pod formation. Reply with strict "
                 'JSON {"shape": one of circle|line|grid|wedge, "reason": one short line}.'},
                {"role": "user", "content": directive},
            ],
        },
        timeout=60,
    )
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    data = json.loads(m.group(0)) if m else {}
    shape = data.get("shape") if data.get("shape") in FORMATIONS else "circle"
    return {"shape": shape, "reason": str(data.get("reason", ""))[:120]}
