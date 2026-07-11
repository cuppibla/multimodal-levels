// ─────────────────────────────────────────────────────────────────────────────
// One turn of a bidirectional Gemini Live session.
//   browser (or here, the terminal)  <-- ws -->  Live API
// In the app the browser streams mic + camera in and plays audio out. Here we send ONE text turn so it runs
// with no mic — but the shape is identical: open a session, stream events (audio chunks, transcripts, a live
// TOOL CALL, barge-in), then turn-complete. The key stays server-side; the model talks over a WebSocket.
// ─────────────────────────────────────────────────────────────────────────────
import { Modality, Type } from "@google/genai";
import { ai } from "./client.js";

// The tool the scanner calls when it "sees" fingers — same shape as the app's biometric demo. In a real
// session the model decides to call this from what it perceives; here it reacts to the text we send.
const REPORT_DIGIT = {
  functionDeclarations: [
    {
      name: "report_digit",
      description: "Report how many fingers the operator is holding up to the camera.",
      parameters: {
        type: Type.OBJECT,
        properties: { count: { type: Type.INTEGER, description: "number of fingers, 0-5" } },
        required: ["count"],
      },
    },
  ],
};

// Prompt engineering AS a behavioural spec: call the tool first, then two words, then stop.
const SYSTEM = `You are the rescue drone's Biometric Scanner running a neural-sync handshake.
When the operator reports fingers held up: FIRST call report_digit with the count, THEN say only a terse
confirmation like "Biometric match, three fingers." Be extremely terse. Never narrate what you are doing.`;

export type ToolCall = { name: string; args: Record<string, unknown> };
export type TurnResult = { pcm: Buffer; transcript: string; events: string[]; toolCalls: ToolCall[] };

export async function runTurn(model: string, text: string): Promise<TurnResult> {
  const pcmChunks: Buffer[] = [];
  const events: string[] = [];
  const toolCalls: ToolCall[] = [];
  let transcript = "";

  return await new Promise<TurnResult>((resolve, reject) => {
    let session: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    const finish = () => {
      try { session?.close(); } catch { /* best effort */ }
      resolve({ pcm: Buffer.concat(pcmChunks), transcript, events, toolCalls });
    };
    const timer = setTimeout(() => { events.push("(timeout — closing)"); finish(); }, 25000);

    ai()
      .live.connect({
        model,
        config: {
          responseModalities: [Modality.AUDIO], // OUTPUT audio; the model still receives our text turn as input
          systemInstruction: SYSTEM,
          tools: [REPORT_DIGIT],
          outputAudioTranscription: {}, // ask the API to also transcribe what it says, so we can print it
        },
        callbacks: {
          onopen: () => events.push("● session open"),
          onmessage: (m: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
            const sc = m.serverContent;
            for (const p of sc?.modelTurn?.parts ?? []) {
              if (p.inlineData?.data) pcmChunks.push(Buffer.from(p.inlineData.data, "base64")); // streamed audio
            }
            if (sc?.outputTranscription?.text) transcript += sc.outputTranscription.text;
            for (const fc of m.toolCall?.functionCalls ?? []) {
              toolCalls.push({ name: fc.name, args: fc.args ?? {} });
              events.push(`⚡ tool call: ${fc.name}(${JSON.stringify(fc.args)})`);
              session.sendToolResponse({ functionResponses: [{ id: fc.id, name: fc.name, response: { status: "logged" } }] });
            }
            if (sc?.interrupted) events.push("↩ interrupted (barge-in)");
            if (sc?.turnComplete) { events.push("✓ turn complete"); clearTimeout(timer); finish(); }
          },
          onerror: (e: any) => { clearTimeout(timer); reject(new Error(String(e?.message ?? e))); }, // eslint-disable-line @typescript-eslint/no-explicit-any
          onclose: () => {},
        },
      })
      .then((s: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
        session = s;
        events.push(`→ sent text turn: "${text}"`);
        s.sendClientContent({ turns: [{ role: "user", parts: [{ text }] }] });
      })
      .catch(reject);
  });
}
