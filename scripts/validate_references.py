#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

CITE_RE = re.compile(r"\\cite(?:p|t|author|year)?\s*\{([^}]+)\}")
BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}")


def collect_citations(text: str) -> set[str]:
    keys: set[str] = set()
    for match in CITE_RE.finditer(text):
        keys.update(k.strip() for k in match.group(1).split(",") if k.strip())
    return keys


def collect_bibitems(text: str) -> tuple[set[str], list[str]]:
    raw = BIBITEM_RE.findall(text)
    duplicates = sorted({k for k in raw if raw.count(k) > 1})
    return set(raw), duplicates


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--paper", type=Path, default=Path("paper/main.tex"))
    p.add_argument(
        "--references", type=Path, default=Path("paper/references_manual.tex")
    )
    p.add_argument(
        "--allow-uncited",
        action="store_true",
        help="Do not fail if bibliography contains uncited entries",
    )
    args = p.parse_args()

    paper = args.paper.read_text(encoding="utf-8")
    refs = args.references.read_text(encoding="utf-8")
    citations = collect_citations(paper)
    bibitems, duplicates = collect_bibitems(refs)
    missing = sorted(citations - bibitems)
    uncited = sorted(bibitems - citations)

    failures: list[str] = []
    if missing:
        failures.append(f"cited keys missing from bibliography: {missing}")
    if duplicates:
        failures.append(f"duplicate bibliography keys: {duplicates}")
    if uncited and not args.allow_uncited:
        failures.append(f"uncited bibliography entries: {uncited}")

    print(f"Citation audit: {len(citations)} cited keys, {len(bibitems)} bibliography entries")
    for message in failures:
        print(f"FAIL: {message}")
    if not failures:
        print("Reference-key audit PASS")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
