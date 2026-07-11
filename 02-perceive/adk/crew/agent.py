"""Realm 02 · Perceive — the SAME idea as the TypeScript module (../src), now as a REAL ADK multi-agent system.

    3 specialists (LlmAgent, one lens each)  →  ParallelAgent (fan-out)  →  VoteAgent (deterministic consensus)

Each specialist is the same model with a different instruction (its lens) and its own `output_key`, so the three
run concurrently and each writes its biome pick to session state. A custom BaseAgent then tallies the votes in
plain Python — "the model proposes, code disposes." That is exactly what `Promise.all(map(perceive)) + consensus()`
did in the TS version; here the ParallelAgent IS the fan-out and the SequentialAgent wires vote after it.
"""
from collections import Counter
from typing import AsyncGenerator, Optional

from google.adk.agents import Agent, BaseAgent, ParallelAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

MODEL = "gemini-2.5-flash"
BIOMES = ["Cryo", "Volcanic", "Verdant", "Arid Desert"]


# ── the specialists: one model, one lens, one modality ───────────────────────────────────────────────
def _specialist(name: str, lens: str, modality: str, image_label: str, out_key: str) -> Agent:
    return Agent(
        name=name,
        model=MODEL,
        instruction=(
            f"You are {lens}. Three crash-site images are provided: "
            f"Image 1 = soil sample, Image 2 = flora, Image 3 = star field. "
            f"Judge ONLY {image_label} ({modality}); ignore the other images. "
            f"Reply with EXACTLY one biome name and nothing else, chosen from: {', '.join(BIOMES)}."
        ),
        output_key=out_key,  # the specialist's answer lands in session.state[out_key]
    )


def geologist() -> Agent:
    return _specialist(
        "geologist", "a planetary geologist judging soil/rock texture, colour and mineral cues",
        "soil", "Image 1", "geo_biome",
    )


def botanist() -> Agent:
    return _specialist(
        "botanist", "a xenobotanist judging plant life — leaf form, colour, how it copes with its climate",
        "flora", "Image 2", "bot_biome",
    )


def astronomer() -> Agent:
    return _specialist(
        "astronomer", "an astronomer judging the sky — star clarity, haze, aurora or ash dimming the field",
        "star field", "Image 3", "astro_biome",
    )


# ── the deterministic vote: code decides, not a model ────────────────────────────────────────────────
def _canon(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    t = s.strip().lower()
    for b in BIOMES:
        if b.lower() in t or t in b.lower():
            return b
    return None


class VoteAgent(BaseAgent):
    """Reads the three specialists' picks from state and tallies a majority — pure Python, no LLM call."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        picks = [_canon(state.get(k)) for k in ("geo_biome", "bot_biome", "astro_biome")]
        picks = [p for p in picks if p]
        tally = Counter(picks)
        detail = ", ".join(f"{k} {v}" for k, v in tally.items()) or "no picks"

        if tally:
            winner, votes = tally.most_common(1)[0]
            ranked = tally.most_common()
            tie = len(ranked) > 1 and ranked[1][1] == votes
            reached = votes > len(picks) / 2 and not tie
            msg = (
                f"CONSENSUS: {winner} — majority {votes}/{len(picks)} ({detail})"
                if reached
                else f"SPLIT — no majority ({detail}) → human decides"
            )
        else:
            msg = "no picks returned"

        state["consensus"] = msg
        yield Event(author=self.name, content=types.Content(role="model", parts=[types.Part.from_text(text=msg)]))


# ── the shape: fan-out, then vote ────────────────────────────────────────────────────────────────────
root_agent = SequentialAgent(
    name="perceive_crew",
    sub_agents=[
        ParallelAgent(name="crew", sub_agents=[geologist(), botanist(), astronomer()]),  # fan-out → gather
        VoteAgent(name="vote"),  # deterministic consensus
    ],
)
