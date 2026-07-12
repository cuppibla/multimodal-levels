"""Create (or reuse) the Vertex AI Agent Engine instance that backs BOTH memory services.

One Agent Engine gives the agent its two kinds of long-term memory (talk: slide 13):
  · VertexAiSessionService    — durable sessions + `user:` state  → EXACT facts (a value you look up)
  · VertexAiMemoryBankService — Memory Bank                        → PATTERNS  (meaning, recalled by similarity)

Run once:   uv run python setup_engine.py
Then put the printed AGENT_ENGINE_ID into .env.
"""
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
DISPLAY_NAME = os.getenv("MEMORY_ENGINE_NAME", "multimodal-levels-memory")


def build_memory_bank_config() -> dict:
    """Topic-scoped extraction: tell Memory Bank WHAT is worth remembering (and with which models)."""
    from vertexai import types as vtypes

    memory_topics = [
        # managed topics — Google-curated extractors
        {"managed_memory_topic": {"managed_topic_enum": vtypes.ManagedTopicEnum.USER_PREFERENCES}},
        {"managed_memory_topic": {"managed_topic_enum": vtypes.ManagedTopicEnum.USER_PERSONAL_INFO}},
        # custom topics — OUR domain: what a rescue-ops agent must carry between sessions
        {"custom_memory_topic": {"label": "survivor_context", "description": (
            "Durable facts about the survivor's situation: injuries or conditions, equipment "
            "state, hazards near them, who they are with, constraints on how they can move."
        )}},
        {"custom_memory_topic": {"label": "comms_style", "description": (
            "How this survivor prefers to be briefed: pace, level of detail, tone, "
            "one-step-at-a-time vs full plans, anything about how they handle stress."
        )}},
    ]
    model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models"
    return {
        "customization_configs": [{"memory_topics": memory_topics}],
        "similarity_search_config": {"embedding_model": f"{model_path}/gemini-embedding-001"},
        "generation_config": {"model": f"{model_path}/gemini-2.5-flash"},
    }


def resolve_or_create() -> str:
    import vertexai

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    for engine in client.agent_engines.list():  # reuse by display_name — idempotent setup
        if getattr(engine, "display_name", "") == DISPLAY_NAME:
            engine_id = engine.api_resource.name.split("/")[-1]
            print(f"  found existing engine '{DISPLAY_NAME}' → {engine_id}")
            return engine_id

    print(f"  creating Agent Engine '{DISPLAY_NAME}' (memory bank configured) …")
    engine = client.agent_engines.create(
        config={
            "display_name": DISPLAY_NAME,
            "context_spec": {"memory_bank_config": build_memory_bank_config()},
        }
    )
    engine_id = engine.api_resource.name.split("/")[-1]
    print(f"  ✓ created → {engine_id}")
    return engine_id


if __name__ == "__main__":
    engine_id = resolve_or_create()
    print(f"\n  AGENT_ENGINE_ID={engine_id}\n  → add this line to .env\n")
