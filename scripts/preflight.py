#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"[preflight] FAIL: {message}")


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
        Path("data/MANIFEST.local.json"),
        Path("paper/main.tex"),
        Path("paper/generated/rq1_table.tex"),
        Path("paper/generated/rq2_table.tex"),
        Path("paper/generated/rq3_table.tex"),
        Path("requirements-frozen.txt"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing required artifacts:")
        for p in missing:
            print(f" - {p}")
        if "data/imperfectiveNLI.json" in missing or "data/MANIFEST.local.json" in missing:
            print("Run: python scripts/fetch_imperfective_nli.py")
        raise SystemExit(1)

    print("[preflight] Dataset structure gate")
    subprocess.run(
        [sys.executable, "scripts/validate_dataset.py", "data/imperfectiveNLI.json"],
        check=True,
    )

    print("[preflight] Dataset provenance-chain gate")
    committed = json.loads(Path("data/MANIFEST.json").read_text(encoding="utf-8"))
    local = json.loads(Path("data/MANIFEST.local.json").read_text(encoding="utf-8"))
    dataset_path = Path("data/imperfectiveNLI.json")
    dataset_sha = sha256(dataset_path)

    source_commit = str(committed.get("source_commit", ""))
    source_blob = str(committed.get("upstream_git_blob_sha1", ""))
    if not HEX40.fullmatch(source_commit):
        fail("data/MANIFEST.json has an invalid or missing 40-hex source_commit")
    if not HEX40.fullmatch(source_blob):
        fail("data/MANIFEST.json has an invalid or missing upstream_git_blob_sha1")

    if local.get("source_commit") != source_commit:
        fail(
            "local dataset source_commit does not match committed provenance: "
            f"{local.get('source_commit')} != {source_commit}"
        )
    if local.get("git_blob_sha1") != source_blob:
        fail(
            "local dataset Git blob does not match committed provenance: "
            f"{local.get('git_blob_sha1')} != {source_blob}"
        )
    if local.get("source_path") != committed.get("source_path"):
        fail("local dataset source_path does not match committed provenance")
    if local.get("source_repository") != committed.get("source_repository"):
        fail("local dataset source_repository does not match committed provenance")

    expected_bytes = int(committed.get("expected_bytes", -1))
    expected_examples = int(committed.get("expected_examples", -1))
    actual_bytes = dataset_path.stat().st_size
    if actual_bytes != expected_bytes:
        fail(f"dataset byte count mismatch: expected {expected_bytes}, got {actual_bytes}")
    if int(local.get("bytes", -1)) != expected_bytes:
        fail("local manifest byte count does not match committed expected_bytes")
    if int(local.get("examples", -1)) != expected_examples or expected_examples != 400:
        fail("dataset example count provenance must resolve to exactly 400")
    if local.get("sha256") != dataset_sha or not HEX64.fullmatch(str(local.get("sha256", ""))):
        fail("local dataset SHA-256 does not match data/MANIFEST.local.json")

    generated_manifest = Path("data/dataset_manifest.json")
    if not generated_manifest.exists():
        fail("data/dataset_manifest.json was not produced by validate_dataset.py")
    generated = json.loads(generated_manifest.read_text(encoding="utf-8"))
    if generated.get("validation") != "PASS":
        fail("dataset validator manifest does not record PASS")
    if generated.get("sha256") != dataset_sha:
        fail("dataset validator SHA-256 disagrees with the downloaded dataset")
    if int(generated.get("n", -1)) != expected_examples:
        fail("dataset validator example count disagrees with committed provenance")

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
    if call_budget != 15_800:
        fail(f"frozen main-study call budget drifted from 15,800 to {call_budget}")

    frozen_requirements = Path("requirements-frozen.txt").read_text(encoding="utf-8")
    for package in ("httpx==", "PyYAML==", "numpy==", "pandas==", "scipy==", "matplotlib=="):
        if package not in frozen_requirements:
            fail(f"requirements-frozen.txt is missing a pinned {package[:-2]} dependency")

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
    print(f"Dataset source commit: {source_commit}")
    print(f"Dataset Git blob: {source_blob}")
    print(f"Dataset SHA256: {dataset_sha}")
    print(f"Frozen main-study call budget before retries: {call_budget:,}")
    print(f"API key present: {'yes' if os.getenv('ZZZ_API_KEY') else 'NO'}")
    if not os.getenv("ZZZ_API_KEY"):
        print(
            "No API key is required for the completed offline gates. "
            "Set ZZZ_API_KEY only when you are ready for the later live catalogue/smoke stage."
        )
    print(
        "Preflight PASS for local immutable data + frozen protocol. "
        "Next offline option: python scripts/offline_rehearsal.py. "
        "Later live option: python scripts/check_models.py."
    )


if __name__ == "__main__":
    main()
