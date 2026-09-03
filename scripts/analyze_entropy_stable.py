#!/usr/bin/env python3
"""Cross-platform-stable predictive-entropy ranking for post-run adjudication A2.

This does not alter model probabilities. It only makes mathematically equal entropy
values tie before rank-based metrics, avoiding platform/libm micro-ordering.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from ullm.metrics import average_precision, binary_auroc, excess_aurc, risk_coverage
from ullm.schemas import LABELS


def stable_entropy(prob: dict[str, float]) -> float:
    terms = [
        -float(prob[label]) * math.log(max(float(prob[label]), 1e-12))
        for label in LABELS
    ]
    # Twelve decimals is much finer than the elicited probability precision and only
    # suppresses last-bit numerical ordering among mathematically identical entropies.
    return round(math.fsum(terms) / math.log(len(LABELS)), 12)


def load_rows(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if int(r.get("repeat", 0)) == 0 and r.get("prediction") is not None]


def evaluate(rows: list[dict], scope: str) -> dict[str, float | int | str]:
    idx = list(range(len(rows))) if scope == "all" else [
        i for i, r in enumerate(rows) if r["example"]["group"].startswith("C_")
    ]
    target = [rows[i]["prediction"]["label"] != rows[i]["example"]["label"] for i in idx]
    score = [stable_entropy(rows[i]["prediction"]["probabilities"]) for i in idx]
    correct = [not x for x in target]
    _, _, aurc = risk_coverage(correct, score)
    return {
        "scope": scope,
        "signal": "predictive_entropy",
        "n": len(idx),
        "error_rate": sum(target) / len(target),
        "error_AUROC": binary_auroc(target, score),
        "error_AUPRC": average_precision(target, score),
        "AURC": aurc,
        "E_AURC": excess_aurc(correct, score),
        "entropy_tie_rule": "math.fsum+round12",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=Path("results/processed/predictive_entropy_stable.csv"))
    args = p.parse_args()
    out = []
    for path in args.paths:
        rows = load_rows(path)
        if not rows:
            continue
        model = rows[0]["model_requested"]
        for scope in ("all", "C"):
            row = evaluate(rows, scope)
            row.update(model=model, prompt_type=rows[0].get("prompt_type", "legacy"), source_file=path.name)
            out.append(row)
    frame = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(frame.to_string(index=False))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
