"""Deterministic gate — the dispatch must be REMOTE (cross-boundary A2A), discovered from the Card, and
return a real answer. Writes outputs/dispatch.json (the checked-in proof of a real round-trip)."""
from __future__ import annotations
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.tools.a2a_tools import discover_agent_card, delegate  # noqa: E402

TASK = "How do I reseat the nav-array coupling after a debris strike?"
CHECKS: list[bool] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")


card = discover_agent_card()
res = delegate(TASK)

check("discovered a real Agent Card (skills + A2A endpoint)",
      bool(card.get("skills")) and bool(card.get("a2a_url")), f"skills={card.get('skills')}")
check("card is NIM-backed (NVIDIA framework)", "NIM" in (card.get("framework") or ""), card.get("framework"))
check("delegation was REMOTE (cross-boundary A2A)", res.get("remote") is True, f"a2a_url={res.get('a2a_url')}")
check("remote agent returned a real answer", bool((res.get("answer") or "").strip()), (res.get("answer") or "")[:60] + "…")

ok = all(CHECKS)
os.makedirs("outputs", exist_ok=True)
json.dump({"task": TASK, "card": card, "dispatch": res, "verified": ok}, open("outputs/dispatch.json", "w"), indent=2)
print("\n" + ("◉ CHANNEL OPEN — discovered the card, delegated across the boundary." if ok else "GATE CLOSED — A2A did not complete."))
sys.exit(0 if ok else 1)
