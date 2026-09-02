#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from ullm.metrics import average_precision, binary_auroc, sampling_uncertainty

LABEL_ORDER = ("True", "False", "Unknown")


def mode_stable(labels: list[str]) -> str:
    counts = {k: labels.count(k) for k in LABEL_ORDER}
    # deterministic tie break is only for bookkeeping; ties are flagged separately.
    return max(LABEL_ORDER, key=lambda k: counts[k])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--expected-k", type=int, default=5)
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
            counts = {k: labels.count(k) for k in LABEL_ORDER}
            max_count = max(counts.values())
            tie = sum(v == max_count for v in counts.values()) > 1
            out_rows.append({
                "source": path.name,
                "model": records[0]["model_requested"],
                "prompt_type": records[0].get("prompt_type", "legacy"),
                "id": example_id,
                "group": ex["group"],
                "verb": ex["verb"],
                "verb_class": ex["verb_class"],
                "gold": ex["label"],
                "sample_mode": mode,
                "sample_correct": mode == ex["label"],
                "mode_tie": tie,
                "n_samples": len(labels),
                "complete_k": len(labels) == args.expected_k,
                "sample_p_true": counts["True"] / len(labels),
                "sample_p_false": counts["False"] / len(labels),
                "sample_p_unknown": counts["Unknown"] / len(labels),
                **uq,
            })

    df = pd.DataFrame(out_rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    ranking_rows = []
    if not df.empty:
        for (model, prompt_type), g in df.groupby(["model", "prompt_type"]):
            complete = g[g["complete_k"].astype(bool)].copy()
            if complete.empty:
                continue
            err = (~complete["sample_correct"].astype(bool)).tolist()
            for signal in ("variation_ratio", "label_entropy"):
                scores = complete[signal].astype(float).tolist()
                ranking_rows.append({
                    "model": model,
                    "prompt_type": prompt_type,
                    "signal": signal,
                    "n": len(complete),
                    "incomplete_items": int((~g["complete_k"].astype(bool)).sum()),
                    "mode_ties": int(complete["mode_tie"].astype(bool).sum()),
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
