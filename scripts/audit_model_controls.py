#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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


def reasoning_content(row: dict[str, Any]) -> str:
    raw = row.get("raw_response") or {}
    choices = raw.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message") or {}
    if not isinstance(message, dict):
        return ""
    value = message.get("reasoning_content")
    return "" if value is None else str(value)


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Verify frozen model-specific request controls were recorded exactly and, "
            "when DeepSeek thinking is disabled, that the gateway did not return CoT."
        )
    )
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    args = p.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected = manifest.get("model_request_overrides", {}) or {}
    if not isinstance(expected, dict):
        raise SystemExit("FAIL: manifest model_request_overrides is not a mapping")

    checked = 0
    override_mismatches: list[tuple[str, str, str]] = []
    reasoning_violations: list[tuple[str, str]] = []

    for path in args.paths:
        for row in load_jsonl(path):
            checked += 1
            model = str(row.get("model_requested", ""))
            example_id = str((row.get("example") or {}).get("id", ""))
            observed = row.get("request_overrides", {}) or {}
            wanted = expected.get(model, {}) or {}
            if observed != wanted:
                override_mismatches.append((path.name, model, example_id))

            thinking = wanted.get("thinking") if isinstance(wanted, dict) else None
            thinking_type = thinking.get("type") if isinstance(thinking, dict) else None
            if thinking_type == "disabled" and reasoning_content(row).strip():
                reasoning_violations.append((path.name, example_id))

    print(
        "model-control audit: "
        f"checked={checked} override_mismatches={len(override_mismatches)} "
        f"reasoning_violations={len(reasoning_violations)}"
    )
    for file_name, model, example_id in override_mismatches[:50]:
        print(
            f"FAIL request-overrides mismatch file={file_name} "
            f"model={model} example={example_id}"
        )
    for file_name, example_id in reasoning_violations[:50]:
        print(
            f"FAIL thinking-disabled route returned reasoning_content "
            f"file={file_name} example={example_id}"
        )

    if override_mismatches or reasoning_violations:
        raise SystemExit(1)
    print("PASS: frozen model-specific controls were recorded and honored")


if __name__ == "__main__":
    main()
