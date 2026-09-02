#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    required = [
        Path("configs/experiment.yaml"),
        Path("configs/models.yaml"),
        Path("configs/preregistered_hypotheses.yaml"),
        Path("data/MANIFEST.json"),
        Path("data/imperfectiveNLI.json"),
        Path("paper/main.tex"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing required artifacts:")
        for p in missing:
            print(f" - {p}")
        if "data/imperfectiveNLI.json" in missing:
            print("Run: python scripts/fetch_imperfective_nli.py")
        raise SystemExit(1)

    subprocess.run(
        [sys.executable, "scripts/validate_dataset.py", "data/imperfectiveNLI.json"],
        check=True,
    )
    exp = yaml.safe_load(Path("configs/experiment.yaml").read_text(encoding="utf-8"))
    models = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    print(f"Models: {', '.join(m['id'] for m in models['models'])}")
    print(f"Primary prompt: {exp['primary_prompt']}; sampling K={exp['sampling']['samples_per_item']}")
    print(f"Prompt robustness: n={exp['prompt_robustness']['n_examples']} conditions={exp['prompt_robustness']['prompt_types']}")
    print(f"Dataset SHA256: {sha256(Path('data/imperfectiveNLI.json'))}")
    print(f"API key present: {'yes' if os.getenv('ZZZ_API_KEY') else 'NO'}")
    if not os.getenv("ZZZ_API_KEY"):
        print("Set ZZZ_API_KEY in your local shell before model checks/runs. Do not commit it.")
    print("Preflight OK for local artifacts. Next: python scripts/check_models.py and archive the catalogue snapshot.")


if __name__ == "__main__":
    main()
