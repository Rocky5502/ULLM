#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ullm.metrics import normalized_entropy, verbal_uncertainty


def load(path: Path) -> list[dict]:
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if r.get("prediction") is not None and int(r.get("repeat", 0)) == 0]


def usage_total(row: dict) -> float:
    usage = row.get("usage") or {}
    for key in ("total_tokens",):
        if usage.get(key) is not None:
            return float(usage[key])
    p = usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
    c = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
    return float(p) + float(c)


def evaluate(base: list[dict], verifier: list[dict], signal: str, threshold: float) -> dict:
    v = {r["example"]["id"]: r for r in verifier}
    chosen: list[tuple[dict, bool]] = []
    verifier_tokens = 0.0
    for b in base:
        pr = b["prediction"]["probabilities"]
        if signal == "1-maxprob":
            u = verbal_uncertainty(pr)
        elif signal == "entropy":
            u = normalized_entropy(pr)
        else:
            raise ValueError(signal)
        do_recheck = u >= threshold
        if do_recheck and b["example"]["id"] in v:
            selected = v[b["example"]["id"]]
            verifier_tokens += usage_total(selected)
        else:
            selected = b
            do_recheck = False
        chosen.append((selected, do_recheck))

    records = [x[0] for x in chosen]
    rechecked = [x[1] for x in chosen]
    correct = [r["prediction"]["label"] == r["example"]["label"] for r in records]
    c = [r for r in records if r["example"]["group"].startswith("C_")]
    d = [r for r in records if r["example"]["group"].startswith("D_")]
    tbr = sum(r["prediction"]["label"] == "True" for r in c) / len(c) if c else float("nan")
    d_acc = sum(r["prediction"]["label"] == "True" for r in d) / len(d) if d else float("nan")
    return {
        "signal": signal,
        "threshold": threshold,
        "accuracy": sum(correct) / len(correct),
        "risk": 1.0 - sum(correct) / len(correct),
        "TBR_C": tbr,
        "group_D_accuracy": d_acc,
        "recheck_rate": sum(rechecked) / len(rechecked),
        "recheck_calls": sum(rechecked),
        "simulated_incremental_verifier_tokens": verifier_tokens,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", nargs="+", type=Path, required=True)
    p.add_argument("--verifier", nargs="+", type=Path, required=True)
    p.add_argument("--thresholds", nargs="+", type=float, default=[0.10, 0.20, 0.30, 0.40])
    p.add_argument("--out", type=Path, default=Path("results/processed/recheck.csv"))
    args = p.parse_args()

    verifier_by_model = {}
    for path in args.verifier:
        rows = load(path)
        if rows:
            verifier_by_model[rows[0]["model_requested"]] = rows

    out = []
    for path in args.base:
        base = load(path)
        if not base:
            continue
        model = base[0]["model_requested"]
        verifier = verifier_by_model.get(model)
        if verifier is None:
            continue

        base_correct = [r["prediction"]["label"] == r["example"]["label"] for r in base]
        verifier_correct = [r["prediction"]["label"] == r["example"]["label"] for r in verifier]
        out.append({
            "model": model, "policy": "base_neutral", "signal": "none", "threshold": float("nan"),
            "accuracy": sum(base_correct)/len(base_correct), "risk": 1-sum(base_correct)/len(base_correct),
            "TBR_C": sum(r["prediction"]["label"] == "True" for r in base if r["example"]["group"].startswith("C_"))/100,
            "group_D_accuracy": sum(r["prediction"]["label"] == "True" for r in base if r["example"]["group"].startswith("D_"))/100,
            "recheck_rate": 0.0, "recheck_calls": 0, "simulated_incremental_verifier_tokens": 0.0,
        })
        out.append({
            "model": model, "policy": "blanket_verifier", "signal": "none", "threshold": float("nan"),
            "accuracy": sum(verifier_correct)/len(verifier_correct), "risk": 1-sum(verifier_correct)/len(verifier_correct),
            "TBR_C": sum(r["prediction"]["label"] == "True" for r in verifier if r["example"]["group"].startswith("C_"))/100,
            "group_D_accuracy": sum(r["prediction"]["label"] == "True" for r in verifier if r["example"]["group"].startswith("D_"))/100,
            "recheck_rate": 1.0, "recheck_calls": len(verifier),
            "simulated_incremental_verifier_tokens": sum(usage_total(r) for r in verifier),
        })
        for signal in ("1-maxprob", "entropy"):
            for threshold in args.thresholds:
                row = evaluate(base, verifier, signal, threshold)
                row.update({"model": model, "policy": "selective_recheck"})
                out.append(row)

    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False) if not df.empty else "No recheck rows produced")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
