"""One-time: seed the survivor network into a real Neo4j graph (idempotent). Run before the mission."""
from __future__ import annotations
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from survivor_graph import NODES, EDGES

load_dotenv()


def main() -> None:
    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "survivornet")),
    )
    with driver.session() as s:
        s.run("MATCH (n:Entity) DETACH DELETE n")
        for n in NODES:
            s.run("MERGE (e:Entity {id:$id}) SET e.name=$name, e.kind=$kind, e.role=$role, e.doc=$doc", **n)
        for e in EDGES:
            s.run(
                "MATCH (a:Entity {id:$from}) MATCH (b:Entity {id:$to}) MERGE (a)-[:REL {type:$type}]->(b)",
                **{"from": e["from"], "to": e["to"], "type": e["type"]},
            )
        n_ent = s.run("MATCH (n:Entity) RETURN count(n) AS c").single()["c"]
        n_rel = s.run("MATCH ()-[r:REL]->() RETURN count(r) AS c").single()["c"]
    driver.close()
    print(f"✓ seeded survivor graph: {n_ent} entities, {n_rel} typed edges on {os.environ.get('NEO4J_URI')}")


if __name__ == "__main__":
    main()
