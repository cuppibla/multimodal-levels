// The "durable" part of memory — a plain JSON file on disk. Nothing clever: this IS the cross-session store.
// Run `remember` in one process, `recall` in another, and the facts survive between them. That's persistence.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import type { Fact } from "./memory.js";

const FILE = "memory.json";

export function load(): Fact[] {
  if (!existsSync(FILE)) return [];
  try {
    return JSON.parse(readFileSync(FILE, "utf8")) as Fact[];
  } catch {
    return [];
  }
}

export function save(facts: Fact[]): void {
  writeFileSync(FILE, JSON.stringify(facts, null, 2));
}

export function clear(): void {
  writeFileSync(FILE, "[]");
}
