"""Level 1 · Beat 7 — "Models create. Code judges."

Generation is probabilistic; the gate is CODE. Whether you're "on the map" is a
deterministic check your code can verify — never "does the model think it's good?".

Run:   uv run python verify.py
"""
import os
import sys

from PIL import Image

CHECKS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  {'✓' if ok else '✗'} {label}" + (f" — {detail}" if detail else ""))


def main() -> None:
    print("\n  deterministic gate — code judges:\n")

    for name in ("portrait", "icon"):
        path = f"outputs/{name}.png"
        exists = os.path.exists(path)
        check(f"{name} exists", exists, path)
        if not exists:
            continue
        try:
            img = Image.open(path)
            img.verify()  # decodable = a real image came back
            img = Image.open(path)
            check(f"{name} is a valid image", True, f"{img.size[0]}×{img.size[1]}")
            if name == "icon":
                w, h = img.size
                check("icon is square (map-marker spec)", abs(w - h) <= max(w, h) * 0.05, f"{w}×{h}")
        except Exception as e:  # noqa: BLE001
            check(f"{name} is a valid image", False, str(e))

    failed = [c for c in CHECKS if not c[1]]
    print()
    if failed:
        print(f"  ✗ GATE CLOSED — {len(failed)} check(s) failed. Regenerate and retry.\n")
        sys.exit(1)
    print("  ◉ BEACON REGISTERED — probabilistic creation, deterministic verification.\n")


if __name__ == "__main__":
    main()
