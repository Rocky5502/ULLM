#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import normalized_entropy, verbal_uncertainty


def load(path: Path) -> list[dict]:
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


def usage_total(row: dict) -> float:
    usage = row.get("usage") or {}
    if usage.get("total_tokens") is not None:
        return float(usage["total_tokens"])
    p = usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
    c = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
    return float(p) + float(c)


def core_metrics(records: list[dict]) -> dict[str, float]:
    if not records:
        return {
            "accuracy": float("nan"),
            "risk": float("nan"),
            "TBR_C": float("nan"),
            "group_D_accuracy": float("nan"),
        }
    correct = [
        r["prediction"]["label"] == r["example"]["label"] for r in records
    ]
    c = [r for r in records if r["example"]["group"].startswith("C_")]
    d = [r for r in records if r["example"]["group"].startswith("D_")]
    accuracy = sum(correct) / len(correct)
    return {
        "accuracy": accuracy,
        "risk": 1.0 - accuracy,
        "TBR_C": (
            sum(r["prediction"]["label"] == "True" for r in c) / len(c)
            if c
            else float("nan")
        ),
        "group_D_accuracy": (
            sum(r["prediction"]["label"] == "True" for r in d) / len(d)
            if d
            else float("nan")
        ),
    }


def align_verifier(base: list[dict], verifier: list[dict]) -> dict[str, dict]:
    base_ids = [r["example"]["id"] for r in base]
    verifier_ids = [r["example"]["id"] for r in verifier]
    if len(base_ids) != len(set(base_ids)):
        raise ValueError("duplicate IDs in base deterministic rows")
    if len(verifier_ids) != len(set(verifier_ids)):
        raise ValueError("duplicate IDs in verifier deterministic rows")
    if set(base_ids) != set(verifier_ids):
        missing = sorted(set(base_ids) - set(verifier_ids))
        extra = sorted(set(verifier_ids) - set(base_ids))
        raise ValueError(
            f"base/verifier ID mismatch: missing={missing[:10]}, extra={extra[:10]}"
        )
    return {r["example"]["id"]: r for r in verifier}


def evaluate(
    base: list[dict],
    verifier_by_id: dict[str, dict],
    signal: str,
    threshold: float,
) -> dict[str, float]:
    chosen: list[dict] = []
    rechecked = 0
    verifier_tokens = 0.0
    for b in base:
        pr = b["prediction"]["probabilities"]
        if signal == "1-maxprob":
            u = verbal_uncertainty(pr)
        elif signal == "entropy":
            u = normalized_entropy(pr)
        else:
            raise ValueError(signal)
        if u >= threshold:
            selected = verifier_by_id[b["example"]["id"]]
            verifier_tokens += usage_total(selected)
            rechecked += 1
        else:
            selected = b
        chosen.append(selected)

    metrics = core_metrics(chosen)
    base_tokens = sum(usage_total(r) for r in base)
    return {
        "signal": signal,
        "threshold": threshold,
        **metrics,
        "recheck_rate": rechecked / len(base),
        "recheck_calls": rechecked,
        "base_tokens": base_tokens,
        "incremental_verifier_tokens": verifier_tokens,
        "total_policy_tokens": base_tokens + verifier_tokens,
        "incremental_token_ratio": verifier_tokens / base_tokens
        if base_tokens > 0
        else float("nan"),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", nargs="+", type=Path, required=True)
    p.add_argument("--verifier", nargs="+", type=Path, required=True)
    p.add_argument(
        "--thresholds", nargs="+", type=float, default=[0.10, 0.20, 0.30, 0.40]
    )
    p.add_argument(
        "--out", type=Path, default=Path("results/processed/recheck.csv")
    )
    args = p.parse_args()

    verifier_by_model: dict[str, list[dict]] = {}
    for path in args.verifier:
        rows = load(path)
        if rows:
            model = rows[0]["model_requested"]
            if model in verifier_by_model:
                raise SystemExit(f"Duplicate verifier artifact for model {model}")
            verifier_by_model[model] = rows

    out: list[dict] = []
    for path in args.base:
        base = load(path)
        if not base:
            continue
        model = base[0]["model_requested"]
        verifier = verifier_by_model.get(model)
        if verifier is None:
            raise SystemExit(f"Missing verifier artifact for model {model}")
        verifier_by_id = align_verifier(base, verifier)

        base_metrics = core_metrics(base)
        aligned_verifier = [verifier_by_id[r["example"]["id"]] for r in base]
        verifier_metrics = core_metrics(aligned_verifier)
        base_tokens = sum(usage_total(r) for r in base)
        verifier_tokens = sum(usage_total(r) for r in aligned_verifier)

        out.append(
            {
                "model": model,
                "policy": "base_neutral",
                "signal": "none",
                "threshold": float("nan"),
                **base_metrics,
                "recheck_rate": 0.0,
                "recheck_calls": 0,
                "base_tokens": base_tokens,
                "incremental_verifier_tokens": 0.0,
                "total_policy_tokens": base_tokens,
                "incremental_token_ratio": 0.0 if base_tokens > 0 else float("nan"),
                "delta_accuracy_vs_base": 0.0,
                "delta_TBR_C_vs_base": 0.0,
                "delta_group_D_accuracy_vs_base": 0.0,
            }
        )
        out.append(
            {
                "model": model,
                "policy": "blanket_verifier",
                "signal": "none",
                "threshold": float("nan"),
                **verifier_metrics,
                "recheck_rate": 1.0,
                "recheck_calls": len(base),
                "base_tokens": base_tokens,
                "incremental_verifier_tokens": verifier_tokens,
                "total_policy_tokens": base_tokens + verifier_tokens,
                "incremental_token_ratio": verifier_tokens / base_tokens
                if base_tokens > 0
                else float("nan"),
                "delta_accuracy_vs_base": verifier_metrics["accuracy"]
                - base_metrics["accuracy"],
                "delta_TBR_C_vs_base": verifier_metrics["TBR_C"]
                - base_metrics["TBR_C"],
                "delta_group_D_accuracy_vs_base": verifier_metrics["group_D_accuracy"]
                - base_metrics["group_D_accuracy"],
            }
        )
        for signal in ("1-maxprob", "entropy"):
            for threshold in args.thresholds:
                row = evaluate(base, verifier_by_id, signal, threshold)
                row.update(
                    {
                        "model": model,
                        "policy": "selective_recheck",
                        "delta_accuracy_vs_base": row["accuracy"]
                        - base_metrics["accuracy"],
                        "delta_TBR_C_vs_base": row["TBR_C"] - base_metrics["TBR_C"],
                        "delta_group_D_accuracy_vs_base": row["group_D_accuracy"]
                        - base_metrics["group_D_accuracy"],
                    }
                )
                out.append(row)

    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No recheck rows produced")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
