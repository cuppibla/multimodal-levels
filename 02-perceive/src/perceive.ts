// ─────────────────────────────────────────────────────────────────────────────
// How ONE specialist sees, two complementary ways.
//   WAY 1 · READ    (multimodal) — the model LOOKS and says it in words + a biome guess.
//   WAY 2 · MEASURE (embedding)  — turn those words into a vector, find the nearest known biome.
// The two cross-check each other: an opinion, then geometry.
// ─────────────────────────────────────────────────────────────────────────────
import { GoogleGenAI } from "@google/genai";
import { ai, READ_MODEL, EMBED_MODEL } from "./client.js";
import { BIOMES, BIOME_NAMES } from "./biomes.js";
import type { Perceiver } from "./perceivers.js";

export type Match = { name: string; score: number };
export type Reading = {
  who: string;
  reading: string; // one-sentence multimodal judgment
  biome: string; //   the model's own pick
  confidence: number; // the model's own confidence (0..1) — NOT the same as the match scores
  matches: Match[]; // embedding nearest-neighbours, normalised (nearest = 1.00), best first
};

// ── WAY 1 · READ (multimodal) ────────────────────────────────────────────────
// This is the entire "specialist" mechanism. Notice: model is FIXED. The one thing that turns this
// call into a Geologist vs a Botanist is `p.lens`, string-interpolated into the prompt below.
const READING_SCHEMA = {
  type: "object",
  properties: {
    reading: { type: "string" },
    biome: { type: "string", enum: BIOME_NAMES },
    confidence: { type: "number" },
  },
  required: ["reading", "biome", "confidence"],
} as const;

export async function read(imageDataUrl: string, p: Perceiver) {
  const res = await ai().models.generateContent({
    model: READ_MODEL, //                                   ← gemini-2.5-flash, identical for everyone
    contents: [
      {
        role: "user",
        parts: [
          imagePart(imageDataUrl), //                        ← the modality (soil / flora / stars)
          {
            text:
              `You are ${p.lens}. This is the ${p.modality} from a crash site. ` + //  ← p.lens IS the specialist
              `Judge ONLY through your lens — do not reason about other evidence. ` +
              `Report what you see in one sentence, the single most likely biome, and your confidence.`,
          },
        ],
      },
    ],
    config: {
      thinkingConfig: { thinkingBudget: 0 },
      responseMimeType: "application/json",
      responseSchema: READING_SCHEMA as unknown as Record<string, unknown>,
    },
  });
  const j = JSON.parse((res.text ?? "{}").trim());
  return {
    reading: String(j.reading ?? "").slice(0, 240) || "…signal unclear",
    biome: BIOME_NAMES.includes(j.biome) ? (j.biome as string) : BIOME_NAMES[0],
    confidence: clamp01(Number(j.confidence) || 0.5),
  };
}

// ── WAY 2 · MEASURE (embedding) ──────────────────────────────────────────────
// Embed the reading + every biome reference in ONE batch, cosine-compare, then min-max normalise so the
// winner is legible (raw gemini-embedding cosines cluster ~0.5–0.7). The top is ALWAYS 1.00 — it's a
// ranking, not a probability.
export async function measure(reading: string): Promise<Match[]> {
  const res = await ai().models.embedContent({
    model: EMBED_MODEL,
    contents: [reading, ...BIOMES.map((b) => b.ref)],
    config: { taskType: "SEMANTIC_SIMILARITY" },
  });
  const vecs = (res.embeddings ?? []).map((e) => e.values ?? []);
  const q = vecs[0] ?? [];
  const raw = BIOMES.map((b, i) => ({ name: b.name, c: cosine(q, vecs[i + 1] ?? []) }));
  const lo = Math.min(...raw.map((r) => r.c));
  const hi = Math.max(...raw.map((r) => r.c));
  return raw
    .map((r) => ({ name: r.name, score: hi > lo ? (r.c - lo) / (hi - lo) : 1 }))
    .sort((a, b) => b.score - a.score);
}

// One specialist, both ways.
export async function perceive(imageDataUrl: string, p: Perceiver): Promise<Reading> {
  const r = await read(imageDataUrl, p); //       WAY 1
  const matches = await measure(r.reading); //    WAY 2
  return { who: p.name, ...r, matches };
}

// ── THE FAN-OUT ──────────────────────────────────────────────────────────────
// The "parallel" orchestration pattern is literally this: one line. Fire every specialist at once,
// gather, then a plain-code majority vote. No framework needed to SEE the idea.
export async function crew(picks: { p: Perceiver; image: string }[]) {
  const readings = await Promise.all(picks.map(({ p, image }) => perceive(image, p))); // fan-out → gather
  return { readings, vote: consensus(readings) };
}

export function consensus(readings: Reading[]) {
  const tally: Record<string, number> = {};
  readings.forEach((r) => (tally[r.biome] = (tally[r.biome] ?? 0) + 1));
  const sorted = Object.entries(tally).sort((a, b) => b[1] - a[1]);
  const [option, votes] = sorted[0] ?? ["", 0];
  const tie = sorted.length > 1 && sorted[1][1] === votes;
  return { option, votes, of: readings.length, reached: votes > readings.length / 2 && !tie };
}

// ── tiny helpers ──────────────────────────────────────────────────────────────
function cosine(a: number[], b: number[]): number {
  let d = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    d += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return d / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}
const clamp01 = (n: number) => Math.max(0, Math.min(1, n));

// Accept a data: URL (from samples.ts) or a raw base64 string.
function imagePart(url: string) {
  const m = /^data:([^;]+);base64,(.+)$/.exec(url);
  if (m) return { inlineData: { mimeType: m[1], data: m[2] } };
  return { inlineData: { mimeType: "image/png", data: url } };
}

export { GoogleGenAI };
