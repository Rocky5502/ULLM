#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", type=Path, default=Path("results/catalog"))
    p.add_argument("--allow-missing", action="store_true")
    args = p.parse_args()

    experiment = yaml.safe_load(Path("configs/experiment.yaml").read_text(encoding="utf-8"))
    configured_base = str(experiment["base_url"]).rstrip("/")
    env_base = os.getenv("ZZZ_BASE_URL")
    if env_base and env_base.rstrip("/") != configured_base:
        raise SystemExit(
            "ZZZ_BASE_URL disagrees with configs/experiment.yaml. Refusing to catalogue-check "
            "a different gateway from the one the frozen runner will actually call. "
            f"configured={configured_base!r}, env={env_base.rstrip('/')!r}"
        )
    base = configured_base

    key = os.getenv("ZZZ_API_KEY")
    if not key:
        sys.exit("ZZZ_API_KEY is not set")

    model_path = Path("configs/models.yaml")
    model_cfg = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    wanted = [x["id"] for x in model_cfg["models"]]

    started = datetime.now(timezone.utc)
    r = httpx.get(
        f"{base}/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
        follow_redirects=False,
    )
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise SystemExit("Unexpected /models response schema: expected an object containing data: []")

    ids = {m.get("id") for m in data["data"] if isinstance(m, dict)}
    state = {m: m in ids for m in wanted}
    checked = datetime.now(timezone.utc)
    stamp = checked.strftime("%Y%m%dT%H%M%SZ")

    request_id = (
        r.headers.get("x-request-id")
        or r.headers.get("request-id")
        or r.headers.get("x-amzn-requestid")
        or r.headers.get("cf-ray")
    )
    payload = {
        "schema_version": 2,
        "checked_utc": checked.isoformat(),
        "request_started_utc": started.isoformat(),
        "base_url": base,
        "endpoint": "/models",
        "http_status": r.status_code,
        "request_id": request_id,
        "wanted": wanted,
        "available": state,
        "catalog_count": len(data["data"]),
        "catalog_sha256": canonical_sha256(data),
        "model_config_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "experiment_config_sha256": hashlib.sha256(Path("configs/experiment.yaml").read_bytes()).hexdigest(),
        "catalog_raw": data,
        "authorization_header_recorded": False,
        "api_key_recorded": False,
    }

    args.outdir.mkdir(parents=True, exist_ok=True)
    out = args.outdir / f"models_{stamp}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wanted": wanted,
                "available": state,
                "snapshot": str(out),
                "catalog_count": payload["catalog_count"],
                "catalog_sha256": payload["catalog_sha256"],
                "request_id": request_id,
                "api_key_recorded": False,
            },
            indent=2,
        )
    )

    missing = [m for m, ok in state.items() if not ok]
    if missing and not args.allow_missing:
        raise SystemExit(
            f"Configured model IDs missing from live catalogue: {missing}. "
            "Stop and commit/freeze any replacement IDs before running paid completions."
        )


if __name__ == "__main__":
    main()
