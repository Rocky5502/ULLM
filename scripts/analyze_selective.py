#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import confidence_uncertainty, normalized_entropy, risk_coverage


def load_det(path: Path) -> list[dict]:
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if r.get("prediction") is not None and int(r.get("repeat", 0)) == 0]


def at_coverage(records: list[dict], uncertainty: list[float], target: float) -> dict[str, float]:
    order = sorted(range(len(records)), key=lambda i: uncertainty[i])
    k = max(1, min(len(records), round(target * len(records))))
    kept = [records[i] for i in order[:k]]
    err = [r["prediction"]["label"] != r["example"]["label"] for r in kept]
    c = [r for r in kept if r["example"]["group"].startswith("C_")]
    d = [r for r in kept if r["example"]["group"].startswith("D_")]
    tbr = sum(r["prediction"]["label"] == "True" for r in c) / len(c) if c else float("nan")
    d_acc = sum(r["prediction"]["label"] == "True" for r in d) / len(d) if d else float("nan")
    return {"coverage": k / len(records), "risk": sum(err) / len(err), "TBR_C": tbr, "group_D_retention_accuracy": d_acc, "n_kept": k}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--sampling", type=Path, default=None)
    p.add_argument("--out", type=Path, default=Path("results/processed/selective.csv"))
    p.add_argument("--coverages", nargs="+", type=float, default=[1.0, 0.9, 0.8, 0.7, 0.5])
    args = p.parse_args()

    sampling = pd.read_csv(args.sampling) if args.sampling and args.sampling.exists() else None
    out = []
    for path in args.paths:
        rows = load_det(path)
        if not rows:
            continue
        model, protocol = rows[0]["model_requested"], rows[0].get("protocol", "legacy")
        correct = [r["prediction"]["label"] == r["example"]["label"] for r in rows]
        signals = {
            "1-maxprob": [confidence_uncertainty(r["prediction"]["probabilities"]) for r in rows],
            "predictive_entropy": [normalized_entropy(r["prediction"]["probabilities"]) for r in rows],
        }
        if sampling is not None:
            sub = sampling[(sampling.model == model) & (sampling.protocol == protocol)].set_index("id")
            if all(r["example"]["id"] in sub.index for r in rows):
                signals["sampling_variation_ratio"] = [float(sub.loc[r["example"]["id"], "variation_ratio"]) for r in rows]
                signals["sampling_label_entropy"] = [float(sub.loc[r["example"]["id"], "label_entropy"]) for r in rows]
        for name, scores in signals.items():
            _, _, aurc = risk_coverage(correct, scores)
            for target in args.coverages:
                out.append({"model": model, "protocol": protocol, "signal": name, "AURC": aurc, **at_coverage(rows, scores, target)})

    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No selective rows produced")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
