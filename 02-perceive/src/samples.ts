// Draw a self-consistent crash site so Level 2 runs with ZERO external assets.
// One biome → soil + flora + stars that all point to the same answer (so the crew tends to agree).
//
//   npm run samples -- verdant      # → assets/verdant-soil.png, verdant-flora.png, verdant-stars.png
//   npm run samples -- volcanic
//
// Then:  npm run perceive -- assets/verdant-soil.png
import "dotenv/config";
import { mkdirSync, writeFileSync } from "node:fs";
import { ai, IMAGE_MODEL, authLabel } from "./client.js";
import { BIOME_BY_ID, BIOMES } from "./biomes.js";

async function draw(prompt: string): Promise<Buffer> {
  const res = await ai().models.generateContent({ model: IMAGE_MODEL, contents: prompt });
  const parts = res.candidates?.[0]?.content?.parts ?? [];
  const img = parts.find((p) => p.inlineData?.data)?.inlineData;
  if (!img?.data) throw new Error("no image came back — check the model has image output on your project");
  return Buffer.from(img.data, "base64");
}

async function main() {
  const id = (process.argv[2] || "verdant").toLowerCase();
  const biome = BIOME_BY_ID[id];
  if (!biome) throw new Error(`unknown biome "${id}" — use one of: ${BIOMES.map((b) => b.id).join(", ")}`);

  console.log(`\n  auth: ${authLabel()}  ·  model: ${IMAGE_MODEL}`);
  console.log(`  drawing a ${biome.name} crash site (soil · flora · stars)…\n`);
  mkdirSync("assets", { recursive: true });

  for (const modality of ["soil", "flora", "stars"] as const) {
    const buf = await draw(biome.gen[modality]);
    const path = `assets/${biome.id}-${modality}.png`;
    writeFileSync(path, buf);
    console.log(`  ✓ ${path}  (${(buf.length / 1024).toFixed(0)} KB)`);
  }
  console.log(`\n  now run:  npm run perceive -- assets/${biome.id}-soil.png\n`);
}

main().catch((e) => {
  console.error(`\n  ✗ ${e?.message ?? e}\n`);
  process.exit(1);
});
