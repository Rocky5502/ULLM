#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description="Create a SHA-256 evidence manifest for a run directory.")
    p.add_argument("run_dir", type=Path)
    p.add_argument(
        "--out",
        type=Path,
        help="Output JSON path. Defaults to <run_dir>.checksums.json beside the run directory.",
    )
    args = p.parse_args()

    run_dir = args.run_dir.resolve()
    if not run_dir.exists() or not run_dir.is_dir():
        raise SystemExit(f"Run directory not found: {run_dir}")

    files = sorted(p for p in run_dir.rglob("*") if p.is_file())
    if not files:
        raise SystemExit(f"No files found under: {run_dir}")

    entries = []
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        entries.append({"path": rel, "bytes": path.stat().st_size, "sha256": digest(path)})

    out = args.out or run_dir.parent / f"{run_dir.name}.checksums.json"
    out = out.resolve()
    if out == run_dir or run_dir in out.parents:
        raise SystemExit("Checksum manifest must be written outside the run directory it authenticates")
    out.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": "sha256",
        "run_dir": str(run_dir),
        "file_count": len(entries),
        "total_bytes": sum(row["bytes"] for row in entries),
        "files": entries,
    }
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "run_dir": str(run_dir),
        "manifest": str(out),
        "file_count": len(entries),
        "total_bytes": manifest["total_bytes"],
    }, indent=2))


if __name__ == "__main__":
    main()
