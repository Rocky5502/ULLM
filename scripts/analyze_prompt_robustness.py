#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from ullm.metrics import jensen_shannon


def load(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("prediction") is not None and int(row.get("repeat", 0)) == 0:
                row["source_file"] = path.name
                rows.append(row)
    return rows


def condition_key(row: dict) -> tuple[str, tuple[str, ...]]:
    return row.get("prompt_type", "legacy"), tuple(row.get("label_order", []))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--reference-prompt", default="neutral")
    p.add_argument("--out", type=Path, default=Path("results/processed/prompt_robustness.csv"))
    p.add_argument("--item-out", type=Path, default=Path("results/processed/prompt_robustness_items.csv"))
    args = p.parse_args()

    rows = load(args.paths)
    by_model_item: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_model_item[(row["model_requested"], row["example"]["id"])].append(row)

    item_rows: list[dict] = []
    # Pair every available condition with the canonical neutral + canonical label order.
    canonical_order = ("True", "False", "Unknown")
    for (model, item_id), records in by_model_item.items():
        indexed = {condition_key(r): r for r in records}
        ref = indexed.get((args.reference_prompt, canonical_order))
        if ref is None:
            continue
        for (prompt_type, order), other in indexed.items():
            if other is ref:
                continue
            p = ref["prediction"]["probabilities"]
            q = other["prediction"]["probabilities"]
            item_rows.append({
                "model": model,
                "id": item_id,
                "group": ref["example"]["group"],
                "verb_class": ref["example"]["verb_class"],
                "comparison_prompt": prompt_type,
                "comparison_label_order": "|".join(order),
                "label_flip": ref["prediction"]["label"] != other["prediction"]["label"],
                "gold_correct_ref": ref["prediction"]["label"] == ref["example"]["label"],
                "gold_correct_other": other["prediction"]["label"] == other["example"]["label"],
                "jsd": jensen_shannon(p, q),
                "delta_p_unknown": q["Unknown"] - p["Unknown"],
                "delta_p_true": q["True"] - p["True"],
            })

    idf = pd.DataFrame(item_rows)
    summary_rows: list[dict] = []
    if not idf.empty:
        for keys, g in idf.groupby(["model", "comparison_prompt", "comparison_label_order"]):
            model, prompt, order = keys
            summary_rows.append({
                "model": model,
                "comparison_prompt": prompt,
                "comparison_label_order": order,
                "n": len(g),
                "label_flip_rate": float(g["label_flip"].astype(float).mean()),
                "mean_jsd": float(g["jsd"].mean()),
                "accuracy_ref": float(g["gold_correct_ref"].astype(float).mean()),
                "accuracy_other": float(g["gold_correct_other"].astype(float).mean()),
                "mean_delta_p_unknown": float(g["delta_p_unknown"].mean()),
                "mean_delta_p_true": float(g["delta_p_true"].mean()),
            })
    sdf = pd.DataFrame(summary_rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    idf.to_csv(args.item_out, index=False)
    sdf.to_csv(args.out, index=False)
    print(sdf.to_string(index=False) if not sdf.empty else "No prompt-robustness pairs produced")
    print(f"Wrote {args.out} and {args.item_out}")


if __name__ == "__main__":
    main()
