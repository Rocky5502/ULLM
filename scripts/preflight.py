#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    required = [
        Path("configs/experiment.yaml"), Path("configs/models.yaml"),
        Path("configs/preregistered_hypotheses.yaml"), Path("data/MANIFEST.json"),
        Path("data/imperfectiveNLI.json"), Path("paper/main.tex"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing required artifacts:")
        for p in missing:
            print(f" - {p}")
        if "data/imperfectiveNLI.json" in missing:
            print("Run: python scripts/fetch_imperfective_nli.py")
        raise SystemExit(1)

    subprocess.run([sys.executable, "scripts/validate_dataset.py", "data/imperfectiveNLI.json"], check=True)
    exp = yaml.safe_load(Path("configs/experiment.yaml").read_text())
    models = yaml.safe_load(Path("configs/models.yaml").read_text())
    print(f"Models: {', '.join(m['id'] for m in models['models'])}")
    print(f"Primary protocol: {exp['primary_protocol']}; sampling K={exp['sampling']['samples_per_item']}")
    print(f"Dataset SHA256: {sha256(Path('data/imperfectiveNLI.json'))}")
    print("Preflight OK. Next: python scripts/check_models.py and archive the catalogue snapshot.")


if __name__ == "__main__":
    main()
