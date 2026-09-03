#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def command(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path)
    args = p.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out or Path("artifacts/local") / f"environment_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    pip_freeze_text = command([sys.executable, "-m", "pip", "freeze"]) or ""
    pip_freeze = [line for line in pip_freeze_text.splitlines() if line.strip()]
    git_status = command(["git", "status", "--porcelain"])

    paths = {
        "experiment_config": Path("configs/experiment.yaml"),
        "model_config": Path("configs/models.yaml"),
        "hypotheses": Path("configs/preregistered_hypotheses.yaml"),
        "frozen_requirements": Path("requirements-frozen.txt"),
        "dataset": Path("data/imperfectiveNLI.json"),
        "dataset_local_manifest": Path("data/MANIFEST.local.json"),
        "paper_source": Path("paper/main.tex"),
    }

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": command(["git", "rev-parse", "HEAD"]),
        "git_branch": command(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "git_worktree_clean": git_status == "" if git_status is not None else None,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "pip_freeze": pip_freeze,
        "api_key_present": bool(os.getenv("ZZZ_API_KEY")),
        "api_key_value_recorded": False,
        "base_url_override_present": bool(os.getenv("ZZZ_BASE_URL")),
        "files": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "sha256": sha256(path),
            }
            for name, path in paths.items()
        },
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "snapshot": str(out),
        "git_commit": payload["git_commit"],
        "git_worktree_clean": payload["git_worktree_clean"],
        "api_key_present": payload["api_key_present"],
        "api_key_value_recorded": False,
        "packages": len(pip_freeze),
    }, indent=2))


if __name__ == "__main__":
    main()
