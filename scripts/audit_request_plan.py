#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_CONTENT_KEYS = {"messages", "raw_text", "raw_response", "premise", "hypothesis"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Malformed JSONL at {path}:{line_no}") from exc
        if not isinstance(row, dict):
            raise RuntimeError(f"Non-object JSON row at {path}:{line_no}")
        rows.append(row)
    return rows


def audit(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    plan_path = run_dir / "request_plan.jsonl"
    errors: list[str] = []

    if not manifest_path.exists():
        return {"status": "FAIL", "errors": [f"missing {manifest_path}"]}
    if not plan_path.exists():
        return {"status": "FAIL", "errors": [f"missing {plan_path}"]}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = load_jsonl(plan_path)

    if manifest.get("execution_mode") != "dry_run":
        errors.append("manifest execution_mode must be dry_run")
    if int(manifest.get("schema_version", 0)) < 3:
        errors.append("dry-run manifest schema_version must be >= 3")

    models = [str(x) for x in manifest.get("models", [])]
    model_request_overrides = manifest.get("model_request_overrides", {}) or {}
    if not isinstance(model_request_overrides, dict):
        errors.append("manifest model_request_overrides must be a mapping")
        model_request_overrides = {}
    selected_ids = {str(x) for x in manifest.get("selected_ids", [])}
    selected_n = int(manifest.get("selected_n", -1))
    repeats = int(manifest.get("samples_per_item", -1))
    expected = len(models) * selected_n * repeats
    if len(rows) != expected:
        errors.append(f"expected {expected} plan rows, found {len(rows)}")

    keys: list[tuple[str, str, int]] = []
    by_pair: dict[tuple[str, str], set[int]] = defaultdict(set)
    model_ids_seen: set[str] = set()
    example_ids_seen: set[str] = set()

    for i, row in enumerate(rows, start=1):
        forbidden = sorted(FORBIDDEN_CONTENT_KEYS & set(row))
        if forbidden:
            errors.append(f"row {i}: request plan leaked content keys {forbidden}")

        model = str(row.get("model_requested", ""))
        example_id = str(row.get("example_id", ""))
        try:
            rep = int(row.get("repeat", -1))
        except (TypeError, ValueError):
            rep = -1

        keys.append((model, example_id, rep))
        by_pair[(model, example_id)].add(rep)
        model_ids_seen.add(model)
        example_ids_seen.add(example_id)

        if model not in models:
            errors.append(f"row {i}: unexpected model {model!r}")
        if example_id not in selected_ids:
            errors.append(f"row {i}: unexpected example_id {example_id!r}")
        if rep < 0 or rep >= repeats:
            errors.append(f"row {i}: repeat {rep} outside expected range 0..{repeats - 1}")
        if float(row.get("temperature", -999)) != float(manifest.get("temperature", -998)):
            errors.append(f"row {i}: temperature drift")
        if int(row.get("max_tokens_requested", -1)) != int(manifest.get("max_tokens", -2)):
            errors.append(f"row {i}: max_tokens drift")
        expected_override = model_request_overrides.get(model, {})
        if row.get("request_overrides", {}) != expected_override:
            errors.append(f"row {i}: model request override drift")
        if row.get("prompt_type") != manifest.get("prompt_type"):
            errors.append(f"row {i}: prompt_type drift")
        if row.get("prompt_sha256") != manifest.get("prompt_sha256"):
            errors.append(f"row {i}: prompt hash drift")
        if list(row.get("label_order", [])) != list(manifest.get("label_order", [])):
            errors.append(f"row {i}: label order drift")
        message_hash = str(row.get("messages_sha256", ""))
        if not HEX64.fullmatch(message_hash):
            errors.append(f"row {i}: invalid messages_sha256")

    dupes = [key for key, n in Counter(keys).items() if n > 1]
    if dupes:
        errors.append(f"duplicate request keys: {dupes[:10]}")
    if model_ids_seen != set(models):
        errors.append(f"model coverage mismatch: expected={models}, seen={sorted(model_ids_seen)}")
    if example_ids_seen != selected_ids:
        errors.append(
            f"example coverage mismatch: missing={sorted(selected_ids - example_ids_seen)[:10]}, "
            f"extra={sorted(example_ids_seen - selected_ids)[:10]}"
        )

    expected_repeats = set(range(repeats))
    bad_pairs = [pair for pair, seen in by_pair.items() if seen != expected_repeats]
    if bad_pairs:
        errors.append(f"repeat coverage mismatch for {bad_pairs[:10]}")
    expected_pairs = {(m, e) for m in models for e in selected_ids}
    if set(by_pair) != expected_pairs:
        missing_pairs = sorted(expected_pairs - set(by_pair))
        errors.append(f"model/example pair coverage mismatch; missing={missing_pairs[:10]}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "run_dir": str(run_dir),
        "rows": len(rows),
        "expected_rows": expected,
        "models": models,
        "selected_n": selected_n,
        "repeats": repeats,
        "prompt_type": manifest.get("prompt_type"),
        "errors": errors,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    args = p.parse_args()
    result = audit(args.run_dir)
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
