// The reference library the MEASURE step matches a reading against (nearest-neighbour in vector space),
// and the prompts `samples.ts` uses to draw a self-consistent crash site so you can run with ZERO assets.
export type Biome = {
  id: string;
  name: string;
  ref: string; // what MEASURE compares the reading's embedding against
  gen: { soil: string; flora: string; stars: string }; // per-modality image prompts (one site, one answer)
};

export const BIOMES: Biome[] = [
  {
    id: "cryo",
    name: "Cryo",
    ref: "frozen ice plains, pale blue frost crystals, sub-zero glacial regolith, snow and rime, brittle icy ground",
    gen: {
      soil: "Extreme macro top-down photo of an alien SOIL sample: pale blue-grey frozen regolith crusted with white frost and tiny ice crystals, scientific flat-lay on a neutral tray, cold clinical lighting.",
      flora: "A single hardy alien plant in snow: frost-dusted blue-green succulent leaves, ice crystals on the edges, sparse cold tundra, muted wintry light.",
      stars: "A crisp night sky over a frozen glacial horizon: sharp cold white stars, faint pale-blue aurora, thin frozen air, dark sky.",
    },
  },
  {
    id: "volcanic",
    name: "Volcanic",
    ref: "molten basalt, black igneous rock, ash fields, glowing lava cracks, sulfur, scorched volcanic ground",
    gen: {
      soil: "Extreme macro top-down photo of an alien SOIL sample: black basaltic volcanic rock and grey ash, glowing orange lava cracks between chunks, sulfur-yellow flecks, scientific flat-lay, dramatic ember glow.",
      flora: "A scorched alien plant near lava: charred dark red leathery leaves, ember-lit edges, ash-covered stems, smoke haze, hot orange rim light.",
      stars: "A night sky above an erupting volcanic horizon: stars dimmed by drifting ash and smoke, orange lava glow on the horizon, reddish haze.",
    },
  },
  {
    id: "verdant",
    name: "Verdant",
    ref: "lush green jungle vegetation, ferns, humid rainforest, dense flora, rich dark loam soil, mossy growth",
    gen: {
      soil: "Extreme macro top-down photo of an alien SOIL sample: rich dark brown loam threaded with green moss and fine white root hairs, damp and fertile, scientific flat-lay, soft humid light.",
      flora: "A lush alien fern in a humid jungle: vivid green fronds, dew drops, dense overlapping foliage, soft dappled sunlight, thriving growth.",
      stars: "A night sky glimpsed through a dense jungle canopy: warm stars scattered between dark leafy silhouettes, humid haze, faint green airglow.",
    },
  },
  {
    id: "arid",
    name: "Arid Desert",
    ref: "dry red sand dunes, cracked parched earth, sparse scrub, fine dust, intense heat, barren desert",
    gen: {
      soil: "Extreme macro top-down photo of an alien SOIL sample: fine red-orange desert sand and cracked dry clay flakes, a few tiny pebbles, bone-dry, scientific flat-lay, harsh warm light.",
      flora: "A lone drought-hardy alien plant in a desert: pale spiny succulent, waxy grey-green skin, cracked red earth around it, harsh sun, long shadow.",
      stars: "A vast clear night sky over red desert dunes: brilliant dense starfield, no haze, dry thin air, deep black sky, a low dune horizon.",
    },
  },
];

export const BIOME_NAMES = BIOMES.map((b) => b.name);
export const BIOME_BY_ID = Object.fromEntries(BIOMES.map((b) => [b.id, b])) as Record<string, Biome>;
