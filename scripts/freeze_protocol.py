#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ullm.prompts import get_system_prompt  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path)
    args = p.parse_args()

    dataset = Path("data/imperfectiveNLI.json")
    local_manifest = Path("data/MANIFEST.local.json")
    if not dataset.exists() or not local_manifest.exists():
        raise SystemExit("Fetch/validate the exact dataset before freezing the protocol")

    exp_path = Path("configs/experiment.yaml")
    models_path = Path("configs/models.yaml")
    hypotheses_path = Path("configs/preregistered_hypotheses.yaml")
    paper_path = Path("paper/main.tex")
    exp = yaml.safe_load(exp_path.read_text(encoding="utf-8"))
    models_cfg = yaml.safe_load(models_path.read_text(encoding="utf-8"))
    local = json.loads(local_manifest.read_text(encoding="utf-8"))
    committed_data = json.loads(Path("data/MANIFEST.json").read_text(encoding="utf-8"))

    model_ids = [m["id"] for m in models_cfg["models"]]
    robust_n = int(exp["prompt_robustness"]["n_examples"])
    stages = [
        {"name": "neutral_deterministic", "items_per_model": 400, "repeats": 1, "calls": 2000},
        {"name": "neutral_sampling", "items_per_model": 400, "repeats": 5, "calls": 10000},
        {"name": "strict_logic", "items_per_model": robust_n, "repeats": 1, "calls": len(model_ids) * robust_n},
        {"name": "definition_aware", "items_per_model": robust_n, "repeats": 1, "calls": len(model_ids) * robust_n},
        {
            "name": "reversed_label_order",
            "items_per_model": int(exp["label_order_robustness"]["n_examples"]),
            "repeats": 1,
            "calls": len(model_ids) * int(exp["label_order_robustness"]["n_examples"]),
        },
        {"name": "verifier_cache", "items_per_model": 400, "repeats": 1, "calls": 2000},
    ]
    main_calls = sum(int(s["calls"]) for s in stages)
    if main_calls != 15800:
        raise RuntimeError(f"Protocol freeze expected 15,800 main calls, got {main_calls}")

    prompt_names = [
        exp["primary_prompt"],
        *exp["prompt_robustness"]["prompt_types"],
        exp["verifier"]["prompt_type"],
    ]
    prompt_hashes = {
        name: text_sha256(get_system_prompt(name)) for name in sorted(set(prompt_names))
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out or Path("artifacts/local") / f"protocol_freeze_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    paper_text = paper_path.read_text(encoding="utf-8")
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN_PRE_API",
        "empirical_results_claimed": False,
        "git_commit": git_commit(),
        "paper_title": "The Imperfective Uncertainty in Large Language Models",
        "research_questions": [
            "RQ1: Uncertainty Recognition",
            "RQ2: Uncertainty Faithfulness",
            "RQ3: Uncertainty-Aware Control",
        ],
        "models": model_ids,
        "gateway_base_url": exp["base_url"],
        "primary_prompt": exp["primary_prompt"],
        "prompt_sha256": prompt_hashes,
        "primary_label_order": list(exp["labels"]),
        "alternate_label_order": list(exp["label_order_robustness"]["alternate_order"]),
        "deterministic": exp["deterministic"],
        "sampling": exp["sampling"],
        "max_tokens": int(exp["max_tokens"]),
        "seed": int(exp["seed"]),
        "selective": exp["selective"],
        "statistics": exp["statistics"],
        "stages": stages,
        "main_call_budget_before_retries": main_calls,
        "smoke_call_budget": len(model_ids) * int(exp.get("smoke_n", 20)),
        "dataset": {
            "source_repository": committed_data["source_repository"],
            "source_commit": committed_data["source_commit"],
            "source_path": committed_data["source_path"],
            "git_blob_sha1": committed_data["upstream_git_blob_sha1"],
            "bytes": dataset.stat().st_size,
            "sha256": sha256(dataset),
            "local_manifest_sha256": sha256(local_manifest),
            "download_manifest_sha256": local["sha256"],
        },
        "file_sha256": {
            "experiment": sha256(exp_path),
            "models": sha256(models_path),
            "hypotheses": sha256(hypotheses_path),
            "paper_main": sha256(paper_path),
            "requirements_frozen": sha256(Path("requirements-frozen.txt")),
        },
        "manuscript_tbd_occurrences": paper_text.count("TBD"),
        "notes": [
            "Gateway model strings are routing identifiers and must be checked live before paid execution.",
            "This snapshot contains no API credential and no model response.",
            "Any scientifically material protocol change after this freeze requires a new committed protocol version and a new freeze snapshot.",
        ],
    }
    if payload["dataset"]["sha256"] != payload["dataset"]["download_manifest_sha256"]:
        raise RuntimeError("Dataset bytes disagree with local download provenance manifest")

    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "protocol_snapshot": str(out),
        "git_commit": payload["git_commit"],
        "main_calls": main_calls,
        "models": len(model_ids),
        "prompt_hashes": prompt_hashes,
        "dataset_sha256": payload["dataset"]["sha256"],
        "empirical_results_claimed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
