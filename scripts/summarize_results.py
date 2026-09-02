#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import ambiguity_discrimination_gap, aspectual_awareness_gap, ece, group_accuracy, multiclass_brier, nll, semantic_uncertainty_recognition, teleological_bias_rate, teleological_overconfidence_rate


def summarize(path: Path) -> dict:
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = [r for r in rows if r.get("prediction") is not None and int(r.get("repeat", 0)) == 0]
    gold = [r["example"]["label"] for r in rows]
    pred = [r["prediction"]["label"] for r in rows]
    probs = [r["prediction"]["probabilities"] for r in rows]
    groups = [r["example"]["group"] for r in rows]
    ga = group_accuracy(groups, gold, pred)
    return {
        "file": path.name,
        "n": len(rows),
        **{f"acc_{k}": v for k, v in ga.items()},
        "TBR_C": teleological_bias_rate(groups, pred),
        "Delta_AA": aspectual_awareness_gap(groups, gold, pred),
        "SUR": semantic_uncertainty_recognition(groups, probs),
        "TOR@0.80": teleological_overconfidence_rate(groups, probs, 0.80),
        "ADG": ambiguity_discrimination_gap(groups, probs),
        "ECE": ece(gold, pred, probs),
        "Brier": multiclass_brier(gold, probs),
        "NLL": nll(gold, probs),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=Path("results/processed/summary.csv"))
    args = p.parse_args()
    df = pd.DataFrame([summarize(x) for x in args.paths])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
