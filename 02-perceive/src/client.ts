// One Gemini client for the whole module — the SAME "no lock-in" choice the real app makes:
// use an AI Studio key if you have one, otherwise your own Vertex project via ADC.
// The key takes precedence (that's why a stray GEMINI_API_KEY quietly wins over Vertex).
import { GoogleGenAI } from "@google/genai";

let client: GoogleGenAI | null = null;

export function ai(): GoogleGenAI {
  if (client) return client;
  const apiKey = process.env.GEMINI_API_KEY;
  client = apiKey
    ? new GoogleGenAI({ apiKey }) //                         AI Studio path — simplest
    : new GoogleGenAI({
        vertexai: true, //                                   Vertex path — your project, your quota
        project: process.env.GOOGLE_CLOUD_PROJECT,
        location: process.env.GOOGLE_CLOUD_LOCATION || "global",
      });
  return client;
}

// One model reads, one model measures, one model draws sample sites. Identical for every specialist.
export const READ_MODEL = process.env.GEMINI_MODEL || "gemini-2.5-flash";
export const EMBED_MODEL = process.env.GEMINI_EMBED_MODEL || "gemini-embedding-001";
export const IMAGE_MODEL = process.env.GEMINI_IMAGE_MODEL || "gemini-2.5-flash-image";

export function authLabel(): string {
  return process.env.GEMINI_API_KEY
    ? "AI Studio key"
    : `Vertex ADC · ${process.env.GOOGLE_CLOUD_PROJECT ?? "(no project set)"}`;
}
