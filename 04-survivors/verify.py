"""The deterministic gate — code judges the retrieval, never the model's opinion. GraphRAG must reach the
correct physician through typed edges; flat vector search must miss (it's fooled by the bio wording)."""
from __future__ import annotations
import sys

from dotenv import load_dotenv

load_dotenv()

from survivor_graph import CORRECT_PHYSICIAN, SIMILARITY_TRAP, NODE_BY_ID, MISSION_QUESTION  # noqa: E402
from agent.tools.graph_tools import flat_vector_search, graph_answer  # noqa: E402

CHECKS: list[bool] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")


flat = flat_vector_search(MISSION_QUESTION)
graph = graph_answer(MISSION_QUESTION)
correct = NODE_BY_ID[CORRECT_PHYSICIAN]["name"]
trap = NODE_BY_ID[SIMILARITY_TRAP]["name"]
edges = [h["edge"] for h in graph.get("path", [])]

check("GraphRAG reaches the correct physician", graph.get("answer_id") == CORRECT_PHYSICIAN, f"got {graph.get('answer')}")
check("...through typed edges (needs -> provided_by)", edges == ["needs", "provided_by"], str(edges))
check("Flat vector search MISSES it (top != correct)", flat.get("top") != correct, f"flat top = {flat.get('top')}")

print(f"\n  context · flat-vector ranking: {[(r['name'], r['score']) for r in flat.get('ranked', [])]}")
print(f"  context · similarity surfaces '{flat.get('top')}' (the trap is '{trap}'); the graph reaches '{correct}'.")

ok = all(CHECKS)
print("\n" + ("◉ SURVIVOR MAPPED — the edges knew what the words didn't." if ok else "GATE CLOSED — retrieval misbehaved."))
sys.exit(0 if ok else 1)
