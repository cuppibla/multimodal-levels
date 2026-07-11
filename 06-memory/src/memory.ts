// ─────────────────────────────────────────────────────────────────────────────
// The DIY-hybrid memory loop — the honest, pre-"managed Memory Bank" version, so the mechanism is visible.
//   WRITE (extract): Gemini reads a transcript → a few DURABLE facts (exact + pattern).
//   READ  (recall):  embed the query + facts → similarity recall (patterns by meaning; exact always kept).
// This is exactly what a managed memory service does for you — here we do it by hand.
// ─────────────────────────────────────────────────────────────────────────────
import { Type } from "@google/genai";
import { ai, READ_MODEL, EMBED_MODEL } from "./client.js";

// The two kinds of knowing: "exact" = a value you LOOK UP (callsign, a number, a date);
// "pattern" = a soft trait about who they are / how they like things, built over time.
export type Fact = { kind: "exact" | "pattern"; label: string; value: string };

// ── WRITE ─────────────────────────────────────────────────────────────────────
// Curate a transcript into 2–6 durable facts. Skip small talk; keep only what would change next time.
export async function extractFacts(transcript: string): Promise<Fact[]> {
  const res = await ai().models.generateContent({
    model: READ_MODEL,
    contents:
      `A survivor just talked with the rescue mission AI. Extract only DURABLE memory worth carrying into ` +
      `their NEXT session — things that would change how the AI greets or helps them.\n` +
      `Two kinds: "exact" = a concrete looked-up value (callsign, a date, a number, a specific named thing); ` +
      `"pattern" = a soft trait about who they are or how they like things.\n` +
      `Skip greetings and small talk. Return 2-6 facts.\n\nTRANSCRIPT:\n${transcript}`,
    config: {
      thinkingConfig: { thinkingBudget: 0 },
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            kind: { type: Type.STRING, enum: ["exact", "pattern"] },
            label: { type: Type.STRING },
            value: { type: Type.STRING },
          },
          required: ["kind", "label", "value"],
        },
      },
    },
  });
  try {
    const arr = JSON.parse((res.text ?? "[]").trim());
    return Array.isArray(arr) ? arr.filter((f: Fact) => f?.label && f?.value).slice(0, 6) : [];
  } catch {
    return [];
  }
}

// ── READ ──────────────────────────────────────────────────────────────────────
// Rank stored facts against a query. Exact facts are ALWAYS surfaced (you want your balance, not something
// *like* it); patterns are ranked by embedding similarity — recall by meaning, not keyword match.
export async function recall(query: string, facts: Fact[]): Promise<{ fact: Fact; score: number }[]> {
  if (!facts.length) return [];
  const texts = facts.map((f) => `${f.label}: ${f.value}`);
  const res = await ai().models.embedContent({
    model: EMBED_MODEL,
    contents: [query || "who is this operator", ...texts],
  });
  const vecs = (res.embeddings ?? []).map((e) => (e.values as number[]) ?? []);
  const q = vecs[0] ?? [];
  return facts
    .map((f, i) => ({ fact: f, score: vecs[i + 1] ? cosine(q, vecs[i + 1]) : 0 }))
    .sort((a, b) => Number(b.fact.kind === "exact") - Number(a.fact.kind === "exact") || b.score - a.score);
}

function cosine(a: number[], b: number[]): number {
  let d = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    d += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return d / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}
