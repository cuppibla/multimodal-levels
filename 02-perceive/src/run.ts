// Level 2 — SEE how a specialist perceives, from the terminal.
//
//   npm run roster                                  # the 3 specialists + their lenses (no API call)
//   npm run perceive -- assets/verdant-soil.png     # Geologist reads the soil, two ways
//   npm run perceive -- assets/verdant-flora.png --who bot
//   npm run perceive -- --crew assets/verdant-soil.png assets/verdant-flora.png assets/verdant-stars.png
//
// Tip: run `npm run samples -- verdant` first to draw a self-consistent crash site into assets/.
import "dotenv/config";
import { readFileSync } from "node:fs";
import { extname } from "node:path";
import { authLabel, READ_MODEL, EMBED_MODEL } from "./client.js";
import { ROSTER, BY_ID, type Perceiver } from "./perceivers.js";
import { perceive, crew, type Reading } from "./perceive.js";

function fileToDataUrl(path: string): string {
  const ext = extname(path).toLowerCase();
  const mime = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : ext === ".webp" ? "image/webp" : "image/png";
  return `data:${mime};base64,${readFileSync(path).toString("base64")}`;
}

function printRoster() {
  console.log(`\n  A specialist = one model (${READ_MODEL}) + one lens + one modality.`);
  console.log("  Same model every time. The lens is the ONLY difference:\n");
  for (const p of ROSTER) {
    console.log(`  ${p.name.padEnd(11)} reads ${p.modality.padEnd(12)} lens → "${p.lens}"`);
  }
  console.log("");
}

function printReading(r: Reading, lens: string) {
  console.log(`\n  ── ${r.who} ──`);
  console.log(`  lens (the prompt): "${lens}"`);
  console.log(`\n  WAY 1 · READ (multimodal, ${READ_MODEL})`);
  console.log(`    "${r.reading}"`);
  console.log(`    → picks ${r.biome}  ·  self-reported confidence ${(r.confidence * 100).toFixed(0)}%`);
  console.log(`\n  WAY 2 · MEASURE (embedding, ${EMBED_MODEL})  — normalised similarity, nearest = 1.00 (a ranking, not a %)`);
  for (const m of r.matches) {
    const bar = "█".repeat(Math.round(m.score * 24)).padEnd(24, "·");
    console.log(`    ${m.name.padEnd(12)} ${bar} ${m.score.toFixed(2)}`);
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--roster") || args.length === 0) return printRoster();

  console.log(`\n  auth: ${authLabel()}`);

  if (args[0] === "--crew") {
    const [soil, flora, stars] = args.slice(1);
    if (!soil || !flora || !stars) throw new Error("--crew needs three images: <soil> <flora> <stars>");
    const picks: { p: Perceiver; image: string }[] = [
      { p: BY_ID.geo, image: fileToDataUrl(soil) },
      { p: BY_ID.bot, image: fileToDataUrl(flora) },
      { p: BY_ID.astro, image: fileToDataUrl(stars) },
    ];
    console.log("\n  fan-out → running 3 specialists at once (Promise.all)…");
    const t0 = Date.now();
    const { readings, vote } = await crew(picks);
    readings.forEach((r) => printReading(r, BY_ID[Object.keys(BY_ID).find((id) => BY_ID[id].name === r.who)!].lens));
    console.log(`\n  wall-clock ${((Date.now() - t0) / 1000).toFixed(1)}s (≈ the slowest single call, not the sum)`);
    console.log(
      vote.reached
        ? `  ◉ CONSENSUS: ${vote.option} — majority ${vote.votes}/${vote.of}\n`
        : `  ⚠ crew split — no majority (${vote.votes}/${vote.of}) → human decides\n`,
    );
    return;
  }

  const imagePath = args.find((a) => !a.startsWith("--"));
  if (!imagePath) throw new Error("pass an image path, e.g. `npm run perceive -- assets/verdant-soil.png`");
  const whoIdx = args.indexOf("--who");
  const who = whoIdx >= 0 ? args[whoIdx + 1] : "geo";
  const p = BY_ID[who];
  if (!p) throw new Error(`unknown specialist "${who}" — use one of: ${ROSTER.map((r) => r.id).join(", ")}`);

  const r = await perceive(fileToDataUrl(imagePath), p);
  printReading(r, p.lens);
  console.log("");
}

main().catch((e) => {
  console.error(`\n  ✗ ${e?.message ?? e}\n`);
  process.exit(1);
});
