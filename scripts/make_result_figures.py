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
    print(f"Wrote {path}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, default=Path("results/processed/summary.csv"))
    p.add_argument("--sampling", type=Path, default=Path("results/processed/sampling.csv"))
    p.add_argument("--outdir", type=Path, default=Path("results/figures"))
    args = p.parse_args()

    summary = pd.read_csv(args.summary)
    metrics = ["TBR_C", "SUR", "TOR@0.80", "ECE"]
    available = [m for m in metrics if m in summary.columns]
    if available:
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        x = range(len(summary))
        width = 0.8 / len(available)
        for j, metric in enumerate(available):
            ax.bar([i + (j - (len(available)-1)/2) * width for i in x], summary[metric], width=width, label=metric)
        ax.set_xticks(list(x), summary["file"], rotation=25, ha="right")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Rate / calibration error")
        ax.legend(ncol=2, fontsize=8)
        save(fig, args.outdir / "model_uncertainty_overview.pdf")
        plt.close(fig)

    if args.sampling.exists():
        sampling = pd.read_csv(args.sampling)
        grouped = sampling.groupby("model", as_index=False)[["variation_ratio", "label_entropy"]].mean()
        fig, ax = plt.subplots(figsize=(6.0, 3.2))
        x = range(len(grouped))
        ax.plot(list(x), grouped["variation_ratio"], marker="o", label="Variation ratio")
        ax.plot(list(x), grouped["label_entropy"], marker="s", label="Label entropy")
        ax.set_xticks(list(x), grouped["model"], rotation=25, ha="right")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Sampling uncertainty")
        ax.legend(fontsize=8)
        save(fig, args.outdir / "sampling_uncertainty.pdf")
        plt.close(fig)


if __name__ == "__main__":
    main()
