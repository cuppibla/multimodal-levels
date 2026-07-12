"""The operator — an ADK agent that dispatches a drone-pod formation over the resilient Pub/Sub bus."""
from __future__ import annotations
import os

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from bus import resilient_formation


def dispatch_formation(directive: str) -> dict:
    """Publish the directive to the real Cloud Pub/Sub bus and run the resilient delivery loop
    (publish → worker-A crash/NACK → redeliver → worker-B plans via NIM → ACK). Returns the event
    trace, the planned shape, and the rendered pods."""
    return resilient_formation(directive, n=15)


root_agent = Agent(
    name="operator",
    model=os.environ.get("AGENT_MODEL", "gemini-2.5-flash"),
    description="Coordinates a drone-pod formation over a resilient Cloud Pub/Sub bus.",
    instruction=(
        "You coordinate the satellite/drone array at scale. For a formation directive:\n"
        "1. Call dispatch_formation(directive) — it publishes to the real bus and runs the resilient loop.\n"
        "Report the event trace (publish → claim → crash → redeliver → plan → ack) and the planned shape, "
        "then the key lesson: at-least-once delivery means a worker can crash after receiving; Pub/Sub "
        "redelivers, so the handler must be idempotent — the message is processed EXACTLY once."
    ),
    tools=[FunctionTool(dispatch_formation)],
)
