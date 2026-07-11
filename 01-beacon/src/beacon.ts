// Two ways to make a character — and why only one stays on-model.
import { ai, IMAGE_MODEL } from "./client.js";
import { portraitPrompt, iconPrompt } from "./identity.js";

function pullImage(res: { candidates?: Array<{ content?: { parts?: Array<{ inlineData?: { data?: string } }> } }> }): Buffer {
  const part = res.candidates?.[0]?.content?.parts?.find((p) => p.inlineData?.data);
  if (!part?.inlineData?.data) throw new Error("no image came back — check the model has image output on your project");
  return Buffer.from(part.inlineData.data, "base64");
}

// ── THE PROBLEM · naive ──────────────────────────────────────────────────────
// Generation is stochastic: two INDEPENDENT stateless calls with the SAME prompt = two different people.
// Run this twice and put the pictures side by side — the identity drifted.
export async function generateOnce(anchor: string, accent?: string): Promise<Buffer> {
  const res = await ai().models.generateContent({
    model: IMAGE_MODEL,
    contents: portraitPrompt(anchor, accent),
    config: { responseModalities: ["TEXT", "IMAGE"] },
  });
  return pullImage(res);
}

// ── THE FIX · one session ────────────────────────────────────────────────────
// Turn 1 draws the portrait. Turn 2 asks for the icon on the SAME chat — so the model can SEE the portrait it
// just drew and match it (in-context conditioning). That's what a "session" IS: replayed history, not a seed.
export async function portraitThenIcon(anchor: string, accent?: string): Promise<{ portrait: Buffer; icon: Buffer }> {
  const chat = ai().chats.create({ model: IMAGE_MODEL, config: { responseModalities: ["TEXT", "IMAGE"] } });

  const p = await chat.sendMessage({ message: portraitPrompt(anchor, accent) }); // turn 1
  const portrait = pullImage(p);

  const i = await chat.sendMessage({ message: iconPrompt(accent) }); //             turn 2, SAME session
  const icon = pullImage(i);

  return { portrait, icon };
}
