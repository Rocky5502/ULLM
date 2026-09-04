#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def argmax_label(probabilities: dict[str, float]) -> str:
    return max(("True", "False", "Unknown"), key=lambda k: float(probabilities[k]))


def analyze(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = [r for r in load_rows(path) if r.get("prediction") is not None]
    if not rows:
        return {}, []

    model = str(rows[0].get("model_requested", ""))
    prompt = str(rows[0].get("prompt_type", "legacy"))
    mismatches: list[dict[str, Any]] = []
    by_group_total: Counter[str] = Counter()
    by_group_bad: Counter[str] = Counter()
    transitions: Counter[str] = Counter()

    for r in rows:
        group = str(r.get("example", {}).get("group", ""))[:1]
        by_group_total[group] += 1
        pred = r["prediction"]
        probs = {k: float(v) for k, v in pred["probabilities"].items()}
        stated = str(pred["label"])
        max_p = max(probs.values())
        max_labels = [k for k, v in probs.items() if abs(v - max_p) <= 1e-12]
        if stated in max_labels:
            continue

        canonical_argmax = argmax_label(probs)
        ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        gap = float(ranked[0][1] - ranked[1][1])
        by_group_bad[group] += 1
        transitions[f"{stated}->{canonical_argmax}"] += 1
        mismatches.append(
            {
                "source_file": path.name,
                "model": model,
                "prompt_type": prompt,
                "id": r.get("example", {}).get("id"),
                "group": r.get("example", {}).get("group"),
                "gold": r.get("example", {}).get("label"),
                "stated_label": stated,
                "argmax_label": canonical_argmax,
                "p_stated": float(probs[stated]),
                "p_argmax": float(probs[canonical_argmax]),
                "top2_gap": gap,
                "stated_correct": stated == r.get("example", {}).get("label"),
                "argmax_correct": canonical_argmax == r.get("example", {}).get("label"),
            }
        )

    n = len(rows)
    bad_n = len(mismatches)
    summary: dict[str, Any] = {
        "source_file": path.name,
        "model": model,
        "prompt_type": prompt,
        "n": n,
        "mismatch_n": bad_n,
        "mismatch_rate": bad_n / n if n else float("nan"),
        "mean_top2_gap_mismatch": (
            sum(float(x["top2_gap"]) for x in mismatches) / bad_n if bad_n else 0.0
        ),
        "max_top2_gap_mismatch": max((float(x["top2_gap"]) for x in mismatches), default=0.0),
        "transition_counts": json.dumps(dict(sorted(transitions.items())), sort_keys=True),
    }
    for letter in "ABCD":
        total = by_group_total.get(letter, 0)
        bad = by_group_bad.get(letter, 0)
        summary[f"mismatch_{letter}_n"] = bad
        summary[f"mismatch_{letter}_rate"] = bad / total if total else float("nan")

    return summary, mismatches


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Quantify schema-valid disagreement between a stated discrete label and "
            "its probability argmax without repairing or deleting responses."
        )
    )
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("results/processed/decision_distribution_consistency.csv"),
    )
    p.add_argument(
        "--items-out",
        type=Path,
        default=Path("results/processed/decision_distribution_consistency_items.csv"),
    )
    args = p.parse_args()

    summaries: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for path in args.paths:
        summary, bad = analyze(path)
        if summary:
            summaries.append(summary)
        items.extend(bad)

    summary_df = pd.DataFrame(summaries)
    item_df = pd.DataFrame(items)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(args.out, index=False)
    item_df.to_csv(args.items_out, index=False)

    if summary_df.empty:
        print("No valid records")
    else:
        cols = ["model", "prompt_type", "n", "mismatch_n", "mismatch_rate", "mean_top2_gap_mismatch"]
        print(summary_df[cols].to_string(index=False))
        print(f"TOTAL mismatches={int(summary_df['mismatch_n'].sum())} / {int(summary_df['n'].sum())}")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.items_out}")


if __name__ == "__main__":
    main()
