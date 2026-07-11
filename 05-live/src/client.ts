// One Gemini client + a Live-model picker. Same no-lock-in choice as the app: your own Vertex project via ADC
// by default, an AI Studio key if one is set. Live model availability drifts by path/region/date, so instead
// of hardcoding one we PROBE candidates and keep the first that actually opens.
import { GoogleGenAI, Modality } from "@google/genai";

let client: GoogleGenAI | null = null;
export function ai(): GoogleGenAI {
  if (client) return client;
  const apiKey = process.env.GEMINI_API_KEY;
  client = apiKey
    ? new GoogleGenAI({ apiKey })
    : new GoogleGenAI({
        vertexai: true,
        project: process.env.GOOGLE_CLOUD_PROJECT,
        location: process.env.GEMINI_LIVE_LOCATION || "us-central1",
      });
  return client;
}

const useVertex = () => !process.env.GEMINI_API_KEY && !!process.env.GOOGLE_CLOUD_PROJECT;

export const authLabel = () =>
  useVertex() ? `Vertex ADC · ${process.env.GOOGLE_CLOUD_PROJECT} · ${process.env.GEMINI_LIVE_LOCATION || "us-central1"}` : "AI Studio key";

function candidates(): string[] {
  if (process.env.GEMINI_LIVE_MODEL) return [process.env.GEMINI_LIVE_MODEL];
  return useVertex()
    ? ["gemini-live-2.5-flash", "gemini-2.0-flash-live-preview-04-09", "gemini-2.5-flash-preview-native-audio-dialog"]
    : ["gemini-2.5-flash-native-audio-preview-09-2025", "gemini-2.0-flash-live-001"];
}

// A healthy idle Live session stays open; an unavailable model errors/closes quickly with not-found.
function canOpen(model: string): Promise<boolean> {
  return new Promise((resolve) => {
    let settled = false;
    let sess: { close: () => void } | undefined;
    const finish = (v: boolean) => {
      if (settled) return;
      settled = true;
      try { sess?.close(); } catch { /* ignore */ }
      resolve(v);
    };
    const timer = setTimeout(() => finish(true), 4000);
    ai()
      .live.connect({
        model,
        config: { responseModalities: [Modality.AUDIO] },
        callbacks: {
          onopen: () => {},
          onmessage: () => {},
          onerror: () => { clearTimeout(timer); finish(false); },
          onclose: () => { clearTimeout(timer); finish(false); },
        },
      })
      .then((s) => { sess = s; })
      .catch(() => { clearTimeout(timer); finish(false); });
  });
}

export async function pickModel(): Promise<string> {
  const list = candidates();
  for (const m of list) if (await canOpen(m)) return m;
  throw new Error(
    `no Live model opened on this ${useVertex() ? "project/region" : "key"}. Try setting GEMINI_LIVE_MODEL, ` +
      `or (Vertex) a region with Live. Tried: ${list.join(", ")}`,
  );
}
