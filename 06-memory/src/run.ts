// Level 6 — give the rescue AI durable, cross-session memory.
//
//   npm run remember -- "Vega-7 here. I get overwhelmed by long checklists — one step at a time please."
//   npm run recall   -- "how should I brief this operator?"
//   npm run demo                      # a canned transcript → extract → recall, end to end
//   npm run forget                    # wipe memory.json
//
// `remember` and `recall` are separate processes — the facts persist in memory.json between them.
import "dotenv/config";
import { authLabel } from "./client.js";
import { extractFacts, recall, type Fact } from "./memory.js";
import { load, save, clear } from "./store.js";

const DEMO_TRANSCRIPT =
  "Operator: This is Vega-7, do you copy? Look, I'll be honest — long checklists make me freeze up, " +
  "just give me one step at a time. My oxygen recycler has been throwing error 42 since the crash, and " +
  "my daughter Mira is waiting for me back home. Let's get to work.";

function show(facts: Fact[]) {
  for (const f of facts) {
    const tag = f.kind === "exact" ? "EXACT  " : "PATTERN";
    console.log(`    [${tag}] ${f.label}: ${f.value}`);
  }
}

async function doRemember(transcript: string) {
  console.log("\n  WRITE — reading the transcript into durable facts…");
  const fresh = await extractFacts(transcript);
  const all = [...load(), ...fresh];
  save(all);
  console.log(`  extracted ${fresh.length}, memory now holds ${all.length}:`);
  show(fresh);
  console.log("");
}

async function doRecall(query: string) {
  const facts = load();
  if (!facts.length) return console.log("\n  (memory is empty — run `npm run remember` or `npm run demo` first)\n");
  console.log(`\n  READ — recalling for: "${query}"`);
  const ranked = await recall(query, facts);
  console.log("  exact facts always surfaced; patterns ranked by meaning:\n");
  for (const { fact, score } of ranked) {
    const tag = fact.kind === "exact" ? "EXACT  " : `${score.toFixed(2)}`;
    console.log(`    [${tag.padEnd(7)}] ${fact.label}: ${fact.value}`);
  }
  console.log("");
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  console.log(`  auth: ${authLabel()}`);

  if (cmd === "forget") {
    clear();
    return console.log("\n  memory.json wiped.\n");
  }
  if (cmd === "demo") {
    await doRemember(DEMO_TRANSCRIPT);
    await doRecall("how should I greet and brief this operator next time?");
    return;
  }
  if (cmd === "remember") {
    const t = rest.join(" ").trim();
    if (!t) throw new Error('give a transcript: npm run remember -- "…what the operator said…"');
    return doRemember(t);
  }
  if (cmd === "recall") {
    const q = rest.join(" ").trim();
    if (!q) throw new Error('give a query: npm run recall -- "how should I brief them?"');
    return doRecall(q);
  }
  throw new Error("usage: remember <transcript> | recall <query> | demo | forget");
}

main().catch((e) => {
  console.error(`\n  ✗ ${e?.message ?? e}\n`);
  process.exit(1);
});
