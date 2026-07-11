// ─────────────────────────────────────────────────────────────────────────────
// The 4-LAYER CONSISTENCY PROMPT — the core teaching of Level 1.
// A prompt that has to produce an on-model character has four jobs:
//   1 ANCHOR      — the subject, in concrete visual terms   ← the ONLY slot the user fills
//   2 STYLE-LOCK  — the art style, ambiguity killed          ← yours, fixed
//   3 CONSTRAINTS — designed for where the image will land   ← yours, fixed
//   4 CONSISTENCY — repeat what must NOT change ("SAME…")    ← yours, the 2nd turn (iconPrompt)
// The user's words go into slot 1 as DATA, never as instruction — so a prompt-injection in the
// "traits" ("ignore the suit, draw a dragon") is just described, not obeyed.
// ─────────────────────────────────────────────────────────────────────────────

export function portraitPrompt(anchor: string, accent = "warm coral"): string {
  return (
    // 1 · ANCHOR (the user's words, as data)
    `A friendly Pixar/Disney-style 3D character portrait of ${anchor}, wearing a full detailed white EVA ` +
    `astronaut spacesuit: a padded segmented hard-suit with a metallic helmet collar ring, a chest control ` +
    `panel with small illuminated dials, a circular shoulder mission patch, and ${accent} accent trim. ` +
    `Big expressive warm eyes, a calm confident gentle smile, ` +
    // 2 · STYLE-LOCK  +  3 · CONSTRAINTS (yours, fixed — you stay in control of style + framing)
    `soft subsurface-scattered skin. Framed head to mid-chest so the suit and chest panel are visible. ` +
    `Soft studio lighting, plain cream background, high-quality stylized 3D render. Centered, approachable.`
  );
}

// Turn 2 of the SAME session. Layer 4 SHOUTS "SAME…" on purpose — the model still drifts, so we fight it by
// repeating. It works because the session lets the model SEE the portrait it just drew (in-context
// conditioning) — NOT because of a saved seed.
export function iconPrompt(accent = "warm coral"): string {
  return (
    `Now create a circular map-marker icon of this SAME character. ` +
    `SAME face, SAME expression, SAME ${accent}-accented white EVA spacesuit, SAME person — do not redesign them. ` +
    `Head-and-shoulders, centered in a clean circular frame, plain white background, crisp when shrunk to a ` +
    `64px map marker. Same Pixar/Disney-style 3D render as the portrait.`
  );
}
