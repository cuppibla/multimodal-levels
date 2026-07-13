"""The Architect — a SEPARATE agent, in its own process (its own repo/team/deploy in real life). It
publishes an Agent Card at /.well-known/agent.json and answers A2A messages at /a2a, backed by NVIDIA
NIM. The dispatcher knows nothing about it but its URL — that's the whole point of A2A.

Run:    NVIDIA_API_KEY=... uv run python -m architect.main        (PORT=8790)
Deploy: gcloud run deploy architect --source ./architect --allow-unauthenticated   (its own HOST)
"""
from __future__ import annotations
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
import uvicorn
from fastapi import FastAPI, Request

PORT = int(os.environ.get("PORT", "8790"))
SELF = os.environ.get("PUBLIC_URL", f"http://localhost:{PORT}").rstrip("/")
NIM_MODEL = os.environ.get("ARCHITECT_MODEL", "meta/llama-3.1-8b-instruct")
NIM_URL = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

# The Agent Card — the discovery contract. A caller binds to THIS shape, not to our code.
CARD = {
    "name": "Architect",
    "description": "Remote schematics agent — give it a component or failure, it returns concise assembly guidance.",
    "url": f"{SELF}/a2a",
    "version": "1.0.0",
    "framework": f"NVIDIA NIM · {NIM_MODEL}",
    "skills": [{"id": "lookup_schematic", "name": "Look up a schematic",
                "description": "Given a component or question, returns concise assembly/repair guidance."}],
}
SYSTEM = ("You are the Architect, a remote engineering agent aboard the relay. Answer with concise, "
          "practical assembly/repair guidance for the stranded crew. Be terse — a few steps, no preamble.")

app = FastAPI(title="Architect A2A agent")


async def _nim(task: str) -> str:
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            f"{NIM_URL}/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}"},
            json={"model": NIM_MODEL, "temperature": 0.2, "max_tokens": 220,
                  "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


@app.get("/.well-known/agent.json")
def agent_card() -> dict:
    return CARD


@app.get("/health")
def health() -> dict:
    return {"ok": True, "agent": CARD["name"]}


@app.post("/a2a")
async def a2a(req: Request) -> dict:
    """An A2A message → the agent's reply. Message shape: {role, parts:[{text}]}."""
    body = await req.json()
    parts = (body.get("message") or {}).get("parts") or []
    task = " ".join(p.get("text", "") for p in parts).strip()
    if not task:
        return {"error": "empty A2A message"}
    return {"message": {"role": "agent", "parts": [{"text": await _nim(task)}]}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", PORT)))
