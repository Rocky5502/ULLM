#!/usr/bin/env python3
"""Exercise the full post-run analysis stack without making any API call.

The fixture is deliberately tiny and synthetic. It verifies CLI wiring, JSONL schema,
manifest-aware audits, bootstrap code, ranking/selective analyses, verifier alignment,
preregistered evidence synthesis, vector figure generation, and LaTeX table generation.
It is never used as evidence.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prediction(label: str, probs: dict[str, float]) -> dict[str, Any]:
    return {
        "label": label,
        "probabilities": probs,
        "reason_short": "Synthetic fixture only; not scientific evidence.",
        "probability_sum_raw": sum(probs.values()),
        "normalization_delta": abs(sum(probs.values()) - 1.0),
        "argmax_consistent": label == max(probs, key=probs.get),
    }


def examples() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for i in (1, 2):
        suffix = f"{i:03d}"
        telic = f"build{i}"
        atelic = f"run{i}"
        rows.extend(
            [
                {
                    "id": f"A_{suffix}",
                    "group": "A_Interrupted_Accomplishment",
                    "verb_class": "Creation",
                    "verb": telic,
                    "premise": f"Someone was {telic}, but stopped.",
                    "hypothesis": f"Someone {telic}ed.",
                    "label": "False",
                },
                {
                    "id": f"B_{suffix}",
                    "group": "B_Interrupted_Activity",
                    "verb_class": "Activity",
                    "verb": atelic,
                    "premise": f"Someone was {atelic}ing, but stopped.",
                    "hypothesis": f"Someone {atelic}.",
                    "label": "True",
                },
                {
                    "id": f"C_{suffix}",
                    "group": "C_Ambiguous_Accomplishment",
                    "verb_class": "Creation",
                    "verb": telic,
                    "premise": f"Someone was {telic}.",
                    "hypothesis": f"Someone {telic}ed.",
                    "label": "Unknown",
                },
                {
                    "id": f"D_{suffix}",
                    "group": "D_Ambiguous_Activity",
                    "verb_class": "Activity",
                    "verb": atelic,
                    "premise": f"Someone was {atelic}ing.",
                    "hypothesis": f"Someone {atelic}.",
                    "label": "True",
                },
            ]
        )
    return rows


def base_prediction(ex: dict[str, str]) -> dict[str, Any]:
    gold = ex["label"]
    if ex["id"] == "C_002":
        return prediction("True", {"True": 0.70, "False": 0.10, "Unknown": 0.20})
    probs = {"True": 0.05, "False": 0.05, "Unknown": 0.05}
    probs[gold] = 0.90
    return prediction(gold, probs)


def record(ex: dict[str, str], pred: dict[str, Any], repeat: int, prompt: str) -> dict[str, Any]:
    return {
        "timestamp_utc": "2026-09-03T00:00:00+00:00",
        "model_requested": "synthetic-model",
        "model_returned": "synthetic-model",
        "temperature": 0.0 if repeat == 0 else 0.7,
        "max_tokens_requested": 220,
        "seed_requested": 42 + repeat,
        "repeat": repeat,
        "prompt_type": prompt,
        "prompt_sha256": "synthetic-prompt-sha",
        "messages_sha256": hashlib.sha256(f"{ex['id']}:{repeat}:{prompt}".encode()).hexdigest(),
        "label_order": ["True", "False", "Unknown"],
        "example": ex,
        "prediction": pred,
        "parse_error": None,
        "request_error": None,
        "raw_text": json.dumps(pred),
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "latency_s": 0.01,
        "request_id": f"synthetic-{ex['id']}-{repeat}",
        "http_status": 200,
        "attempts_used": 1,
        "raw_response": {"synthetic": True},
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def run(*args: str) -> None:
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run([PYTHON, *args], cwd=ROOT, env=env, check=True)


def manifest(dataset: Path, mode: str, k: int, selected: list[str]) -> dict[str, Any]:
    config = ROOT / "configs/experiment.yaml"
    models = ROOT / "configs/models.yaml"
    return {
        "schema_version": 3,
        "run_id": f"synthetic-{mode}",
        "created_utc": "2026-09-03T00:00:00+00:00",
        "execution_mode": "live",
        "dataset_sha256": sha256(dataset),
        "dataset_path": str(dataset),
        "dataset_n": len(selected),
        "selected_n": len(selected),
        "selected_ids": sorted(selected),
        "models": ["synthetic-model"],
        "mode": mode,
        "temperature": 0.0 if mode == "deterministic" else 0.7,
        "samples_per_item": k,
        "max_tokens": 220,
        "prompt_type": "neutral",
        "prompt_sha256": "synthetic-prompt-sha",
        "label_order": ["True", "False", "Unknown"],
        "config_sha256": sha256(config),
        "models_sha256": sha256(models),
        "git_commit": "synthetic",
    }


def main() -> None:
    exs = examples()
    with tempfile.TemporaryDirectory(prefix="ullm-smoke-") as tmp_name:
        tmp = Path(tmp_name)
        dataset = tmp / "synthetic.json"
        dataset.write_text(json.dumps(exs), encoding="utf-8")
        selected = [x["id"] for x in exs]

        det = tmp / "det" / "synthetic-model__deterministic__neutral.jsonl"
        det_rows = [record(ex, base_prediction(ex), 0, "neutral") for ex in exs]
        write_jsonl(det, det_rows)
        det_manifest = tmp / "det" / "manifest.json"
        det_manifest.write_text(json.dumps(manifest(dataset, "deterministic", 1, selected)), encoding="utf-8")

        sampling_path = tmp / "sampling" / "synthetic-model__sampling__neutral.jsonl"
        sampling_rows: list[dict[str, Any]] = []
        for ex in exs:
            for rep in range(5):
                pred = base_prediction(ex)
                if ex["id"] == "C_002" and rep in (3, 4):
                    pred = prediction("Unknown", {"True": 0.20, "False": 0.10, "Unknown": 0.70})
                row = record(ex, pred, rep, "neutral")
                row["temperature"] = 0.7
                sampling_rows.append(row)
        write_jsonl(sampling_path, sampling_rows)
        sampling_manifest = tmp / "sampling" / "manifest.json"
        sampling_manifest.write_text(json.dumps(manifest(dataset, "sampling", 5, selected)), encoding="utf-8")

        verifier_path = tmp / "verifier" / "synthetic-model__deterministic__verifier.jsonl"
        verifier_rows = []
        for ex in exs:
            gold = ex["label"]
            probs = {"True": 0.05, "False": 0.05, "Unknown": 0.05}
            probs[gold] = 0.90
            verifier_rows.append(record(ex, prediction(gold, probs), 0, "verifier"))
        write_jsonl(verifier_path, verifier_rows)

        processed = tmp / "processed"
        figures = tmp / "figures"
        tables = tmp / "paper_generated"

        run("scripts/audit_run.py", str(det), "--manifest", str(det_manifest), "--expected-k", "1", "--out", str(processed / "audit_det.json"))
        run("scripts/audit_run.py", str(sampling_path), "--manifest", str(sampling_manifest), "--expected-k", "5", "--out", str(processed / "audit_sampling.json"))
        run("scripts/summarize_results.py", str(det), "--out", str(processed / "summary.csv"))
        run("scripts/bootstrap_summary.py", str(det), "--bootstrap", "25", "--out", str(processed / "bootstrap.csv"))
        run("scripts/analyze_sampling.py", str(sampling_path), "--expected-k", "5", "--out", str(processed / "sampling.csv"), "--ranking-out", str(processed / "sampling_ranking.csv"))
        run("scripts/analyze_uncertainty_ranking.py", str(det), "--sampling", str(processed / "sampling.csv"), "--out", str(processed / "ranking.csv"))
        run("scripts/bootstrap_uncertainty_ranking.py", str(det), "--sampling", str(processed / "sampling.csv"), "--bootstrap", "25", "--out", str(processed / "ranking_bootstrap.csv"))
        run("scripts/analyze_pairwise.py", str(det), "--bootstrap", "25", "--out", str(processed / "pairwise.csv"), "--transitions-out", str(processed / "transitions.csv"))
        run("scripts/analyze_selective.py", str(det), "--sampling", str(processed / "sampling.csv"), "--out", str(processed / "selective.csv"))
        run("scripts/analyze_recheck.py", "--base", str(det), "--verifier", str(verifier_path), "--out", str(processed / "recheck.csv"))
        run("scripts/analyze_hypotheses.py", "--det", str(det), "--bootstrap", str(processed / "bootstrap.csv"), "--ranking-bootstrap", str(processed / "ranking_bootstrap.csv"), "--recheck", str(processed / "recheck.csv"), "--permutations", "25", "--out", str(processed / "hypothesis_evidence.csv"))
        run("scripts/make_result_figures.py", "--summary", str(processed / "summary.csv"), "--sampling", str(processed / "sampling.csv"), "--ranking", str(processed / "ranking.csv"), "--selective", str(processed / "selective.csv"), "--pairwise", str(processed / "pairwise.csv"), "--recheck", str(processed / "recheck.csv"), "--outdir", str(figures))
        run("scripts/make_paper_tables.py", "--summary", str(processed / "summary.csv"), "--bootstrap", str(processed / "bootstrap.csv"), "--ranking", str(processed / "ranking.csv"), "--ranking-bootstrap", str(processed / "ranking_bootstrap.csv"), "--recheck", str(processed / "recheck.csv"), "--outdir", str(tables))

        expected = [
            processed / "summary.csv",
            processed / "bootstrap.csv",
            processed / "sampling.csv",
            processed / "ranking.csv",
            processed / "ranking_bootstrap.csv",
            processed / "pairwise.csv",
            processed / "selective.csv",
            processed / "recheck.csv",
            processed / "hypothesis_evidence.csv",
            figures / "rq1_group_c_uncertainty.pdf",
            tables / "rq1_table.tex",
            tables / "rq1_ci_table.tex",
            tables / "rq2_table.tex",
            tables / "rq2_ci_table.tex",
            tables / "rq3_table.tex",
        ]
        missing = [str(p) for p in expected if not p.exists()]
        if missing:
            raise SystemExit(f"Synthetic pipeline did not produce expected artifacts: {missing}")
        print("Synthetic zero-API pipeline smoke PASS")


if __name__ == "__main__":
    main()
