// One Gemini client — AI Studio key if you have one, else your own Vertex project via ADC.
import { GoogleGenAI } from "@google/genai";

let client: GoogleGenAI | null = null;
export function ai(): GoogleGenAI {
  if (client) return client;
  const apiKey = process.env.GEMINI_API_KEY;
  client = apiKey
    ? new GoogleGenAI({ apiKey })
    : new GoogleGenAI({
        vertexai: true,
        project: process.env.GOOGLE_CLOUD_PROJECT,
        location: process.env.GOOGLE_CLOUD_LOCATION || "global",
      });
  return client;
}

export const READ_MODEL = process.env.GEMINI_MODEL || "gemini-2.5-flash";
export const EMBED_MODEL = process.env.GEMINI_EMBED_MODEL || "gemini-embedding-001";
export const authLabel = () =>
  process.env.GEMINI_API_KEY ? "AI Studio key" : `Vertex ADC · ${process.env.GOOGLE_CLOUD_PROJECT ?? "(no project)"}`;
