#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def finish_reason(row: dict[str, Any]) -> str | None:
    raw = row.get("raw_response") or {}
    choices = raw.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return None
    value = choices[0].get("finish_reason")
    return str(value) if value is not None else None


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fail a live run if any preserved provider response exhausted its completion budget."
    )
    p.add_argument("paths", nargs="+", type=Path)
    args = p.parse_args()

    exhausted: list[tuple[str, str, int | None]] = []
    checked = 0
    for path in args.paths:
        for row in load_jsonl(path):
            checked += 1
            if finish_reason(row) != "length":
                continue
            usage = row.get("usage") or {}
            exhausted.append(
                (
                    path.name,
                    str((row.get("example") or {}).get("id")),
                    usage.get("completion_tokens"),
                )
            )

    print(f"completion-budget audit: checked={checked} exhausted={len(exhausted)}")
    for file_name, example_id, completion_tokens in exhausted[:50]:
        print(
            f"FAIL finish_reason=length file={file_name} example={example_id} "
            f"completion_tokens={completion_tokens}"
        )
    if exhausted:
        raise SystemExit(1)
    print("PASS: no preserved response ended with finish_reason=length")


if __name__ == "__main__":
    main()
