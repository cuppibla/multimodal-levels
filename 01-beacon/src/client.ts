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
        location: process.env.GEMINI_IMAGE_LOCATION || "global",
      });
  return client;
}

export const IMAGE_MODEL = process.env.GEMINI_IMAGE_MODEL || "gemini-2.5-flash-image";
export const authLabel = () =>
  process.env.GEMINI_API_KEY ? "AI Studio key" : `Vertex ADC · ${process.env.GOOGLE_CLOUD_PROJECT ?? "(no project)"}`;
