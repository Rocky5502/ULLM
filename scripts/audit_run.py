#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_file(path: Path, expected_k: int | None = None) -> dict:
    rows = []
    malformed_lines = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            malformed_lines += 1

    keys = [(r.get("example", {}).get("id"), int(r.get("repeat", 0))) for r in rows]
    dupes = [k for k, n in Counter(keys).items() if n > 1]
    request_errors = [r for r in rows if r.get("request_error")]
    parse_errors = [r for r in rows if not r.get("request_error") and r.get("prediction") is None]
    argmax_bad = [r for r in rows if r.get("prediction") and not r["prediction"].get("argmax_consistent", True)]
    norm_bad = [
        r for r in rows
        if r.get("prediction") and float(r["prediction"].get("normalization_delta", 0.0)) > 0.02
    ]

    requested = sorted({str(r.get("model_requested")) for r in rows})
    returned = sorted({str(r.get("model_returned")) for r in rows if r.get("model_returned")})
    prompt_types = sorted({str(r.get("prompt_type", "legacy")) for r in rows})
    prompt_hashes = sorted({str(r.get("prompt_sha256")) for r in rows if r.get("prompt_sha256")})
    label_orders = {tuple(r.get("label_order", [])) for r in rows}

    counts_by_id: dict[str, int] = defaultdict(int)
    for example_id, _ in keys:
        counts_by_id[str(example_id)] += 1
    incomplete_ids: list[str] = []
    if expected_k is not None:
        incomplete_ids = sorted(k for k, n in counts_by_id.items() if n != expected_k)

    warnings = []
    failures = []
    if malformed_lines:
        failures.append(f"{malformed_lines} malformed JSONL lines")
    if dupes:
        failures.append(f"duplicate example/repeat keys: {dupes[:10]}")
    if request_errors:
        failures.append(f"request errors: {len(request_errors)}")
    if parse_errors:
        failures.append(f"parse errors: {len(parse_errors)}")
    if argmax_bad:
        warnings.append(f"label/probability argmax inconsistencies: {len(argmax_bad)}")
    if norm_bad:
        warnings.append(f"raw probability sums >0.02 away from one: {len(norm_bad)}")
    if len(requested) != 1:
        failures.append(f"multiple requested model IDs in one file: {requested}")
    if len(returned) > 1:
        warnings.append(f"gateway returned multiple model IDs: {returned}")
    if len(prompt_types) != 1 or len(prompt_hashes) > 1:
        failures.append(f"mixed prompt conditions/hashes: types={prompt_types}, hashes={prompt_hashes}")
    if len(label_orders) > 1:
        failures.append(f"mixed label orders in one file: {sorted(label_orders)}")
    if incomplete_ids:
        failures.append(f"items not having expected K={expected_k}: {incomplete_ids[:10]} ({len(incomplete_ids)} total)")

    usage_present = sum(bool(r.get("usage")) for r in rows)
    latency_present = sum(r.get("latency_s") is not None for r in rows)
    if rows and usage_present < len(rows):
        warnings.append(f"usage metadata missing on {len(rows) - usage_present}/{len(rows)} rows")
    if rows and latency_present < len(rows):
        warnings.append(f"latency missing on {len(rows) - latency_present}/{len(rows)} rows")

    return {
        "file": str(path),
        "sha256": sha256(path),
        "n_rows": len(rows),
        "n_unique_ids": len(counts_by_id),
        "requested_models": requested,
        "returned_models": returned,
        "prompt_types": prompt_types,
        "prompt_hashes": prompt_hashes,
        "label_orders": [list(x) for x in sorted(label_orders)],
        "request_errors": len(request_errors),
        "parse_errors": len(parse_errors),
        "argmax_inconsistencies": len(argmax_bad),
        "normalization_warnings": len(norm_bad),
        "warnings": warnings,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--expected-k", type=int)
    p.add_argument("--out", type=Path, default=Path("results/processed/audit.json"))
    p.add_argument("--allow-fail", action="store_true")
    args = p.parse_args()

    report = [audit_file(path, args.expected_k) for path in args.paths]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for row in report:
        print(f"{row['status']:4} {row['file']}")
        for msg in row["failures"]:
            print(f"  FAIL: {msg}")
        for msg in row["warnings"]:
            print(f"  WARN: {msg}")
    print(f"Wrote {args.out}")
    if any(r["status"] == "FAIL" for r in report) and not args.allow_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
