# Level 6 · Remember Me

> Durable, cross-session memory — by hand, so you can see the mechanism a managed Memory Bank hides.

The real code from the app's **Realm 06**, in three files:

| File | What it is |
|------|-----------|
| [`src/memory.ts`](src/memory.ts) | `extractFacts` (write) + `recall` (read) |
| [`src/store.ts`](src/store.ts) | `memory.json` — the durable store |
| [`src/run.ts`](src/run.ts) | the CLI |

## The loop: write, then read

**WRITE** — a session ends. Gemini reads the transcript and keeps only what's *durable* — the things that would change how it greets or helps this person next time. Two kinds:

- **exact** — a value you look up: a callsign, a number, a date.
- **pattern** — a soft trait: "freezes up at long checklists."

**READ** — next session. Embed the query + every stored fact, and recall by **meaning** (not keyword). Exact facts are always surfaced (you want *your* balance, not something like it); patterns rank by similarity.

```ts
const facts = await extractFacts(transcript);          // WRITE — a few durable facts
const hits  = await recall("how do I brief them?", facts); // READ — by meaning
```

"Persistence is not memory": the store ([`store.ts`](src/store.ts)) is just a JSON file. What makes it *memory* is the extract-then-recall loop around it — which is exactly the split between a database and a memory service.

## Run it

```bash
cp .env.example .env        # add GEMINI_API_KEY, or use your Vertex project
npm install

npm run demo                # canned transcript → extract → recall, end to end
# or drive it yourself, across two separate runs (the facts persist in memory.json):
npm run remember -- "Vega-7 here. Long checklists make me freeze — one step at a time. Recycler throws error 42."
npm run recall   -- "how should I brief this operator?"
npm run forget              # wipe the store
```

`remember` and `recall` are **separate processes** — the memory survives between them. That's the whole point.
