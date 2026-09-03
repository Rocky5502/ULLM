#!/usr/bin/env python3
"""Freeze provenance for derived analysis artifacts separately from raw API execution.

Raw run manifests already record the Git commit that constructed/provider-called each
request. This script records the *analysis* Git commit plus cryptographic hashes of the
raw evidence and derived outputs. The two-SHA design lets the raw experiment stay pinned
to `experiment-ready-v1` while analysis/submission tooling can be improved transparently
before any empirical interpretation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_RUN_IDS = (
    "frozen-det-neutral-v1",
    "frozen-sampling-neutral-v1",
    "robust-strict-v1",
    "robust-definition-v1",
    "robust-label-order-v1",
    "frozen-verifier-v1",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def scientific_tree_dirty() -> bool | None:
    """Detect uncommitted changes that could alter scientific computation.

    Generated result tables and manuscript prose are intentionally excluded; only code,
    configs, dependency locks, and committed data provenance are scientific inputs here.
    """
    paths = [
        "src",
        "scripts",
        "configs",
        "requirements.txt",
        "requirements-frozen.txt",
        "data/MANIFEST.json",
    ]
    try:
        proc = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", *paths],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if proc.returncode == 0:
            return False
        if proc.returncode == 1:
            return True
        return None
    except Exception:
        return None


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def collect_files(base: Path, patterns: tuple[str, ...]) -> list[Path]:
    files: set[Path] = set()
    if not base.exists():
        return []
    for pattern in patterns:
        files.update(p for p in base.glob(pattern) if p.is_file())
    return sorted(files)


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--raw-dir",
        action="append",
        type=Path,
        help="raw run directory; repeat. Defaults to all six canonical frozen runs.",
    )
    p.add_argument("--processed-dir", type=Path, default=Path("results/processed"))
    p.add_argument("--figures-dir", type=Path, default=Path("results/figures"))
    p.add_argument("--paper-generated-dir", type=Path, default=Path("paper/generated"))
    p.add_argument(
        "--out", type=Path, default=Path("results/processed/analysis_manifest.json")
    )
    p.add_argument(
        "--allow-noncanonical",
        action="store_true",
        help="permit arbitrary run IDs for zero-API/synthetic plumbing tests only.",
    )
    args = p.parse_args()

    raw_dirs = args.raw_dir or [Path("results/raw") / run_id for run_id in CANONICAL_RUN_IDS]
    errors: list[str] = []
    raw_runs: list[dict[str, Any]] = []
    observed_ids: list[str] = []

    for raw_dir in raw_dirs:
        manifest_path = raw_dir / "manifest.json"
        if not manifest_path.is_file():
            errors.append(f"missing raw manifest: {manifest_path}")
            continue
        try:
            manifest = load_manifest(manifest_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid raw manifest {manifest_path}: {exc}")
            continue
        run_id = str(manifest.get("run_id", raw_dir.name))
        observed_ids.append(run_id)
        if not args.allow_noncanonical and manifest.get("execution_mode") != "live":
            errors.append(f"canonical analysis refuses non-live raw run: {run_id}")
        raw_files = collect_files(raw_dir, ("manifest.json", "*.jsonl"))
        if len(raw_files) < 2:
            errors.append(f"raw run lacks manifest + JSONL evidence: {raw_dir}")
        raw_runs.append(
            {
                "run_id": run_id,
                "raw_execution_git_commit": manifest.get("git_commit"),
                "dataset_sha256": manifest.get("dataset_sha256"),
                "config_sha256": manifest.get("config_sha256"),
                "models_sha256": manifest.get("models_sha256"),
                "prompt_type": manifest.get("prompt_type"),
                "mode": manifest.get("mode"),
                "selected_n": manifest.get("selected_n"),
                "files": [file_record(path) for path in raw_files],
            }
        )

    if not args.allow_noncanonical:
        if tuple(observed_ids) != CANONICAL_RUN_IDS:
            errors.append(
                "canonical run order/identity mismatch: "
                f"expected {list(CANONICAL_RUN_IDS)}, observed {observed_ids}"
            )

    analysis_sha = git_commit()
    dirty = scientific_tree_dirty()
    if analysis_sha is None:
        errors.append("could not resolve analysis Git commit")
    if dirty is True:
        errors.append("scientific code/config working tree has uncommitted changes")
    if dirty is None:
        errors.append("could not verify scientific code/config working-tree cleanliness")

    processed = collect_files(
        args.processed_dir,
        ("*.csv", "audit_*.json"),
    )
    figures = collect_files(args.figures_dir, ("*.pdf", "*.svg"))
    generated = collect_files(args.paper_generated_dir, ("*.tex",))
    if not args.allow_noncanonical:
        if not processed:
            errors.append("no processed analysis artifacts found")
        if not figures:
            errors.append("no generated result figures found")
        if not generated:
            errors.append("no generated LaTeX tables found")

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "evidence_class": "synthetic/non-evidence" if args.allow_noncanonical else "canonical-live-analysis",
        "analysis_git_commit": analysis_sha,
        "scientific_tree_dirty": dirty,
        "raw_runs": raw_runs,
        "processed_artifacts": [file_record(path) for path in processed],
        "figure_artifacts": [file_record(path) for path in figures],
        "paper_generated_artifacts": [file_record(path) for path in generated],
        "errors": errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "evidence_class": payload["evidence_class"],
        "analysis_git_commit": analysis_sha,
        "raw_run_ids": observed_ids,
        "processed_files": len(processed),
        "figure_files": len(figures),
        "generated_tables": len(generated),
        "out": str(args.out),
        "errors": errors,
    }, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
