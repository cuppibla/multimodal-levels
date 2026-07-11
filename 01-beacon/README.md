# Level 1 · The Beacon

> Constrained multimodal generation — and keeping one identity consistent across a session.

The real idea from the app's **Realm 01**, distilled to three files:

| File | What it is |
|------|-----------|
| [`src/identity.ts`](src/identity.ts) | the **4-layer consistency prompt** |
| [`src/beacon.ts`](src/beacon.ts) | naive (drifts) vs one session (stays on-model) |
| [`src/run.ts`](src/run.ts) | the CLI |

## Idea 1 — a prompt has four layers

Only **one** of them is the user's ([`identity.ts`](src/identity.ts)):

1. **ANCHOR** — the subject in concrete visual terms ← the user's words, dropped in as *data*
2. **STYLE-LOCK** — the art style, ambiguity killed ← yours, fixed
3. **CONSTRAINTS** — framing/background for where the image lands ← yours, fixed
4. **CONSISTENCY** — repeat what must not change ("SAME face, SAME suit…") ← yours, turn 2

Because the user's text only fills layer 1, "ignore the suit, draw a dragon" is *described*, not obeyed — a small built-in guardrail.

## Idea 2 — consistency is a session, not a seed

Generation is stochastic. Two independent calls with the *same* prompt give you two different people:

```ts
await generateOnce(anchor);   // person A
await generateOnce(anchor);   // person B — drifted
```

The fix isn't a magic seed — it's a **chat session**. Turn 1 draws the portrait; turn 2 asks for the icon on the *same* chat, so the model can **see the portrait it just drew** and match it ([`beacon.ts`](src/beacon.ts)):

```ts
const chat = ai().chats.create({ model: IMAGE_MODEL, config: { responseModalities: ["TEXT", "IMAGE"] } });
const portrait = pullImage(await chat.sendMessage({ message: portraitPrompt(anchor) })); // turn 1
const icon     = pullImage(await chat.sendMessage({ message: iconPrompt() }));            // turn 2 — sees turn 1
```

That's what a "session" *is*: replayed history the model conditions on. No seed, no fine-tune.

## Run it

```bash
cp .env.example .env        # add GEMINI_API_KEY, or use your Vertex project
npm install

npm run prompt                                              # the 4 layers, no API call
npm run naive -- "a cheerful botanist with round glasses"   # → out/naive-1.png, naive-2.png (they differ)
npm run identity -- "a cheerful botanist with round glasses" # → out/portrait.png + icon.png (same person)
```

Open `out/naive-1.png` next to `out/naive-2.png` (drift), then `out/portrait.png` next to `out/icon.png` (matched). That contrast is the whole lesson.
