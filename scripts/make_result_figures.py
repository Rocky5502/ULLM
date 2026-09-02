#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    print(f"Wrote {path} and {path.with_suffix('.svg')}")


def clean_model(x: object) -> str:
    text = str(x)
    aliases = {
        "gpt-5.6-sol": "GPT-5.6 Sol",
        "claude-sonnet-5": "Claude Sonnet 5",
        "deepseek-v4-pro": "DeepSeek V4 Pro",
        "qwen3.8-max": "Qwen 3.8 Max",
        "gemini-3.7-flash": "Gemini 3.7 Flash",
    }
    return aliases.get(text, text)


def model_labels(df: pd.DataFrame) -> list[str]:
    return [clean_model(x) for x in df["model"]]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--summary", type=Path, default=Path("results/processed/summary_neutral.csv")
    )
    p.add_argument(
        "--sampling", type=Path, default=Path("results/processed/sampling.csv")
    )
    p.add_argument(
        "--ranking",
        type=Path,
        default=Path("results/processed/uncertainty_ranking.csv"),
    )
    p.add_argument(
        "--selective", type=Path, default=Path("results/processed/selective.csv")
    )
    p.add_argument(
        "--pairwise", type=Path, default=Path("results/processed/pairwise.csv")
    )
    p.add_argument(
        "--robustness",
        type=Path,
        default=Path("results/processed/prompt_robustness.csv"),
    )
    p.add_argument(
        "--recheck", type=Path, default=Path("results/processed/recheck.csv")
    )
    p.add_argument("--outdir", type=Path, default=Path("results/figures"))
    args = p.parse_args()

    # RQ1: semantic recognition versus false completion on the critical Group C.
    if args.summary.exists():
        summary = pd.read_csv(args.summary)
        metrics = [m for m in ["SUR", "TOR@0.80", "TBR_C"] if m in summary.columns]
        if metrics:
            fig, ax = plt.subplots(figsize=(7.4, 3.5))
            x = list(range(len(summary)))
            width = 0.76 / len(metrics)
            for j, metric in enumerate(metrics):
                pos = [i + (j - (len(metrics) - 1) / 2) * width for i in x]
                ax.bar(pos, summary[metric], width=width, label=metric)
            ax.axhline(0.5, linewidth=0.8, linestyle="--")
            ax.set_xticks(x, model_labels(summary), rotation=15, ha="right")
            ax.set_ylim(0, 1)
            ax.set_ylabel("Rate / mean probability")
            ax.set_title("RQ1: Semantic recognition versus teleological completion")
            ax.legend(ncol=len(metrics), fontsize=8, frameon=False)
            save(fig, args.outdir / "rq1_group_c_uncertainty.pdf")
            plt.close(fig)

        if {"ECE", "ECE_Unknown"}.issubset(summary.columns):
            fig, ax = plt.subplots(figsize=(7.0, 3.4))
            x = list(range(len(summary)))
            width = 0.34
            ax.bar(
                [i - width / 2 for i in x],
                summary["ECE"],
                width=width,
                label="Top-label ECE",
            )
            ax.bar(
                [i + width / 2 for i in x],
                summary["ECE_Unknown"],
                width=width,
                label="Unknown-class ECE",
            )
            ax.set_xticks(x, model_labels(summary), rotation=15, ha="right")
            ax.set_ylim(bottom=0)
            ax.set_ylabel("Calibration error")
            ax.set_title("Aggregate calibration can hide Unknown-class miscalibration")
            ax.legend(fontsize=8, frameon=False)
            save(fig, args.outdir / "rq1_calibration.pdf")
            plt.close(fig)

    if args.sampling.exists():
        sampling = pd.read_csv(args.sampling)
        if not sampling.empty:
            grouped = sampling.groupby("model", as_index=False)[
                ["variation_ratio", "label_entropy"]
            ].mean()
            fig, ax = plt.subplots(figsize=(7.0, 3.3))
            x = list(range(len(grouped)))
            ax.plot(
                x, grouped["variation_ratio"], marker="o", label="Variation ratio"
            )
            ax.plot(x, grouped["label_entropy"], marker="s", label="Label entropy")
            ax.set_xticks(x, model_labels(grouped), rotation=15, ha="right")
            ax.set_ylim(0, 1)
            ax.set_ylabel("Mean sampling uncertainty")
            ax.set_title("RQ2: Repeated-sampling disagreement")
            ax.legend(fontsize=8, frameon=False)
            save(fig, args.outdir / "rq2_sampling_uncertainty.pdf")
            plt.close(fig)

    if args.ranking.exists():
        ranking = pd.read_csv(args.ranking)
        if not ranking.empty:
            if "scope" in ranking.columns:
                ranking = ranking[ranking["scope"] == "all"]
            pivot = ranking.pivot(index="model", columns="signal", values="error_AUROC")
            fig, ax = plt.subplots(figsize=(7.4, 3.6))
            x = list(range(len(pivot)))
            cols = list(pivot.columns)
            width = 0.72 / max(1, len(cols))
            for j, signal in enumerate(cols):
                ax.bar(
                    [i + (j - (len(cols) - 1) / 2) * width for i in x],
                    pivot[signal],
                    width=width,
                    label=signal,
                )
            ax.axhline(0.5, linewidth=0.9, linestyle="--", label="random ranking")
            ax.set_xticks(
                x,
                [clean_model(i) for i in pivot.index],
                rotation=15,
                ha="right",
            )
            ax.set_ylim(0, 1)
            ax.set_ylabel("Error-detection AUROC")
            ax.set_title("RQ2: Do black-box uncertainty signals rank failures?")
            ax.legend(fontsize=7, frameon=False, ncol=2)
            save(fig, args.outdir / "rq2_error_ranking.pdf")
            plt.close(fig)

    if args.pairwise.exists():
        pairwise = pd.read_csv(args.pairwise)
        agg = pairwise[pairwise["pair"].isin(["A_to_C", "B_to_D"])].copy()
        if not agg.empty:
            for pair_name, g in agg.groupby("pair"):
                fig, ax = plt.subplots(figsize=(7.0, 3.4))
                x = list(range(len(g)))
                ax.bar(x, g["mean_delta_target_probability"])
                if {"delta_target_ci_low", "delta_target_ci_high"}.issubset(g.columns):
                    y = g["mean_delta_target_probability"].astype(float)
                    lo = y - g["delta_target_ci_low"].astype(float)
                    hi = g["delta_target_ci_high"].astype(float) - y
                    ax.errorbar(x, y, yerr=[lo, hi], fmt="none", capsize=3)
                ax.axhline(0, linewidth=0.8)
                ax.set_xticks(
                    x,
                    [clean_model(m) for m in g["model"]],
                    rotation=15,
                    ha="right",
                )
                ax.set_ylabel("Mean probability update")
                target = "P(Unknown)" if pair_name == "A_to_C" else "P(True)"
                ax.set_title(
                    f"Paired context update {pair_name.replace('_', '→')}: Δ{target}"
                )
                save(fig, args.outdir / f"pairwise_{pair_name}.pdf")
                plt.close(fig)

    if args.robustness.exists():
        robust = pd.read_csv(args.robustness)
        if not robust.empty:
            robust["condition"] = (
                robust["comparison_prompt"].astype(str)
                + " / "
                + robust["comparison_label_order"].astype(str)
            )
            conditions = list(dict.fromkeys(robust["condition"].tolist()))
            models = list(dict.fromkeys(robust["model"].tolist()))
            fig, ax = plt.subplots(figsize=(7.4, 3.7))
            width = 0.78 / max(1, len(conditions))
            for j, condition in enumerate(conditions):
                g = robust[robust["condition"] == condition].set_index("model")
                vals = [
                    float(g.loc[m, "label_flip_rate"])
                    if m in g.index
                    else float("nan")
                    for m in models
                ]
                ax.bar(
                    [
                        i + (j - (len(conditions) - 1) / 2) * width
                        for i in range(len(models))
                    ],
                    vals,
                    width=width,
                    label=condition,
                )
            ax.set_xticks(
                range(len(models)),
                [clean_model(m) for m in models],
                rotation=15,
                ha="right",
            )
            ax.set_ylim(0, 1)
            ax.set_ylabel("Label flip rate")
            ax.set_title("Prompt / label-order robustness")
            ax.legend(fontsize=6.5, frameon=False)
            save(fig, args.outdir / "robustness_label_flips.pdf")
            plt.close(fig)

    if args.selective.exists():
        selective = pd.read_csv(args.selective)
        if not selective.empty:
            for model, sub in selective.groupby("model"):
                fig, ax = plt.subplots(figsize=(5.9, 3.5))
                for signal, g in sub.groupby("signal"):
                    g = g.sort_values("coverage")
                    ax.plot(g["coverage"], g["risk"], marker="o", label=signal)
                ax.set_xlim(0.45, 1.02)
                ax.set_ylim(bottom=0)
                ax.set_xlabel("Achieved threshold-realizable coverage")
                ax.set_ylabel("Selective risk")
                ax.set_title(f"RQ3 risk–coverage: {clean_model(model)}")
                ax.legend(fontsize=7, frameon=False)
                safe = str(model).replace("/", "_").replace(":", "_")
                save(fig, args.outdir / f"rq3_risk_coverage__{safe}.pdf")
                plt.close(fig)

    if args.recheck.exists():
        recheck = pd.read_csv(args.recheck)
        if not recheck.empty:
            for model, sub in recheck.groupby("model"):
                sel = sub[
                    (sub["policy"] == "selective_recheck")
                    & (sub["signal"] == "1-maxprob")
                ].sort_values("recheck_rate")
                if sel.empty:
                    continue
                fig, ax = plt.subplots(figsize=(6.0, 3.5))
                ax.plot(
                    sel["recheck_rate"], sel["risk"], marker="o", label="overall risk"
                )
                ax.plot(
                    sel["recheck_rate"], sel["TBR_C"], marker="s", label="TBR-C"
                )
                ax.plot(
                    sel["recheck_rate"],
                    1 - sel["group_D_accuracy"],
                    marker="^",
                    label="1 − Group-D accuracy",
                )
                ax.set_xlim(left=0)
                ax.set_ylim(bottom=0)
                ax.set_xlabel("Recheck rate (primary 1-maxprob signal)")
                ax.set_ylabel("Error / bias rate")
                ax.set_title(f"Selective verifier trade-off: {clean_model(model)}")
                ax.legend(fontsize=7, frameon=False)
                safe = str(model).replace("/", "_").replace(":", "_")
                save(fig, args.outdir / f"rq3_recheck_tradeoff__{safe}.pdf")
                plt.close(fig)


if __name__ == "__main__":
    main()
