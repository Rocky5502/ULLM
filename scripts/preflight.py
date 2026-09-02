#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    print("[preflight] Project consistency gate")
    subprocess.run([sys.executable, "scripts/validate_project.py"], check=True)

    required = [
        Path("configs/experiment.yaml"),
        Path("configs/models.yaml"),
        Path("configs/preregistered_hypotheses.yaml"),
        Path("data/MANIFEST.json"),
        Path("data/THIRD_PARTY_DATA.md"),
        Path("data/imperfectiveNLI.json"),
        Path("paper/main.tex"),
        Path("paper/generated/rq1_table.tex"),
        Path("paper/generated/rq2_table.tex"),
        Path("paper/generated/rq3_table.tex"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing required artifacts:")
        for p in missing:
            print(f" - {p}")
        if "data/imperfectiveNLI.json" in missing:
            print("Run: python scripts/fetch_imperfective_nli.py")
        raise SystemExit(1)

    print("[preflight] Dataset structure gate")
    subprocess.run(
        [sys.executable, "scripts/validate_dataset.py", "data/imperfectiveNLI.json"],
        check=True,
    )

    local_manifest = Path("data/MANIFEST.local.json")
    if not local_manifest.exists():
        raise SystemExit(
            "data/MANIFEST.local.json is missing. Re-fetch with scripts/fetch_imperfective_nli.py "
            "so download provenance is recorded."
        )
    local = json.loads(local_manifest.read_text(encoding="utf-8"))
    dataset_sha = sha256(Path("data/imperfectiveNLI.json"))
    if local.get("sha256") != dataset_sha:
        raise SystemExit("Local dataset SHA-256 does not match data/MANIFEST.local.json")
    if int(local.get("examples", -1)) != 400:
        raise SystemExit("Local data manifest does not record exactly 400 examples")

    exp = yaml.safe_load(Path("configs/experiment.yaml").read_text(encoding="utf-8"))
    models = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    model_ids = [m["id"] for m in models["models"]]
    robust_n = int(exp["prompt_robustness"]["n_examples"])
    call_budget = (
        len(model_ids) * 400 * int(exp["deterministic"]["samples_per_item"])
        + len(model_ids) * 400 * int(exp["sampling"]["samples_per_item"])
        + len(model_ids) * robust_n * len(exp["prompt_robustness"]["prompt_types"])
        + len(model_ids) * int(exp["label_order_robustness"]["n_examples"])
        + len(model_ids) * 400
    )

    print(f"Models: {', '.join(model_ids)}")
    print(
        f"Primary prompt: {exp['primary_prompt']}; "
        f"sampling K={exp['sampling']['samples_per_item']}"
    )
    print(
        "Prompt robustness: "
        f"n={robust_n} conditions={exp['prompt_robustness']['prompt_types']}"
    )
    print(
        "Primary RQ3 recheck point: "
        f"{exp['selective']['primary_recheck_signal']} @ "
        f"{exp['selective']['primary_recheck_threshold']}"
    )
    print(f"Dataset SHA256: {dataset_sha}")
    print(f"Frozen main-study call budget before retries: {call_budget:,}")
    print(f"API key present: {'yes' if os.getenv('ZZZ_API_KEY') else 'NO'}")
    if not os.getenv("ZZZ_API_KEY"):
        print(
            "Set ZZZ_API_KEY in your local shell before model checks/runs. "
            "Do not commit it."
        )
    print(
        "Preflight OK for local artifacts. Next: python scripts/check_models.py "
        "to freeze the live gateway catalogue."
    )


if __name__ == "__main__":
    main()
