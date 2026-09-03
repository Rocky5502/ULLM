#!/usr/bin/env python3
"""Generate a preregistered evidence table for H1--H4 without post-hoc story selection.

Only H1 receives a formal randomization p-value: within each telic verb, A/C condition
assignments are exchangeable under the null of no ambiguity-specific P(Unknown) update.
The five model-wise H1 p-values are Holm adjusted as predeclared. H2 is descriptive by
design; H3 is judged from verb-cluster AUROC intervals versus 0.5; H4 reports all
predeclared trade-off components rather than collapsing them into a favorable scalar.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from ullm.metrics import ambiguity_discrimination_gap
from ullm.statistics import holm_adjust


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


def h1_adg_randomization(
    rows: list[dict[str, Any]], *, n_perm: int, seed: int
) -> tuple[float, float, int]:
    by_verb: dict[str, dict[str, float]] = defaultdict(dict)
    groups: list[str] = []
    probs: list[dict[str, float]] = []
    bd: list[float] = []

    for row in rows:
        group = str(row["example"]["group"])[0]
        p_u = float(row["prediction"]["probabilities"]["Unknown"])
        groups.append(str(row["example"]["group"]))
        probs.append(row["prediction"]["probabilities"])
        if group in {"A", "C"}:
            by_verb[str(row["example"]["verb"])][group] = p_u
        elif group in {"B", "D"}:
            bd.append(p_u)

    pairs = [pair for pair in by_verb.values() if set(pair) == {"A", "C"}]
    if not pairs or not bd:
        return float("nan"), float("nan"), len(pairs)

    a = np.asarray([pair["A"] for pair in pairs], dtype=float)
    c = np.asarray([pair["C"] for pair in pairs], dtype=float)
    bd_arr = np.asarray(bd, dtype=float)
    observed = float(ambiguity_discrimination_gap(groups, probs))

    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(n_perm):
        swap = rng.integers(0, 2, size=len(pairs), dtype=np.int8).astype(bool)
        perm_c = np.where(swap, a, c)
        perm_a = np.where(swap, c, a)
        perm_stat = float(np.mean(perm_c) - np.mean(np.concatenate([perm_a, bd_arr])))
        if perm_stat >= observed - 1e-15:
            exceed += 1
    p_value = (exceed + 1.0) / (n_perm + 1.0)
    return observed, float(p_value), len(pairs)


def metric_ci(
    frame: pd.DataFrame, *, model: str, metric: str
) -> tuple[float, float, float]:
    sub = frame[(frame["model"] == model) & (frame["metric"] == metric)]
    if sub.empty:
        return float("nan"), float("nan"), float("nan")
    row = sub.iloc[0]
    return float(row["estimate"]), float(row["ci_low"]), float(row["ci_high"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--det", nargs="+", type=Path, required=True)
    p.add_argument("--bootstrap", type=Path, required=True)
    p.add_argument("--ranking-bootstrap", type=Path, required=True)
    p.add_argument("--recheck", type=Path, required=True)
    p.add_argument("--config", type=Path, default=Path("configs/experiment.yaml"))
    p.add_argument("--permutations", type=int, default=10000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--out", type=Path, default=Path("results/processed/hypothesis_evidence.csv")
    )
    args = p.parse_args()

    if args.permutations < 1:
        raise SystemExit("--permutations must be >= 1")

    bootstrap = pd.read_csv(args.bootstrap)
    ranking_boot = pd.read_csv(args.ranking_bootstrap)
    recheck = pd.read_csv(args.recheck)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    primary_signal = str(config["selective"]["primary_recheck_signal"])
    primary_threshold = float(config["selective"]["primary_recheck_threshold"])

    rows_by_model: dict[str, list[dict[str, Any]]] = {}
    h1_raw: list[dict[str, Any]] = []
    for file_index, path in enumerate(args.det):
        records = load_det(path)
        if not records:
            continue
        model = str(records[0]["model_requested"])
        rows_by_model[model] = records
        adg, p_value, n_pairs = h1_adg_randomization(
            records,
            n_perm=args.permutations,
            seed=args.seed + 1009 * file_index,
        )
        _, ci_low, ci_high = metric_ci(bootstrap, model=model, metric="ADG")
        h1_raw.append(
            {
                "hypothesis": "H1",
                "rq": "RQ1",
                "model": model,
                "component": "ADG",
                "signal": "verbalized_P(Unknown)",
                "estimate": adg,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "p_value": p_value,
                "p_holm": float("nan"),
                "criterion": "ADG > 0; one-sided A/C paired-label randomization; Holm across five models",
                "directional_result": (
                    "positive_ci" if np.isfinite(ci_low) and ci_low > 0 else
                    "negative_ci" if np.isfinite(ci_high) and ci_high < 0 else
                    "interval_crosses_zero"
                ),
                "n_clusters_or_pairs": n_pairs,
            }
        )

    adjusted = holm_adjust([float(row["p_value"]) for row in h1_raw])
    for row, p_adj in zip(h1_raw, adjusted):
        row["p_holm"] = p_adj
        row["formal_result"] = (
            "directional_evidence_after_holm"
            if np.isfinite(p_adj) and p_adj < 0.05 and float(row["estimate"]) > 0
            else "not_significant_after_holm"
        )

    out: list[dict[str, Any]] = list(h1_raw)
    models = list(rows_by_model)

    # H2 is explicitly descriptive: high-confidence completion in Group C is a severity
    # diagnostic, not a null-hypothesis test.
    for model in models:
        est, lo, hi = metric_ci(bootstrap, model=model, metric="TOR@0.80")
        out.append(
            {
                "hypothesis": "H2",
                "rq": "RQ1",
                "model": model,
                "component": "TOR@0.80",
                "signal": "P(True)",
                "estimate": est,
                "ci_low": lo,
                "ci_high": hi,
                "p_value": float("nan"),
                "p_holm": float("nan"),
                "criterion": "descriptive severity diagnostic; lower is better",
                "directional_result": "descriptive_only",
                "formal_result": "not_tested_by_design",
            }
        )

    # H3: do not pick whichever signal looks best. Emit all four signals/model and compare
    # the verb-cluster 95% AUROC interval to random ranking (0.5).
    rb = ranking_boot[
        (ranking_boot["scope"] == "all")
        & (ranking_boot["metric"] == "error_AUROC")
    ]
    for _, row in rb.iterrows():
        lo = float(row["ci_low"])
        hi = float(row["ci_high"])
        if np.isfinite(lo) and lo > 0.5:
            direction = "interval_above_random"
        elif np.isfinite(hi) and hi < 0.5:
            direction = "interval_below_random"
        else:
            direction = "interval_includes_random"
        out.append(
            {
                "hypothesis": "H3",
                "rq": "RQ2",
                "model": row["model"],
                "component": "error_AUROC",
                "signal": row["signal"],
                "estimate": float(row["estimate"]),
                "ci_low": lo,
                "ci_high": hi,
                "p_value": float("nan"),
                "p_holm": float("nan"),
                "criterion": "verb-cluster 95% AUROC interval compared with 0.5; all signals reported",
                "directional_result": direction,
                "formal_result": "interval_based_not_p_value",
            }
        )

    # H4: preserve the full trade-off rather than manufacturing a single success score.
    for model in models:
        base = recheck[(recheck["model"] == model) & (recheck["policy"] == "base_neutral")]
        blanket = recheck[(recheck["model"] == model) & (recheck["policy"] == "blanket_verifier")]
        selective = recheck[
            (recheck["model"] == model)
            & (recheck["policy"] == "selective_recheck")
            & (recheck["signal"] == primary_signal)
            & ((recheck["threshold"] - primary_threshold).abs() < 1e-12)
        ]
        if base.empty or blanket.empty or selective.empty:
            continue
        b = base.iloc[0]
        k = blanket.iloc[0]
        s = selective.iloc[0]
        components = {
            "risk_delta_vs_base": float(s["risk"] - b["risk"]),
            "TBR_C_delta_vs_base": float(s["TBR_C"] - b["TBR_C"]),
            "group_D_delta_vs_base": float(s["group_D_accuracy"] - b["group_D_accuracy"]),
            "group_D_delta_vs_blanket": float(s["group_D_accuracy"] - k["group_D_accuracy"]),
            "recheck_rate": float(s["recheck_rate"]),
            "incremental_token_ratio": float(s["incremental_token_ratio"]),
        }
        component_directions = {
            "risk_reduced": components["risk_delta_vs_base"] < 0,
            "TBR_reduced": components["TBR_C_delta_vs_base"] < 0,
            "D_not_worse_than_base": components["group_D_delta_vs_base"] >= 0,
            "D_better_than_or_equal_blanket": components["group_D_delta_vs_blanket"] >= 0,
            "fewer_rechecks_than_blanket": components["recheck_rate"] < 1.0,
        }
        out.append(
            {
                "hypothesis": "H4",
                "rq": "RQ3",
                "model": model,
                "component": f"selective_{primary_signal}@{primary_threshold:.2f}",
                "signal": primary_signal,
                "estimate": float(s["risk"]),
                "ci_low": float("nan"),
                "ci_high": float("nan"),
                "p_value": float("nan"),
                "p_holm": float("nan"),
                "criterion": "report risk/TBR/D-retention/cost components; full threshold sweep remains primary",
                "directional_result": json.dumps(component_directions, sort_keys=True),
                "formal_result": "multi_component_descriptive",
                **components,
            }
        )

    frame = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(frame.to_string(index=False) if not frame.empty else "No hypothesis evidence produced")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
