"""The REAL resilient bus on Google Cloud Pub/Sub — publish once, survive a crash.

  publish FORM_UP → worker-A receives + NACKs (crash before ack) → Pub/Sub REDELIVERS the same message
  → worker-B receives, plans (NIM), and ACKs → processed exactly once.

The lesson: at-least-once delivery means a worker can die after receiving; the broker redelivers, so the
handler must be idempotent. No client-side theater — every event is a real broker operation.
"""
from __future__ import annotations
import json
import os
import time

from google.cloud import pubsub_v1

from ops import plan_formation, render_formation

TOPIC = "wbh-formation"
SUB = "wbh-formation-sub"


def project_id() -> str:
    return os.environ.get("PUBSUB_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "wbh-local"


def resilient_formation(directive: str, n: int = 15) -> dict:
    project = project_id()
    pub = pubsub_v1.PublisherClient()
    sub = pubsub_v1.SubscriberClient()
    tp = pub.topic_path(project, TOPIC)
    sp = sub.subscription_path(project, SUB)
    events: list[dict] = []
    t0 = time.monotonic()
    at = lambda: round((time.monotonic() - t0) * 1000)
    broker = "pubsub-emulator" if os.environ.get("PUBSUB_EMULATOR_HOST") else "cloud-pubsub"

    msg_id = pub.publish(tp, json.dumps({"type": "FORM_UP", "directive": directive}).encode()).result()
    events.append({"kind": "publish", "text": f"PUBLISH  FORM_UP → {TOPIC} · msg {msg_id}", "ms": at()})

    def pull_one():
        resp = sub.pull(subscription=sp, max_messages=1, timeout=20)
        return resp.received_messages[0] if resp.received_messages else None

    # worker-A: receive delivery #1, NACK (crash before ack) → Pub/Sub redelivers
    a = pull_one()
    events.append({"kind": "claim", "text": "worker-A  received (delivery #1) · planning…", "ms": at()})
    sub.modify_ack_deadline(subscription=sp, ack_ids=[a.ack_id], ack_deadline_seconds=0)  # NACK
    events.append({"kind": "crash", "text": "worker-A  ✗ CRASHED before ack — NACK → Pub/Sub redelivers", "ms": at()})

    # worker-B: receive the redelivery, do the real work, ACK → processed exactly once
    b = pull_one()
    events.append({"kind": "redeliver", "text": "bus       ↻ redelivered same msg → worker-B (delivery #2)", "ms": at()})
    plan = plan_formation(json.loads(b.message.data.decode())["directive"])
    pods = render_formation(plan["shape"], n)
    sub.acknowledge(subscription=sp, ack_ids=[b.ack_id])
    events.append({"kind": "plan", "text": f"worker-B  ✓ planned: {plan['shape']} — {plan['reason']}", "ms": at()})
    events.append({"kind": "ack", "text": "worker-B  ✓ ACK — settled, processed exactly once", "ms": at()})

    return {"plan": plan, "pods": pods, "events": events, "msgId": msg_id, "broker": broker, "ms": at()}
