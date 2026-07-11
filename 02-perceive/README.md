# Level 2 · Perceive

> How one specialist sees — and why three of them beat one generalist.

This is the real code from the app's **Realm 02**, with the game scaffolding removed. Four small files hold the whole idea:

| File | What it is |
|------|-----------|
| [`src/perceivers.ts`](src/perceivers.ts) | the specialists — **just data**. A `lens` string each. |
| [`src/perceive.ts`](src/perceive.ts) | the two ways of seeing + the parallel fan-out |
| [`src/biomes.ts`](src/biomes.ts) | the reference library `measure` matches against |
| [`src/run.ts`](src/run.ts) | a tiny CLI so you can watch it happen |

## The one idea: a specialist is not a separate AI

A "Geologist" is **the same `gemini-2.5-flash`** as every other specialist. What makes it a Geologist is one instruction — the `lens` — and which image it's handed. That's the entire definition ([`perceivers.ts`](src/perceivers.ts)):

```ts
{ id: "geo", name: "Geologist", modality: "soil sample",
  lens: "a planetary geologist judging ONLY the soil/rock texture, colour and mineral cues" }

{ id: "bot", name: "Botanist",  modality: "flora",
  lens: "a xenobotanist judging ONLY the plant life — leaf form, colour, how it copes with its climate" }
```

And here is the single place that string is used — the `lens` is interpolated straight into the prompt, model held constant ([`perceive.ts`](src/perceive.ts) → `read()`):

```ts
model: READ_MODEL,                                    // gemini-2.5-flash — identical for everyone
contents: [{ role: "user", parts: [
  imagePart(imageDataUrl),                            // the modality
  { text: `You are ${p.lens}. This is the ${p.modality} from a crash site. Judge ONLY through your lens…` },
]}],                                                   // ↑ p.lens IS the specialist
```

`read(soil, geo)` and `read(flora, bot)` are the **same function call**. Swap the 15-word string, get a different specialist. No training, no second endpoint.

## Two ways one specialist sees

1. **READ** (multimodal) — the model looks and says what it sees, in words + a best-guess biome. *An opinion.*
2. **MEASURE** (embedding) — turn those words into a vector, find the nearest biome in a reference library. *Geometry.*

They cross-check each other. The MEASURE bars are **normalised similarity** — the nearest is always `1.00`, so it's a ranking, not a confidence %.

## The fan-out is one line

Three specialists don't need each other, so run them at once, then vote ([`perceive.ts`](src/perceive.ts) → `crew()`):

```ts
const readings = await Promise.all(picks.map(({ p, image }) => perceive(image, p))); // fan-out → gather
return { readings, vote: consensus(readings) };                                       // plain-code majority
```

That `Promise.all(map(perceive))` **is** the "parallel" pattern. Everything fancier (ADK's `ParallelAgent`) is a wrapper over exactly this shape.

## Run it

```bash
cp .env.example .env        # add GEMINI_API_KEY, or use your Vertex project
npm install

npm run roster              # the 3 lenses, no API call — start here
npm run samples -- verdant  # draw a matching soil/flora/stars crash site into assets/
npm run perceive -- assets/verdant-soil.png            # Geologist, two ways
npm run perceive -- assets/verdant-soil.png --who bot  # same image, Botanist's lens — watch it hedge
npm run perceive -- --crew assets/verdant-soil.png assets/verdant-flora.png assets/verdant-stars.png
```

Swapping `--who geo` for `--who bot` on the **same** soil image is the demo: identical model, identical call, different lens → a Botanist looking at soil gives a visibly weaker read. That's the whole point, in one command.
