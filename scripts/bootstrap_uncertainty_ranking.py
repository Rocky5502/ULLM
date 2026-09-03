#!/usr/bin/env python3
"""Verb-cluster bootstrap intervals for RQ2 uncertainty-ranking metrics.

This complements the point-estimate ranking table. Resampling is by lexical verb rather
than templated row so uncertainty claims do not treat A/C or B/D pairs as IID examples.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ullm.metrics import (
    average_precision,
    binary_auroc,
    excess_aurc,
    normalized_entropy,
    risk_coverage,
    verbal_uncertainty,
)


def load_det(path: Path) -> list[dict[str, Any]]:
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


def build_signals(
    rows: list[dict[str, Any]], sampling: pd.DataFrame | None
) -> dict[str, np.ndarray]:
    signals: dict[str, np.ndarray] = {
        "1-maxprob": np.asarray(
            [verbal_uncertainty(r["prediction"]["probabilities"]) for r in rows],
            dtype=float,
        ),
        "predictive_entropy": np.asarray(
            [normalized_entropy(r["prediction"]["probabilities"]) for r in rows],
            dtype=float,
        ),
    }
    if sampling is None or sampling.empty or not rows:
        return signals

    model = rows[0]["model_requested"]
    prompt_type = rows[0].get("prompt_type", "legacy")
    sub = sampling[
        (sampling.model == model) & (sampling.prompt_type == prompt_type)
    ].set_index("id")
    if all(r["example"]["id"] in sub.index for r in rows):
        signals["sampling_variation_ratio"] = np.asarray(
            [float(sub.loc[r["example"]["id"], "variation_ratio"]) for r in rows],
            dtype=float,
        )
        signals["sampling_label_entropy"] = np.asarray(
            [float(sub.loc[r["example"]["id"], "label_entropy"]) for r in rows],
            dtype=float,
        )
    return signals


def metric_bundle(
    rows: list[dict[str, Any]], indices: list[int], scores: np.ndarray
) -> dict[str, float]:
    target = np.asarray(
        [
            rows[i]["prediction"]["label"] != rows[i]["example"]["label"]
            for i in indices
        ],
        dtype=bool,
    )
    scoped_scores = np.asarray([scores[i] for i in indices], dtype=float)
    correct = (~target).tolist()
    _, _, aurc = risk_coverage(correct, scoped_scores.tolist())
    return {
        "error_AUROC": float(binary_auroc(target.tolist(), scoped_scores.tolist())),
        "error_AUPRC": float(average_precision(target.tolist(), scoped_scores.tolist())),
        "AURC": float(aurc),
        "E_AURC": float(excess_aurc(correct, scoped_scores.tolist())),
    }


def scope_indices(rows: list[dict[str, Any]], scope: str) -> list[int]:
    if scope == "all":
        return list(range(len(rows)))
    if scope == "C":
        return [
            i for i, row in enumerate(rows) if row["example"]["group"].startswith("C_")
        ]
    raise ValueError(scope)


def bootstrap_scope(
    rows: list[dict[str, Any]],
    signals: dict[str, np.ndarray],
    *,
    scope: str,
    n_boot: int,
    confidence: float,
    seed: int,
) -> list[dict[str, Any]]:
    idx = scope_indices(rows, scope)
    cluster_to_indices: dict[str, list[int]] = defaultdict(list)
    for i in idx:
        cluster_to_indices[str(rows[i]["example"]["verb"])].append(i)
    clusters = sorted(cluster_to_indices)
    if not clusters:
        return []

    point = {
        signal: metric_bundle(rows, idx, scores) for signal, scores in signals.items()
    }
    metric_names = ("error_AUROC", "error_AUPRC", "AURC", "E_AURC")
    draws = {
        signal: {metric: np.empty(n_boot, dtype=float) for metric in metric_names}
        for signal in signals
    }

    rng = np.random.default_rng(seed)
    for b in range(n_boot):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        sample_idx = [
            i for cluster in sampled for i in cluster_to_indices[str(cluster)]
        ]
        for signal, scores in signals.items():
            values = metric_bundle(rows, sample_idx, scores)
            for metric in metric_names:
                draws[signal][metric][b] = values[metric]

    alpha = 1.0 - confidence
    out: list[dict[str, Any]] = []
    for signal in signals:
        for metric in metric_names:
            values = draws[signal][metric]
            finite = values[np.isfinite(values)]
            if len(finite):
                lo, hi = np.quantile(
                    finite, [alpha / 2.0, 1.0 - alpha / 2.0]
                )
            else:
                lo = hi = float("nan")
            out.append(
                {
                    "scope": scope,
                    "signal": signal,
                    "metric": metric,
                    "estimate": point[signal][metric],
                    "ci_low": float(lo),
                    "ci_high": float(hi),
                    "n_clusters": len(clusters),
                    "n_boot": n_boot,
                    "confidence": confidence,
                }
            )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--sampling", type=Path)
    p.add_argument("--bootstrap", type=int, default=10000)
    p.add_argument("--confidence", type=float, default=0.95)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("results/processed/uncertainty_ranking_bootstrap.csv"),
    )
    args = p.parse_args()

    if args.bootstrap < 1:
        raise SystemExit("--bootstrap must be >= 1")
    if not 0.0 < args.confidence < 1.0:
        raise SystemExit("--confidence must be in (0,1)")

    sampling = (
        pd.read_csv(args.sampling)
        if args.sampling is not None and args.sampling.exists()
        else None
    )

    output: list[dict[str, Any]] = []
    for file_index, path in enumerate(args.paths):
        rows = load_det(path)
        if not rows:
            continue
        model = rows[0]["model_requested"]
        prompt_type = rows[0].get("prompt_type", "legacy")
        signals = build_signals(rows, sampling)
        for scope_index, scope in enumerate(("all", "C")):
            result = bootstrap_scope(
                rows,
                signals,
                scope=scope,
                n_boot=args.bootstrap,
                confidence=args.confidence,
                seed=args.seed + file_index * 1009 + scope_index * 100003,
            )
            for row in result:
                row.update(
                    {
                        "model": model,
                        "prompt_type": prompt_type,
                        "source_file": path.name,
                    }
                )
                output.append(row)

    df = pd.DataFrame(output)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No ranking bootstrap rows produced")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
