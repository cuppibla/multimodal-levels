# Level 5 · Going Live

> A bidirectional Gemini Live session — streamed audio out, a live tool call, all over one WebSocket.

The real shape from the app's **Realm 05** (its `live/server.mjs` proxy), distilled so it runs in a terminal with **no mic**:

| File | What it is |
|------|-----------|
| [`src/client.ts`](src/client.ts) | connect + **probe** for a Live model that opens |
| [`src/live.ts`](src/live.ts) | one turn: send text → stream audio + transcript + a tool call |
| [`src/wav.ts`](src/wav.ts) | wrap the streamed PCM in a WAV header |

## What "Live" actually is

Not request→response. You **open a session** (a WebSocket) and then events flow both ways until the turn completes:

```
open → [audio chunk] [audio chunk] … + [transcript] + ⚡tool call → turn complete
```

The one turn in [`live.ts`](src/live.ts):

```ts
const session = await ai().live.connect({
  model,
  config: { responseModalities: [Modality.AUDIO], systemInstruction, tools: [REPORT_DIGIT], outputAudioTranscription: {} },
  callbacks: {
    onopen:    () => …,
    onmessage: (m) => {                       // audio chunks, transcript, and…
      for (const fc of m.toolCall?.functionCalls ?? []) session.sendToolResponse(…); // …a LIVE tool call
      if (m.serverContent?.turnComplete) done();
    },
  },
});
session.sendClientContent({ turns: [{ role: "user", parts: [{ text }] }] });  // our one input turn
```

In the app, the browser streams **mic + camera** in on `sendRealtimeInput`, plays the audio out, and the model calls `report_digit` when it *sees* your fingers. Here we send a text turn instead — the session, the streaming, the tool call, the barge-in event are all the same. The key stays server-side; the model is reached over the WebSocket, never from the browser directly.

## Run it

```bash
cp .env.example .env        # add GEMINI_API_KEY, or use your Vertex project
npm install

npm run live                                         # → event stream + out/reply.wav
npm run live -- "Neural sync online, holding up two fingers"
```

Live model names drift by project/region/date, so the module **probes** a list and keeps the first that opens (same trick the app uses). If none open on your account, set `GEMINI_LIVE_MODEL` in `.env`. Open `out/reply.wav` to hear the scanner's spoken confirmation.
