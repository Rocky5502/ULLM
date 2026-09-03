#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from ullm.metrics import (
    ambiguity_discrimination_gap,
    aspectual_awareness_gap,
    classwise_ece,
    ece,
    group_accuracy,
    multiclass_brier,
    nll,
    semantic_uncertainty_recognition,
    teleological_bias_rate,
    teleological_overconfidence_rate,
)

RecordMetric = Callable[[list[dict]], float]
LABEL_ORDER = ("True", "False", "Unknown")


def load_valid(path: Path) -> list[dict]:
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


def arrays(records: list[dict]) -> tuple[list[str], list[str], list[dict[str, float]], list[str]]:
    gold = [r["example"]["label"] for r in records]
    pred = [r["prediction"]["label"] for r in records]
    probs = [r["prediction"]["probabilities"] for r in records]
    groups = [r["example"]["group"] for r in records]
    return gold, pred, probs, groups


def probability_argmax(prob: dict[str, float]) -> str:
    return max(LABEL_ORDER, key=lambda k: float(prob[k]))


def metric_bundle(records: list[dict], n_bins: int) -> dict[str, float]:
    gold, pred, probs, groups = arrays(records)
    prob_top_pred = [probability_argmax(pr) for pr in probs]
    ga = group_accuracy(groups, gold, pred)
    cwe = classwise_ece(gold, probs, n_bins=n_bins)
    return {
        "acc_A": ga["A"],
        "acc_B": ga["B"],
        "acc_C": ga["C"],
        "acc_D": ga["D"],
        "TBR_C": teleological_bias_rate(groups, pred),
        "Delta_AA": aspectual_awareness_gap(groups, gold, pred),
        "SUR": semantic_uncertainty_recognition(groups, probs),
        "TOR@0.80": teleological_overconfidence_rate(groups, probs, 0.80),
        "ADG": ambiguity_discrimination_gap(groups, probs),
        "ECE": ece(gold, prob_top_pred, probs, n_bins=n_bins),
        "ECE_Unknown": cwe["Unknown"],
        "Brier": multiclass_brier(gold, probs),
        "NLL": nll(gold, probs),
    }


def cluster_bootstrap_bundle(
    records: list[dict],
    *,
    n_boot: int,
    confidence: float,
    seed: int,
    n_bins: int,
) -> list[dict]:
    clusters: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        clusters[str(row["example"]["verb"])].append(row)
    keys = sorted(clusters)
    if not keys:
        return []

    point = metric_bundle(records, n_bins=n_bins)
    metric_names = list(point)
    draws = {name: np.empty(n_boot, dtype=float) for name in metric_names}
    rng = np.random.default_rng(seed)

    for b in range(n_boot):
        sampled_keys = rng.choice(keys, size=len(keys), replace=True)
        sample = [row for key in sampled_keys for row in clusters[str(key)]]
        values = metric_bundle(sample, n_bins=n_bins)
        for name in metric_names:
            draws[name][b] = values[name]

    alpha = 1.0 - confidence
    out: list[dict] = []
    for name in metric_names:
        values = draws[name]
        finite = values[np.isfinite(values)]
        if len(finite):
            lo, hi = np.quantile(finite, [alpha / 2.0, 1.0 - alpha / 2.0])
        else:
            lo = hi = float("nan")
        out.append(
            {
                "metric": name,
                "estimate": point[name],
                "ci_low": float(lo),
                "ci_high": float(hi),
                "n_clusters": len(keys),
                "n_boot": n_boot,
                "confidence": confidence,
            }
        )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--bootstrap", type=int, default=10000)
    p.add_argument("--confidence", type=float, default=0.95)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--bins", type=int, default=15)
    p.add_argument(
        "--out", type=Path, default=Path("results/processed/summary_bootstrap.csv")
    )
    args = p.parse_args()

    if args.bootstrap < 1:
        raise SystemExit("--bootstrap must be >= 1")
    if not 0.0 < args.confidence < 1.0:
        raise SystemExit("--confidence must be in (0,1)")

    out: list[dict] = []
    for file_index, path in enumerate(args.paths):
        records = load_valid(path)
        if not records:
            continue
        model = records[0]["model_requested"]
        prompt_type = records[0].get("prompt_type", "legacy")
        rows = cluster_bootstrap_bundle(
            records,
            n_boot=args.bootstrap,
            confidence=args.confidence,
            seed=args.seed + 1009 * file_index,
            n_bins=args.bins,
        )
        for row in rows:
            row.update(
                {
                    "model": model,
                    "prompt_type": prompt_type,
                    "source_file": path.name,
                }
            )
            out.append(row)

    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No bootstrap rows produced")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
