"""NVIDIA NeMo Retriever embeddings (nv-embedqa-e5-v5) — the "find where to look" half of GraphRAG.

Asymmetric: the question is embedded as a `query`, the bios as `passage`s (NeMo Retriever is trained
for retrieval, so query/passage get different encodings). Runs on your NVIDIA key over the OpenAI-
compatible endpoint. Swap the model via NEMO_EMBED_MODEL.
"""
from __future__ import annotations
import os

import httpx
import numpy as np

NEMO_URL = os.environ.get("NEMO_EMBED_URL", "https://integrate.api.nvidia.com/v1/embeddings")
MODEL = os.environ.get("NEMO_EMBED_MODEL", "nvidia/nv-embedqa-e5-v5")


def embed(texts: list[str], input_type: str) -> np.ndarray:
    """input_type: 'query' or 'passage'. Returns an (n, dim) array."""
    r = httpx.post(
        NEMO_URL,
        headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}"},
        json={"model": MODEL, "input": texts, "input_type": input_type, "encoding_format": "float"},
        timeout=60,
    )
    r.raise_for_status()
    return np.array([d["embedding"] for d in r.json()["data"]], dtype=float)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
