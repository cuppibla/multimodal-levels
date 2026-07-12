"""The survivor network — the seed data for the real Neo4j graph.

The GraphRAG lesson lives in the bios:
  • Dr. Okoye is the RIGHT answer for Mara's burns — but her bio never says "burn." She is reachable
    ONLY through typed edges: (mara)-[:needs]->(burn-care)-[:provided_by]->(okoye).
  • Dr. Vale's bio SCREAMS "burn triage, thermal injury" — so flat vector search ranks Vale #1 — but
    Vale provides rewarming, not burn care, and is NOT reachable from Mara. Similarity misleads; the
    graph corrects.
"""

MISSION_QUESTION = "Which physician can treat the crew member who took severe burns in the reactor breach?"

# The physician the typed walk must reach (ground truth for verify.py) and the one flat similarity is
# expected to wrongly surface.
CORRECT_PHYSICIAN = "okoye"
SIMILARITY_TRAP = "vale"

# Entity nodes: id, name, kind (survivor|need|person), role, doc (the bio embeddings see)
NODES = [
    {"id": "mara", "name": "Mara", "kind": "survivor", "role": "",
     "doc": "Crew member caught in the reactor breach; took severe burns and is trapped on the eastern ridge."},
    {"id": "rex", "name": "Rex", "kind": "survivor", "role": "",
     "doc": "Cargo hauler with a compound fracture after the debris strike; immobile in the hold."},
    {"id": "vega", "name": "Vega", "kind": "survivor", "role": "",
     "doc": "Stranded in the northern hab as heat failed; core temperature dropping toward hypothermia."},

    {"id": "burn-care", "name": "Burn Care", "kind": "need", "role": "",
     "doc": "Specialized treatment for severe burn injuries and tissue reconstruction."},
    {"id": "orthopedics", "name": "Orthopedics", "kind": "need", "role": "",
     "doc": "Fracture stabilization and bone repair."},
    {"id": "rewarming", "name": "Rewarming", "kind": "need", "role": "",
     "doc": "Controlled core-temperature restoration for hypothermia."},

    # RIGHT answer for burns — note the bio never contains the word "burn".
    {"id": "okoye", "name": "Dr. Okoye", "kind": "person", "role": "physician",
     "doc": "Field medic aboard the relay; trauma and reconstructive-tissue specialist."},
    # DISTRACTOR — bio is drenched in "burn", but Vale provides rewarming and is unreachable from Mara.
    {"id": "vale", "name": "Dr. Vale", "kind": "person", "role": "physician",
     "doc": "Authored the crew manual on burn triage and thermal-injury protocols; runs the rewarming bay."},
    {"id": "reyes", "name": "Dr. Reyes", "kind": "person", "role": "physician",
     "doc": "Orthopedic surgeon; sets fractures and stabilizes bone."},
]

# Directed typed edges: from -> to, with a relationship type
EDGES = [
    {"from": "mara", "to": "burn-care", "type": "needs"},
    {"from": "burn-care", "to": "okoye", "type": "provided_by"},
    {"from": "rex", "to": "orthopedics", "type": "needs"},
    {"from": "orthopedics", "to": "reyes", "type": "provided_by"},
    {"from": "vega", "to": "rewarming", "type": "needs"},
    {"from": "rewarming", "to": "vale", "type": "provided_by"},
]

PHYSICIANS = [n for n in NODES if n["role"] == "physician"]
SURVIVORS = [n for n in NODES if n["kind"] == "survivor"]
NODE_BY_ID = {n["id"]: n for n in NODES}
