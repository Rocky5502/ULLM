#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from ullm.metrics import average_precision, binary_auroc, sampling_uncertainty


def mode_stable(labels: list[str]) -> str:
    counts = {k: labels.count(k) for k in ("True", "False", "Unknown")}
    return max(("True", "False", "Unknown"), key=lambda k: counts[k])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=Path("results/processed/sampling.csv"))
    p.add_argument("--ranking-out", type=Path, default=Path("results/processed/sampling_ranking.csv"))
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
            records.sort(key=lambda r: int(r.get("repeat", 0)))
            labels = [r["prediction"]["label"] for r in records]
            uq = sampling_uncertainty(labels)
            ex = records[0]["example"]
            mode = mode_stable(labels)
            out_rows.append({
                "source": path.name,
                "model": records[0]["model_requested"],
                "protocol": records[0].get("protocol", "legacy"),
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

    ranking_rows = []
    if not df.empty:
        for (model, protocol), g in df.groupby(["model", "protocol"]):
            err = (~g["sample_correct"].astype(bool)).tolist()
            for signal in ("variation_ratio", "label_entropy"):
                scores = g[signal].astype(float).tolist()
                ranking_rows.append({
                    "model": model,
                    "protocol": protocol,
                    "signal": signal,
                    "n": len(g),
                    "error_rate": float(sum(err) / len(err)),
                    "error_AUROC": binary_auroc(err, scores),
                    "error_AUPRC": average_precision(err, scores),
                })
    rdf = pd.DataFrame(ranking_rows)
    rdf.to_csv(args.ranking_out, index=False)
    if not rdf.empty:
        print(rdf.to_string(index=False))
    print(f"\nWrote {args.out} and {args.ranking_out}")


if __name__ == "__main__":
    main()
