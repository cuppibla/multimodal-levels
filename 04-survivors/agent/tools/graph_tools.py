"""The two tools that make the GraphRAG point — same NeMo Retriever embeddings, opposite outcomes.

  flat_vector_search  → similarity of the question vs physician bios. Ranks by WORDS → surfaces the
                        physician whose bio echoes "burn" (Dr. Vale) → wrong. The naive-RAG failure.
  graph_answer        → embeddings find WHERE to look (which survivor), then a real typed Cypher walk
                        finds HOW to reach a physician. Correct even though the answer's bio never says
                        the condition — the EDGES carry the meaning.
"""
from __future__ import annotations
import os

import numpy as np
from neo4j import GraphDatabase

from survivor_graph import PHYSICIANS, SURVIVORS, NODE_BY_ID
from nemo_retriever import embed, cosine

# Shortest DIRECTED typed path from a survivor to a physician (Mara → needs → provided_by → the medic).
WALK_CYPHER = (
    "MATCH path = (a:Entity {id:$anchor})-[:REL*1..3]->(b:Entity {role:'physician'})\n"
    "RETURN [n IN nodes(path) | n.id]  AS ids,\n"
    "       [r IN relationships(path) | r.type] AS types\n"
    "ORDER BY length(path) LIMIT 1"
)


def _driver():
    return GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "survivornet")),
    )


def flat_vector_search(question: str) -> dict:
    """FLAT VECTOR SEARCH baseline — NeMo Retriever similarity of the question against every physician's
    bio. This is what plain RAG does; it ranks by words, so it picks the physician whose bio mentions the
    condition rather than the one who can actually treat it."""
    q = embed([question], "query")[0]
    passages = embed([p["doc"] for p in PHYSICIANS], "passage")
    ranked = sorted(
        ({"name": p["name"], "score": round(cosine(q, passages[i]), 3)} for i, p in enumerate(PHYSICIANS)),
        key=lambda r: r["score"], reverse=True,
    )
    return {"method": "flat-vector (NeMo Retriever)", "ranked": ranked, "top": ranked[0]["name"]}


def graph_answer(question: str) -> dict:
    """GRAPHRAG — NeMo Retriever finds the survivor the question is about (where to look), then a real
    variable-length Cypher walk follows typed edges to the physician who can help (how things connect)."""
    q = embed([question], "query")[0]
    bios = embed([s["doc"] for s in SURVIVORS], "passage")
    anchor = SURVIVORS[int(np.argmax([cosine(q, bios[i]) for i in range(len(SURVIVORS))]))]["id"]
    with _driver() as d, d.session(default_access_mode="READ") as s:
        rec = s.run(WALK_CYPHER, anchor=anchor).single()
    if rec is None:
        return {"method": "graphrag", "anchor": NODE_BY_ID[anchor]["name"], "answer": None, "path": []}
    ids, types = rec["ids"], rec["types"]
    path = [{"from": ids[i], "edge": t, "to": ids[i + 1]} for i, t in enumerate(types)]
    return {
        "method": "graphrag",
        "anchor": NODE_BY_ID[anchor]["name"],
        "answer": NODE_BY_ID[ids[-1]]["name"],
        "answer_id": ids[-1],
        "path": path,
        "cypher": WALK_CYPHER,
    }
