#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", type=Path, default=Path("results/catalog"))
    p.add_argument("--allow-missing", action="store_true")
    args = p.parse_args()

    base = os.getenv("ZZZ_BASE_URL", "https://api.zhizengzeng.com/v1").rstrip("/")
    key = os.getenv("ZZZ_API_KEY")
    if not key:
        sys.exit("ZZZ_API_KEY is not set")
    wanted = [x["id"] for x in yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))["models"]]
    r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    ids = {m.get("id") for m in data.get("data", [])}
    state = {m: m in ids for m in wanted}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "wanted": wanted,
        "available": state,
        "catalog_count": len(data.get("data", [])),
        "catalog_raw": data,
    }
    args.outdir.mkdir(parents=True, exist_ok=True)
    out = args.outdir / f"models_{stamp}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"wanted": wanted, "available": state, "snapshot": str(out)}, indent=2))
    missing = [m for m, ok in state.items() if not ok]
    if missing and not args.allow_missing:
        raise SystemExit(f"Configured model IDs missing from live catalogue: {missing}. Freeze replacement IDs before running.")


if __name__ == "__main__":
    main()
