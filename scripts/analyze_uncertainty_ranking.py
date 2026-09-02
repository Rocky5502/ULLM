#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import (
    average_precision,
    binary_auroc,
    excess_aurc,
    normalized_entropy,
    risk_coverage,
    verbal_uncertainty,
)


def load_det(path: Path) -> list[dict]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [
        r
        for r in rows
        if int(r.get("repeat", 0)) == 0 and r.get("prediction") is not None
    ]


def evaluate_scope(
    rows: list[dict],
    signal_name: str,
    scores: list[float],
    scope: str,
) -> dict[str, float | int | str]:
    if scope == "all":
        idx = list(range(len(rows)))
    elif scope == "C":
        idx = [
            i for i, r in enumerate(rows) if r["example"]["group"].startswith("C_")
        ]
    else:
        raise ValueError(scope)

    target = [
        rows[i]["prediction"]["label"] != rows[i]["example"]["label"] for i in idx
    ]
    scoped_scores = [scores[i] for i in idx]
    correct = [not x for x in target]
    _, _, aurc = risk_coverage(correct, scoped_scores)
    return {
        "scope": scope,
        "signal": signal_name,
        "n": len(idx),
        "error_rate": sum(target) / len(target) if target else float("nan"),
        "error_AUROC": binary_auroc(target, scoped_scores),
        "error_AUPRC": average_precision(target, scoped_scores),
        "AURC": aurc,
        "E_AURC": excess_aurc(correct, scoped_scores),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--sampling", type=Path)
    p.add_argument(
        "--out", type=Path, default=Path("results/processed/uncertainty_ranking.csv")
    )
    args = p.parse_args()

    sampling = (
        pd.read_csv(args.sampling)
        if args.sampling is not None and args.sampling.exists()
        else None
    )

    out: list[dict] = []
    for path in args.paths:
        rows = load_det(path)
        if not rows:
            continue
        model = rows[0]["model_requested"]
        prompt_type = rows[0].get("prompt_type", "legacy")
        signals: dict[str, list[float]] = {
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

        for signal_name, scores in signals.items():
            for scope in ("all", "C"):
                result = evaluate_scope(rows, signal_name, scores, scope)
                result.update(
                    {
                        "model": model,
                        "prompt_type": prompt_type,
                        "source_file": path.name,
                    }
                )
                out.append(result)

    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No ranking rows produced")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
