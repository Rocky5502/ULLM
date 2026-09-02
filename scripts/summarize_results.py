#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import (
    ambiguity_discrimination_gap,
    aspectual_awareness_gap,
    classwise_ece,
    ece,
    group_accuracy,
    multiclass_brier,
    nll,
    paired_condition_consistency,
    semantic_uncertainty_recognition,
    teleological_bias_rate,
    teleological_overconfidence_rate,
)


def _usage(rows: list[dict], key: str) -> float:
    vals = []
    for r in rows:
        u = r.get("usage") or {}
        aliases = {
            "prompt_tokens": ["prompt_tokens", "input_tokens"],
            "completion_tokens": ["completion_tokens", "output_tokens"],
            "total_tokens": ["total_tokens"],
        }[key]
        for a in aliases:
            if u.get(a) is not None:
                vals.append(float(u[a]))
                break
    return float(sum(vals))


def summarize(path: Path, n_bins: int = 15) -> dict:
    all_rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    deterministic = [r for r in all_rows if int(r.get("repeat", 0)) == 0]
    rows = [r for r in deterministic if r.get("prediction") is not None]
    request_failures = sum(bool(r.get("request_error")) for r in deterministic)
    parse_failures = sum((not r.get("request_error")) and r.get("prediction") is None for r in deterministic)
    argmax_inconsistent = sum(
        r.get("prediction") is not None and not r["prediction"].get("argmax_consistent", True)
        for r in deterministic
    )
    gold = [r["example"]["label"] for r in rows]
    pred = [r["prediction"]["label"] for r in rows]
    probs = [r["prediction"]["probabilities"] for r in rows]
    groups = [r["example"]["group"] for r in rows]
    ga = group_accuracy(groups, gold, pred)
    pair = paired_condition_consistency(rows)
    cwe = classwise_ece(gold, probs, n_bins=n_bins)
    denom = len(deterministic) or 1
    return {
        "file": path.name,
        "model": rows[0]["model_requested"] if rows else (deterministic[0].get("model_requested", "") if deterministic else ""),
        "prompt_type": rows[0].get("prompt_type", "legacy") if rows else (deterministic[0].get("prompt_type", "legacy") if deterministic else ""),
        "n_expected_records": len(deterministic),
        "n_valid": len(rows),
        "request_failure_rate": request_failures / denom,
        "parse_failure_rate": parse_failures / denom,
        "argmax_inconsistency_rate": argmax_inconsistent / denom,
        **{f"acc_{k}": v for k, v in ga.items()},
        "TBR_C": teleological_bias_rate(groups, pred),
        "Delta_AA": aspectual_awareness_gap(groups, gold, pred),
        "SUR": semantic_uncertainty_recognition(groups, probs),
        "TOR@0.80": teleological_overconfidence_rate(groups, probs, 0.80),
        "ADG": ambiguity_discrimination_gap(groups, probs),
        "ECE": ece(gold, pred, probs, n_bins=n_bins),
        "ECE_True": cwe["True"],
        "ECE_False": cwe["False"],
        "ECE_Unknown": cwe["Unknown"],
        "Brier": multiclass_brier(gold, probs),
        "NLL": nll(gold, probs),
        "pair_AC_both_correct": pair["AC"],
        "pair_BD_both_correct": pair["BD"],
        "prompt_tokens": _usage(rows, "prompt_tokens"),
        "completion_tokens": _usage(rows, "completion_tokens"),
        "total_tokens": _usage(rows, "total_tokens"),
        "mean_latency_s": sum(float(r.get("latency_s") or 0.0) for r in rows) / len(rows) if rows else float("nan"),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=Path("results/processed/summary.csv"))
    p.add_argument("--bins", type=int, default=15)
    args = p.parse_args()
    df = pd.DataFrame([summarize(x, n_bins=args.bins) for x in args.paths])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
