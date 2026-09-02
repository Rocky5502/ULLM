#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import (
    excess_aurc,
    normalized_entropy,
    risk_coverage,
    select_indices_at_coverage,
    threshold_risk_coverage,
    verbal_uncertainty,
)


def load_det(path: Path) -> list[dict]:
    rows = [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    return [
        r
        for r in rows
        if r.get("prediction") is not None and int(r.get("repeat", 0)) == 0
    ]


def at_coverage(
    records: list[dict], uncertainty: list[float], target: float
) -> dict[str, float]:
    indices, achieved, boundary = select_indices_at_coverage(uncertainty, target)
    kept = [records[i] for i in indices]
    kept_ids = {r["example"]["id"] for r in kept}
    err = [
        r["prediction"]["label"] != r["example"]["label"] for r in kept
    ]
    c_all = [r for r in records if r["example"]["group"].startswith("C_")]
    d_all = [r for r in records if r["example"]["group"].startswith("D_")]
    c = [r for r in c_all if r["example"]["id"] in kept_ids]
    d = [r for r in d_all if r["example"]["id"] in kept_ids]
    tbr = (
        sum(r["prediction"]["label"] == "True" for r in c) / len(c)
        if c
        else float("nan")
    )
    d_acc = (
        sum(r["prediction"]["label"] == "True" for r in d) / len(d)
        if d
        else float("nan")
    )
    return {
        "target_coverage": target,
        "coverage": achieved,
        "uncertainty_threshold": boundary,
        "risk": sum(err) / len(err) if err else float("nan"),
        "TBR_C": tbr,
        "group_C_coverage": len(c) / len(c_all) if c_all else float("nan"),
        "group_D_retention_accuracy": d_acc,
        "group_D_coverage": len(d) / len(d_all) if d_all else float("nan"),
        "n_kept": len(kept),
    }


def coverage_at_risk(
    records: list[dict], uncertainty: list[float], target_risk: float
) -> float:
    correct = [
        r["prediction"]["label"] == r["example"]["label"] for r in records
    ]
    coverages, risks, _ = threshold_risk_coverage(correct, uncertainty)
    feasible = [float(c) for c, r in zip(coverages, risks) if r <= target_risk]
    return max(feasible) if feasible else 0.0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--sampling", type=Path, default=None)
    p.add_argument(
        "--out", type=Path, default=Path("results/processed/selective.csv")
    )
    p.add_argument(
        "--coverages", nargs="+", type=float, default=[1.0, 0.9, 0.8, 0.7, 0.5]
    )
    p.add_argument(
        "--target-risks", nargs="+", type=float, default=[0.10, 0.05]
    )
    args = p.parse_args()

    sampling = (
        pd.read_csv(args.sampling)
        if args.sampling and args.sampling.exists()
        else None
    )
    out = []
    for path in args.paths:
        rows = load_det(path)
        if not rows:
            continue
        model = rows[0]["model_requested"]
        prompt_type = rows[0].get("prompt_type", "legacy")
        correct = [
            r["prediction"]["label"] == r["example"]["label"] for r in rows
        ]
        signals = {
            "1-maxprob": [
                verbal_uncertainty(r["prediction"]["probabilities"]) for r in rows
            ],
            "predictive_entropy": [
                normalized_entropy(r["prediction"]["probabilities"]) for r in rows
            ],
        }
        if sampling is not None and not sampling.empty:
            sub = sampling[
                (sampling.model == model) & (sampling.prompt_type == prompt_type)
            ].set_index("id")
            if all(r["example"]["id"] in sub.index for r in rows):
                signals["sampling_variation_ratio"] = [
                    float(sub.loc[r["example"]["id"], "variation_ratio"])
                    for r in rows
                ]
                signals["sampling_label_entropy"] = [
                    float(sub.loc[r["example"]["id"], "label_entropy"])
                    for r in rows
                ]

        for name, scores in signals.items():
            _, _, aurc = risk_coverage(correct, scores)
            eaurc = excess_aurc(correct, scores)
            target_coverages = {
                f"coverage_at_risk_{r:.2f}": coverage_at_risk(rows, scores, r)
                for r in args.target_risks
            }
            for target in args.coverages:
                out.append(
                    {
                        "model": model,
                        "prompt_type": prompt_type,
                        "signal": name,
                        "AURC": aurc,
                        "E_AURC": eaurc,
                        **target_coverages,
                        **at_coverage(rows, scores, target),
                    }
                )

    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No selective rows produced")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
