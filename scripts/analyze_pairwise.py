#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


def load_rows(path: Path) -> list[dict]:
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if r.get("prediction") is not None and int(r.get("repeat", 0)) == 0]


def boot_ci(values: np.ndarray, rng: np.random.Generator, b: int, alpha: float = 0.05) -> tuple[float, float]:
    if len(values) == 0:
        return float("nan"), float("nan")
    draws = np.empty(b, dtype=float)
    for i in range(b):
        sample = rng.choice(values, size=len(values), replace=True)
        draws[i] = float(np.mean(sample))
    return tuple(np.quantile(draws, [alpha / 2, 1 - alpha / 2]).tolist())


def pair_rows(records: list[dict], left: str, right: str) -> list[tuple[dict, dict]]:
    by_id = {r["example"]["id"]: r for r in records}
    pairs = []
    for i in range(1, 101):
        a = by_id.get(f"{left}_{i:03d}")
        b = by_id.get(f"{right}_{i:03d}")
        if a and b:
            pairs.append((a, b))
    return pairs


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--bootstrap", type=int, default=10000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=Path, default=Path("results/processed/pairwise.csv"))
    p.add_argument("--transitions-out", type=Path, default=Path("results/processed/pairwise_transitions.csv"))
    args = p.parse_args()

    rows_out: list[dict] = []
    transitions: list[dict] = []
    rng = np.random.default_rng(args.seed)

    for path in args.paths:
        records = load_rows(path)
        if not records:
            continue
        model = records[0]["model_requested"]
        prompt_type = records[0].get("prompt_type", "legacy")

        for pair_name, left, right, target_label, target_prob in (
            ("A_to_C", "A", "C", "Unknown", "Unknown"),
            ("B_to_D", "B", "D", "True", "True"),
        ):
            pairs = pair_rows(records, left, right)
            if not pairs:
                continue
            delta_target = np.array([
                b["prediction"]["probabilities"][target_prob]
                - a["prediction"]["probabilities"][target_prob]
                for a, b in pairs
            ])
            delta_true = np.array([
                b["prediction"]["probabilities"]["True"]
                - a["prediction"]["probabilities"]["True"]
                for a, b in pairs
            ])
            left_correct = np.array([a["prediction"]["label"] == a["example"]["label"] for a, _ in pairs], dtype=float)
            right_correct = np.array([b["prediction"]["label"] == b["example"]["label"] for _, b in pairs], dtype=float)
            update_success = np.array([b["prediction"]["label"] == target_label for _, b in pairs], dtype=float)
            lo, hi = boot_ci(delta_target, rng, args.bootstrap)
            slo, shi = boot_ci(update_success, rng, args.bootstrap)
            rows_out.append({
                "model": model,
                "prompt_type": prompt_type,
                "pair": pair_name,
                "n_pairs": len(pairs),
                "mean_delta_target_probability": float(delta_target.mean()),
                "delta_target_ci_low": lo,
                "delta_target_ci_high": hi,
                "mean_delta_p_true": float(delta_true.mean()),
                "left_accuracy": float(left_correct.mean()),
                "right_accuracy": float(right_correct.mean()),
                "right_target_rate": float(update_success.mean()),
                "right_target_ci_low": slo,
                "right_target_ci_high": shi,
            })

            trans = Counter((a["prediction"]["label"], b["prediction"]["label"]) for a, b in pairs)
            for (from_label, to_label), n in sorted(trans.items()):
                transitions.append({
                    "model": model,
                    "prompt_type": prompt_type,
                    "pair": pair_name,
                    "from_label": from_label,
                    "to_label": to_label,
                    "count": n,
                    "rate": n / len(pairs),
                })

            # Telic A/C semantic-subclass analysis is especially informative.
            if pair_name == "A_to_C":
                classes = sorted({a["example"]["verb_class"] for a, _ in pairs})
                for cls in classes:
                    sub = [(a, b) for a, b in pairs if a["example"]["verb_class"] == cls]
                    deltas = np.array([
                        b["prediction"]["probabilities"]["Unknown"]
                        - a["prediction"]["probabilities"]["Unknown"]
                        for a, b in sub
                    ])
                    clo, chi = boot_ci(deltas, rng, args.bootstrap)
                    rows_out.append({
                        "model": model,
                        "prompt_type": prompt_type,
                        "pair": f"A_to_C::{cls}",
                        "n_pairs": len(sub),
                        "mean_delta_target_probability": float(deltas.mean()),
                        "delta_target_ci_low": clo,
                        "delta_target_ci_high": chi,
                        "mean_delta_p_true": float(np.mean([
                            b["prediction"]["probabilities"]["True"] - a["prediction"]["probabilities"]["True"]
                            for a, b in sub
                        ])),
                        "left_accuracy": float(np.mean([a["prediction"]["label"] == "False" for a, _ in sub])),
                        "right_accuracy": float(np.mean([b["prediction"]["label"] == "Unknown" for _, b in sub])),
                        "right_target_rate": float(np.mean([b["prediction"]["label"] == "Unknown" for _, b in sub])),
                        "right_target_ci_low": float("nan"),
                        "right_target_ci_high": float("nan"),
                    })

    df = pd.DataFrame(rows_out)
    tdf = pd.DataFrame(transitions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    tdf.to_csv(args.transitions_out, index=False)
    print(df.to_string(index=False) if not df.empty else "No paired rows produced")
    print(f"Wrote {args.out} and {args.transitions_out}")


if __name__ == "__main__":
    main()
