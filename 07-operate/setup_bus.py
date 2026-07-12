"""One-time: create the Pub/Sub topic + subscription (idempotent). Run before the mission."""
from __future__ import annotations
import os

from dotenv import load_dotenv

load_dotenv()

from google.cloud import pubsub_v1  # noqa: E402

from bus import TOPIC, SUB, project_id  # noqa: E402


def main() -> None:
    project = project_id()
    pub = pubsub_v1.PublisherClient()
    sub = pubsub_v1.SubscriberClient()
    tp = pub.topic_path(project, TOPIC)
    sp = sub.subscription_path(project, SUB)
    try:
        pub.create_topic(name=tp); print(f"✓ created topic {TOPIC}")
    except Exception:
        print(f"· topic {TOPIC} already exists")
    try:
        sub.create_subscription(name=sp, topic=tp, ack_deadline_seconds=10); print(f"✓ created subscription {SUB}")
    except Exception:
        print(f"· subscription {SUB} already exists")
    print(f"  on project {project}")


if __name__ == "__main__":
    main()
