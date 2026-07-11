// Level 1 — generate an explorer identity, and keep it consistent.
//
//   npm run prompt                              # print the 4-layer prompt (no API call)
//   npm run identity -- "a cheerful botanist with round glasses"   # portrait + matching icon (SAME session)
//   npm run naive -- "a cheerful botanist with round glasses"      # two stateless portraits → they drift
import "dotenv/config";
import { mkdirSync, writeFileSync } from "node:fs";
import { authLabel, IMAGE_MODEL } from "./client.js";
import { portraitPrompt, iconPrompt } from "./identity.js";
import { generateOnce, portraitThenIcon } from "./beacon.js";

const DEFAULT_ANCHOR = "a cheerful young explorer with freckles and short curly hair";

function anchorFrom(args: string[]): string {
  const a = args.filter((x) => !x.startsWith("--")).join(" ").trim();
  return a || DEFAULT_ANCHOR;
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--prompt")) {
    const anchor = anchorFrom(args);
    console.log("\n  The 4-layer consistency prompt (your words fill ONLY layer 1):\n");
    console.log("  ── PORTRAIT (turns 1) ──");
    console.log("  " + portraitPrompt(anchor).replace(/\. /g, ".\n  "));
    console.log("\n  ── ICON (turn 2, layer 4 = the SAME… demand) ──");
    console.log("  " + iconPrompt().replace(/\. /g, ".\n  ") + "\n");
    return;
  }

  mkdirSync("out", { recursive: true });
  const anchor = anchorFrom(args);
  console.log(`\n  auth: ${authLabel()}  ·  model: ${IMAGE_MODEL}`);
  console.log(`  anchor: "${anchor}"\n`);

  if (args.includes("--naive")) {
    console.log("  THE PROBLEM — two independent stateless calls, same prompt:");
    for (const n of [1, 2]) {
      const buf = await generateOnce(anchor);
      writeFileSync(`out/naive-${n}.png`, buf);
      console.log(`    ✓ out/naive-${n}.png  (${(buf.length / 1024).toFixed(0)} KB)`);
    }
    console.log("\n  → open them side by side: same prompt, two different people. Identity drifted.\n");
    return;
  }

  console.log("  THE FIX — turn 1 portrait, turn 2 icon on the SAME session:");
  const { portrait, icon } = await portraitThenIcon(anchor);
  writeFileSync("out/portrait.png", portrait);
  writeFileSync("out/icon.png", icon);
  console.log(`    ✓ out/portrait.png  (${(portrait.length / 1024).toFixed(0)} KB)`);
  console.log(`    ✓ out/icon.png      (${(icon.length / 1024).toFixed(0)} KB)`);
  console.log("\n  → the icon matches the portrait: same face, same suit. The session carried the identity.\n");
}

main().catch((e) => {
  console.error(`\n  ✗ ${e?.message ?? e}\n`);
  process.exit(1);
});
