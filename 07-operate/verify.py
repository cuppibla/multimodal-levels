"""Deterministic gate — the resilient loop must run on REAL Cloud Pub/Sub: publish → crash/NACK →
redeliver → plan → ACK, processed exactly once. Writes outputs/bus_run.json (the checked-in trace)."""
from __future__ import annotations
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from bus import resilient_formation  # noqa: E402

DIRECTIVE = "Encircle the ridge to sweep every approach at once."
CHECKS: list[bool] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")


res = resilient_formation(DIRECTIVE, n=12)
kinds = [e["kind"] for e in res["events"]]

check("real Cloud Pub/Sub (not the emulator)", res["broker"] == "cloud-pubsub", res["broker"])
check("full resilient loop (publish→crash→redeliver→ack)",
      kinds == ["publish", "claim", "crash", "redeliver", "plan", "ack"], " → ".join(kinds))
check("worker-B planned a real formation (NIM)",
      res["plan"]["shape"] in ("circle", "line", "grid", "wedge"), f"{res['plan']['shape']} — {res['plan']['reason']}")
check("rendered the pods", len(res["pods"]) == 12, str(len(res["pods"])))

ok = all(CHECKS)
os.makedirs("outputs", exist_ok=True)
json.dump({"directive": DIRECTIVE, **res, "verified": ok}, open("outputs/bus_run.json", "w"), indent=2)
print("\n" + ("◉ FORMATION HELD — one crash, still processed exactly once." if ok else "GATE CLOSED — the bus loop broke."))
sys.exit(0 if ok else 1)
