#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_GROUPS = {
    "A_Interrupted_Accomplishment": (100, "False"),
    "B_Interrupted_Activity": (100, "True"),
    "C_Ambiguous_Accomplishment": (100, "Unknown"),
    "D_Ambiguous_Activity": (100, "True"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    if len(rows) != 400:
        errors.append(f"expected 400 rows, found {len(rows)}")

    ids = [str(r.get("id", "")) for r in rows]
    duplicates = [k for k, v in Counter(ids).items() if v > 1]
    if duplicates:
        errors.append(f"duplicate IDs: {duplicates[:10]}")

    by_group: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        missing = [k for k in ("id", "group", "verb_class", "verb", "premise", "hypothesis", "label") if k not in row]
        if missing:
            errors.append(f"{row.get('id','<no-id>')}: missing fields {missing}")
            continue
        by_group[str(row["group"])].append(row)

    if set(by_group) != set(EXPECTED_GROUPS):
        errors.append(f"unexpected group set: {sorted(by_group)}")
    for group, (n_expected, label_expected) in EXPECTED_GROUPS.items():
        rows_g = by_group.get(group, [])
        if len(rows_g) != n_expected:
            errors.append(f"{group}: expected {n_expected}, found {len(rows_g)}")
        bad_labels = [r["id"] for r in rows_g if r["label"] != label_expected]
        if bad_labels:
            errors.append(f"{group}: wrong labels on {bad_labels[:10]}")

    index = {r.get("id"): r for r in rows}
    for i in range(1, 101):
        suffix = f"{i:03d}"
        for x, y in (("A", "C"), ("B", "D")):
            a, b = index.get(f"{x}_{suffix}"), index.get(f"{y}_{suffix}")
            if a is None or b is None:
                errors.append(f"missing pair {x}_{suffix}/{y}_{suffix}")
                continue
            if a["verb"] != b["verb"]:
                errors.append(f"verb mismatch {x}_{suffix}/{y}_{suffix}: {a['verb']} != {b['verb']}")
            if a["hypothesis"] != b["hypothesis"]:
                errors.append(f"hypothesis mismatch {x}_{suffix}/{y}_{suffix}")
            if a["verb_class"] != b["verb_class"]:
                errors.append(f"verb_class mismatch {x}_{suffix}/{y}_{suffix}")

    expected_ids = {f"{g}_{i:03d}" for g in "ABCD" for i in range(1, 101)}
    if set(ids) != expected_ids:
        missing = sorted(expected_ids - set(ids))
        extra = sorted(set(ids) - expected_ids)
        errors.append(f"ID coverage mismatch; missing={missing[:10]}, extra={extra[:10]}")
    return errors


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("path", nargs="?", type=Path, default=Path("data/imperfectiveNLI.json"))
    p.add_argument("--write-manifest", type=Path, default=Path("data/dataset_manifest.json"))
    args = p.parse_args()

    rows = json.loads(args.path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("Dataset root must be a JSON list")
    errors = validate(rows)
    if errors:
        print("DATASET VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    manifest = {
        "path": str(args.path),
        "sha256": sha256(args.path),
        "n": len(rows),
        "groups": dict(sorted(Counter(r["group"] for r in rows).items())),
        "labels": dict(sorted(Counter(r["label"] for r in rows).items())),
        "verb_classes": dict(sorted(Counter(r["verb_class"] for r in rows).items())),
        "pairing_checks": ["A<->C", "B<->D"],
        "validation": "PASS",
    }
    args.write_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.write_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
