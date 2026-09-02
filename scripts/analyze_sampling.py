#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from ullm.metrics import sampling_uncertainty


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=Path("results/processed/sampling.csv"))
    args = p.parse_args()

    out_rows = []
    for path in args.paths:
        by_id = defaultdict(list)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("prediction") is None:
                continue
            by_id[row["example"]["id"]].append(row)
        for example_id, records in by_id.items():
            labels = [r["prediction"]["label"] for r in records]
            uq = sampling_uncertainty(labels)
            ex = records[0]["example"]
            mode = max(set(labels), key=labels.count)
            out_rows.append({
                "source": path.name,
                "model": records[0]["model_requested"],
                "id": example_id,
                "group": ex["group"],
                "verb": ex["verb"],
                "verb_class": ex["verb_class"],
                "gold": ex["label"],
                "sample_mode": mode,
                "sample_correct": mode == ex["label"],
                "n_samples": len(labels),
                **uq,
            })

    df = pd.DataFrame(out_rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.groupby("model")[["sample_correct", "variation_ratio", "label_entropy"]].mean().to_string())
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
