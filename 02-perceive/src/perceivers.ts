// ─────────────────────────────────────────────────────────────────────────────
// THE WHOLE POINT OF LEVEL 2, in one file.
//
// A "specialist" is NOT a separate AI, a separate model, or a separate service.
// It is the SAME model (gemini-2.5-flash) + one narrow instruction (the `lens`)
// + one modality (which image it is allowed to look at).
//
// Change the `lens` string  → you get a different specialist.
// Nothing else differs. No training, no fine-tune, no second endpoint.
// ─────────────────────────────────────────────────────────────────────────────

export type Perceiver = {
  id: string;
  name: string;
  modality: string; // the human name of the artifact this specialist reads
  lens: string; //     the ONLY thing that makes a Geologist a Geologist
};

export const ROSTER: Perceiver[] = [
  {
    id: "geo",
    name: "Geologist",
    modality: "soil sample",
    lens: "a planetary geologist judging ONLY the soil/rock texture, colour and mineral cues",
  },
  {
    id: "bot",
    name: "Botanist",
    modality: "flora",
    lens: "a xenobotanist judging ONLY the plant life — leaf form, colour, how it copes with its climate",
  },
  {
    id: "astro",
    name: "Astronomer",
    modality: "star field",
    lens: "an astronomer judging ONLY the sky — star clarity, haze, aurora or ash dimming the field",
  },
];

export const BY_ID = Object.fromEntries(ROSTER.map((p) => [p.id, p])) as Record<string, Perceiver>;
