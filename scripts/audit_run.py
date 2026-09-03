#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    malformed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            malformed += 1
    return rows, malformed


def audit_file(
    path: Path,
    expected_k: int | None = None,
    manifest: dict[str, Any] | None = None,
    *,
    allow_argmax_inconsistency: bool = False,
) -> dict[str, Any]:
    rows, malformed_lines = load_jsonl(path)
    keys = [(r.get("example", {}).get("id"), int(r.get("repeat", 0))) for r in rows]
    dupes = [k for k, n in Counter(keys).items() if n > 1]
    request_errors = [r for r in rows if r.get("request_error")]
    parse_errors = [r for r in rows if not r.get("request_error") and r.get("prediction") is None]
    argmax_bad = [
        r for r in rows
        if r.get("prediction") and not r["prediction"].get("argmax_consistent", True)
    ]
    norm_bad = [
        r for r in rows
        if r.get("prediction")
        and float(r["prediction"].get("normalization_delta", 0.0)) > 0.02
    ]
    empty_reasons = [
        r for r in rows
        if r.get("prediction") and not str(r["prediction"].get("reason_short", "")).strip()
    ]

    requested = sorted({str(r.get("model_requested")) for r in rows})
    returned = sorted({str(r.get("model_returned")) for r in rows if r.get("model_returned")})
    prompt_types = sorted({str(r.get("prompt_type", "legacy")) for r in rows})
    prompt_hashes = sorted({str(r.get("prompt_sha256")) for r in rows if r.get("prompt_sha256")})
    label_orders = {tuple(r.get("label_order", [])) for r in rows}
    max_tokens_values = {
        int(r["max_tokens_requested"]) for r in rows if r.get("max_tokens_requested") is not None
    }
    temperatures = {float(r["temperature"]) for r in rows if r.get("temperature") is not None}
    missing_message_hashes = sum(not bool(r.get("messages_sha256")) for r in rows)

    counts_by_id: dict[str, int] = defaultdict(int)
    repeats_by_id: dict[str, set[int]] = defaultdict(set)
    for example_id, repeat in keys:
        counts_by_id[str(example_id)] += 1
        repeats_by_id[str(example_id)].add(repeat)

    if expected_k is None and manifest is not None:
        expected_k = int(manifest.get("samples_per_item", 1))

    incomplete_ids: list[str] = []
    bad_repeat_ids: list[str] = []
    if expected_k is not None:
        expected_repeats = set(range(expected_k))
        incomplete_ids = sorted(k for k, n in counts_by_id.items() if n != expected_k)
        bad_repeat_ids = sorted(k for k, reps in repeats_by_id.items() if reps != expected_repeats)

    warnings: list[str] = []
    failures: list[str] = []
    if malformed_lines:
        failures.append(f"{malformed_lines} malformed JSONL lines")
    if dupes:
        failures.append(f"duplicate example/repeat keys: {dupes[:10]}")
    if request_errors:
        failures.append(f"request errors: {len(request_errors)}")
    if parse_errors:
        failures.append(f"parse errors: {len(parse_errors)}")
    if argmax_bad:
        msg = f"label/probability argmax contract violations: {len(argmax_bad)}"
        if allow_argmax_inconsistency:
            warnings.append(msg + " (preserved as observed decision-distribution inconsistency)")
        else:
            failures.append(msg)
    if norm_bad:
        failures.append(f"raw probability sums >0.02 away from one: {len(norm_bad)}")
    if empty_reasons:
        failures.append(f"missing required one-sentence reason_short: {len(empty_reasons)}")
    if len(requested) != 1:
        failures.append(f"requested model IDs per file must be exactly one: {requested}")
    if len(returned) > 1:
        warnings.append(f"gateway returned multiple model IDs: {returned}")
    if len(prompt_types) != 1 or len(prompt_hashes) != 1:
        failures.append(f"mixed/missing prompt condition hashes: types={prompt_types}, hashes={prompt_hashes}")
    if len(label_orders) != 1:
        failures.append(f"mixed/missing label orders: {sorted(label_orders)}")
    if len(max_tokens_values) != 1:
        failures.append(f"mixed/missing max_tokens_requested: {sorted(max_tokens_values)}")
    if len(temperatures) != 1:
        failures.append(f"mixed/missing temperatures: {sorted(temperatures)}")
    if missing_message_hashes:
        failures.append(f"messages_sha256 missing on {missing_message_hashes} rows")
    if incomplete_ids:
        failures.append(
            f"items not having expected K={expected_k}: {incomplete_ids[:10]} ({len(incomplete_ids)} total)"
        )
    if bad_repeat_ids:
        failures.append(
            f"items with wrong repeat index set for K={expected_k}: {bad_repeat_ids[:10]} ({len(bad_repeat_ids)} total)"
        )

    if manifest is not None:
        if manifest.get("execution_mode") != "live":
            failures.append(
                f"run audit requires execution_mode=live, found {manifest.get('execution_mode')!r}"
            )
        expected_ids = {str(x) for x in manifest.get("selected_ids", [])}
        observed_ids = set(counts_by_id)
        missing_ids = sorted(expected_ids - observed_ids)
        extra_ids = sorted(observed_ids - expected_ids)
        if missing_ids:
            failures.append(f"IDs missing vs manifest: {missing_ids[:10]} ({len(missing_ids)} total)")
        if extra_ids:
            failures.append(f"IDs not present in manifest: {extra_ids[:10]} ({len(extra_ids)} total)")
        expected_rows = int(manifest.get("selected_n", len(expected_ids))) * int(expected_k or 1)
        if len(rows) != expected_rows:
            failures.append(f"row count {len(rows)} != manifest expectation {expected_rows}")
        if requested and requested[0] not in set(manifest.get("models", [])):
            failures.append(f"requested model {requested[0]} not in manifest models {manifest.get('models')}")
        if prompt_types and prompt_types[0] != manifest.get("prompt_type"):
            failures.append(f"prompt_type {prompt_types[0]} != manifest {manifest.get('prompt_type')}")
        if prompt_hashes and prompt_hashes[0] != manifest.get("prompt_sha256"):
            failures.append("prompt SHA-256 does not match manifest")
        if label_orders and list(next(iter(label_orders))) != manifest.get("label_order"):
            failures.append("label order does not match manifest")
        if max_tokens_values and next(iter(max_tokens_values)) != int(manifest.get("max_tokens", -1)):
            failures.append("max_tokens_requested does not match manifest")
        if temperatures and abs(
            next(iter(temperatures)) - float(manifest.get("temperature", float("nan")))
        ) > 1e-12:
            failures.append("temperature does not match manifest")

    usage_present = sum(bool(r.get("usage")) for r in rows)
    latency_present = sum(r.get("latency_s") is not None for r in rows)
    request_id_present = sum(bool(r.get("request_id")) for r in rows)
    http_status_present = sum(r.get("http_status") is not None for r in rows)
    attempts_present = sum(r.get("attempts_used") is not None for r in rows)
    retry_rows = [r for r in rows if isinstance(r.get("attempts_used"), int) and r["attempts_used"] > 1]
    non_200 = [r for r in rows if r.get("http_status") is not None and int(r["http_status"]) != 200]

    if rows and usage_present < len(rows):
        warnings.append(f"usage metadata missing on {len(rows) - usage_present}/{len(rows)} rows")
    if rows and latency_present < len(rows):
        warnings.append(f"latency missing on {len(rows) - latency_present}/{len(rows)} rows")
    if rows and request_id_present < len(rows):
        warnings.append(f"request ID missing on {len(rows) - request_id_present}/{len(rows)} rows")
    if rows and attempts_present < len(rows):
        warnings.append(f"attempt-count metadata missing on {len(rows) - attempts_present}/{len(rows)} rows")
    if rows and http_status_present < len(rows):
        warnings.append(f"HTTP-status metadata missing on {len(rows) - http_status_present}/{len(rows)} rows")
    if retry_rows:
        warnings.append(f"successful rows requiring >1 HTTP attempt: {len(retry_rows)}")
    if non_200:
        failures.append(f"successful records with non-200 final HTTP status: {len(non_200)}")

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
        "argmax_inconsistency_policy": "preserve-and-warn" if allow_argmax_inconsistency else "strict-fail",
        "normalization_contract_failures": len(norm_bad),
        "empty_reason_failures": len(empty_reasons),
        "retry_rows": len(retry_rows),
        "usage_present": usage_present,
        "latency_present": latency_present,
        "request_id_present": request_id_present,
        "http_status_present": http_status_present,
        "attempts_present": attempts_present,
        "warnings": warnings,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--expected-k", type=int)
    p.add_argument("--out", type=Path, default=Path("results/processed/audit.json"))
    p.add_argument("--allow-fail", action="store_true")
    p.add_argument(
        "--allow-argmax-inconsistency",
        action="store_true",
        help=(
            "Preserve schema-valid rows whose stated label disagrees with the reported probability argmax. "
            "These rows remain scientific observations and are reported as contract-consistency warnings; "
            "all other audit failures remain fatal."
        ),
    )
    args = p.parse_args()

    manifest: dict[str, Any] | None = None
    global_failures: list[str] = []
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if manifest.get("execution_mode") != "live":
            global_failures.append(
                f"manifest execution_mode must be live for scientific analysis, found {manifest.get('execution_mode')!r}"
            )
        dataset_path = Path(str(manifest.get("dataset_path", "")))
        if not dataset_path.exists():
            global_failures.append(f"manifest dataset path missing locally: {dataset_path}")
        elif sha256(dataset_path) != manifest.get("dataset_sha256"):
            global_failures.append("local dataset SHA-256 differs from frozen manifest")

        config_path = Path("configs/experiment.yaml")
        models_path = Path("configs/models.yaml")
        if config_path.exists() and sha256(config_path) != manifest.get("config_sha256"):
            global_failures.append("current experiment config differs from frozen manifest")
        if models_path.exists() and sha256(models_path) != manifest.get("models_sha256"):
            global_failures.append("current model config differs from frozen manifest")

    report = [
        audit_file(
            path,
            args.expected_k,
            manifest,
            allow_argmax_inconsistency=args.allow_argmax_inconsistency,
        )
        for path in args.paths
    ]
    requested_files = [
        r["requested_models"][0]
        for r in report
        if len(r.get("requested_models", [])) == 1
    ]
    if manifest is not None:
        expected_models = list(manifest.get("models", []))
        missing_model_files = sorted(set(expected_models) - set(requested_files))
        duplicate_model_files = [m for m, n in Counter(requested_files).items() if n > 1]
        if missing_model_files:
            global_failures.append(f"missing output file(s) for manifest model(s): {missing_model_files}")
        if duplicate_model_files:
            global_failures.append(f"multiple output files for model(s): {duplicate_model_files}")

    payload = {
        "manifest": str(args.manifest) if args.manifest else None,
        "manifest_sha256": sha256(args.manifest) if args.manifest else None,
        "contract_adjudication": {
            "allow_argmax_inconsistency": bool(args.allow_argmax_inconsistency),
            "rule": (
                "preserve stated label as discrete decision and probability vector as continuous report; "
                "do not retry or repair schema-valid disagreement rows"
                if args.allow_argmax_inconsistency
                else "strict label-equals-probability-argmax contract"
            ),
        },
        "global_failures": global_failures,
        "files": report,
        "status": "PASS" if not global_failures and all(r["status"] == "PASS" for r in report) else "FAIL",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"RUN {payload['status']} manifest={payload['manifest']}")
    print(
        "Contract policy: "
        + ("PRESERVE+WARN argmax inconsistencies" if args.allow_argmax_inconsistency else "STRICT")
    )
    for msg in global_failures:
        print(f"  FAIL: {msg}")
    for row in report:
        print(f"{row['status']:4} {row['file']}")
        for msg in row["failures"]:
            print(f"  FAIL: {msg}")
        for msg in row["warnings"]:
            print(f"  WARN: {msg}")
    print(f"Wrote {args.out}")
    if payload["status"] == "FAIL" and not args.allow_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
