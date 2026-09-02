#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

EXPECTED_LABEL = {"A": "False", "B": "True", "C": "Unknown", "D": "True"}
EXPECTED_N = 100


def letter(group: str) -> str:
    return group.split("_", 1)[0]


def validate(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    ids = [r.get("id") for r in rows]
    if len(rows) != 400:
        errors.append(f"expected 400 examples, found {len(rows)}")
    if len(set(ids)) != len(ids):
        errors.append("example IDs are not unique")

    counts = Counter(letter(str(r.get("group", ""))) for r in rows)
    for g in "ABCD":
        if counts[g] != EXPECTED_N:
            errors.append(f"Group {g}: expected {EXPECTED_N}, found {counts[g]}")

    for r in rows:
        g = letter(str(r.get("group", "")))
        if g in EXPECTED_LABEL and r.get("label") != EXPECTED_LABEL[g]:
            errors.append(f"{r.get('id')}: Group {g} must have label {EXPECTED_LABEL[g]}")

    by_id = {str(r["id"]): r for r in rows if "id" in r}
    for i in range(1, 101):
        suffix = f"{i:03d}"
        for left, right in (("A", "C"), ("B", "D")):
            a, b = by_id.get(f"{left}_{suffix}"), by_id.get(f"{right}_{suffix}")
            if not a or not b:
                errors.append(f"missing pair {left}_{suffix}/{right}_{suffix}")
                continue
            if a.get("verb") != b.get("verb"):
                errors.append(f"verb mismatch in pair {left}_{suffix}/{right}_{suffix}")
            if a.get("hypothesis") != b.get("hypothesis"):
                errors.append(f"hypothesis mismatch in pair {left}_{suffix}/{right}_{suffix}")
    return errors


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("path", nargs="?", type=Path, default=Path("data/imperfectiveNLI.json"))
    args = p.parse_args()
    rows = json.loads(args.path.read_text(encoding="utf-8"))
    errors = validate(rows)
    if errors:
        print("Dataset validation FAILED:")
        for e in errors[:30]:
            print(f" - {e}")
        if len(errors) > 30:
            print(f" ... and {len(errors) - 30} more")
        raise SystemExit(1)
    print("Dataset validation OK: 400 unique examples, 100/group, labels and A/C + B/D pairings verified.")


if __name__ == "__main__":
    main()
