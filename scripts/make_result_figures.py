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


def model_labels(df: pd.DataFrame) -> list[str]:
    return [str(x).replace("-", "\n", 1) for x in df["model"]]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, default=Path("results/processed/summary_strict.csv"))
    p.add_argument("--sampling", type=Path, default=Path("results/processed/sampling.csv"))
    p.add_argument("--selective", type=Path, default=Path("results/processed/selective.csv"))
    p.add_argument("--outdir", type=Path, default=Path("results/figures"))
    args = p.parse_args()

    if args.summary.exists():
        summary = pd.read_csv(args.summary)
        metrics = [m for m in ["SUR", "TOR@0.80", "TBR_C"] if m in summary.columns]
        if metrics:
            fig, ax = plt.subplots(figsize=(7.2, 3.4))
            x = list(range(len(summary)))
            width = 0.8 / len(metrics)
            for j, metric in enumerate(metrics):
                pos = [i + (j - (len(metrics)-1)/2) * width for i in x]
                ax.bar(pos, summary[metric], width=width, label=metric)
            ax.set_xticks(x, model_labels(summary))
            ax.set_ylim(0, 1)
            ax.set_ylabel("Rate")
            ax.set_title("Imperfective uncertainty on the critical Group C")
            ax.legend(ncol=len(metrics), fontsize=8)
            save(fig, args.outdir / "rq1_group_c_uncertainty.pdf")
            plt.close(fig)

    if args.sampling.exists():
        sampling = pd.read_csv(args.sampling)
        if not sampling.empty:
            grouped = sampling.groupby("model", as_index=False)[["variation_ratio", "label_entropy"]].mean()
            fig, ax = plt.subplots(figsize=(6.8, 3.2))
            x = list(range(len(grouped)))
            ax.plot(x, grouped["variation_ratio"], marker="o", label="Variation ratio")
            ax.plot(x, grouped["label_entropy"], marker="s", label="Label entropy")
            ax.set_xticks(x, model_labels(grouped))
            ax.set_ylim(0, 1)
            ax.set_ylabel("Sampling uncertainty")
            ax.set_title("RQ2: repeated-sampling disagreement")
            ax.legend(fontsize=8)
            save(fig, args.outdir / "rq2_sampling_uncertainty.pdf")
            plt.close(fig)

    if args.selective.exists():
        selective = pd.read_csv(args.selective)
        if not selective.empty:
            for model, sub in selective.groupby("model"):
                fig, ax = plt.subplots(figsize=(5.8, 3.4))
                for signal, g in sub.groupby("signal"):
                    g = g.sort_values("coverage")
                    ax.plot(g["coverage"], g["risk"], marker="o", label=signal)
                ax.set_xlim(0.45, 1.02)
                ax.set_ylim(bottom=0)
                ax.set_xlabel("Coverage")
                ax.set_ylabel("Selective risk")
                ax.set_title(f"RQ3 risk–coverage: {model}")
                ax.legend(fontsize=7)
                safe = str(model).replace("/", "_")
                save(fig, args.outdir / f"rq3_risk_coverage__{safe}.pdf")
                plt.close(fig)


if __name__ == "__main__":
    main()
