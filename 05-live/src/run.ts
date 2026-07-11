// Level 5 — open a Gemini Live session, send one turn, watch the events stream back.
//
//   npm run live                                        # default: "…holding up three fingers"
//   npm run live -- "Neural sync online, holding up two fingers"
//
// You get: the event stream (open → tool call → audio → turn complete), the transcript, and out/reply.wav.
import "dotenv/config";
import { mkdirSync, writeFileSync } from "node:fs";
import { authLabel, pickModel } from "./client.js";
import { runTurn } from "./live.js";
import { pcmToWav } from "./wav.js";

const DEFAULT = "Neural sync online. I'm holding up three fingers to the camera.";

async function main() {
  const text = process.argv.slice(2).filter((a) => !a.startsWith("--")).join(" ").trim() || DEFAULT;

  console.log(`\n  auth: ${authLabel()}`);
  console.log("  probing for a Live model this project can open…");
  const model = await pickModel();
  console.log(`  model: ${model}`);

  const r = await runTurn(model, text);

  console.log("\n  ── event stream (this IS the Live loop) ──");
  r.events.forEach((e) => console.log("    " + e));

  console.log(`\n  scanner said: "${r.transcript.trim() || "(no transcript returned)"}"`);
  if (r.toolCalls.length) {
    console.log(`  live tool calls: ${r.toolCalls.map((t) => `${t.name}(${JSON.stringify(t.args)})`).join(", ")}`);
  }

  if (r.pcm.length) {
    mkdirSync("out", { recursive: true });
    writeFileSync("out/reply.wav", pcmToWav(r.pcm));
    console.log(`\n  ✓ out/reply.wav  (~${(r.pcm.length / 48000).toFixed(1)}s of audio) — open it to hear the scanner\n`);
  } else {
    console.log("\n  (no audio chunks came back this turn)\n");
  }
}

main().catch((e) => {
  console.error(`\n  ✗ ${e?.message ?? e}\n`);
  process.exit(1);
});
