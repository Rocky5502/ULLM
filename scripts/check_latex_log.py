#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("log", nargs="?", type=Path, default=Path("paper/main.log"))
    p.add_argument(
        "--max-overfull-vbox-pt",
        type=float,
        default=1.0,
        help="Allow tiny vertical float rounding but fail larger overfull vboxes",
    )
    args = p.parse_args()

    text = args.log.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []

    if re.search(r"Overfull \\hbox", text):
        snippets = re.findall(r"Overfull \\hbox[^\n]*", text)
        failures.append("overfull horizontal boxes: " + " | ".join(snippets[:5]))

    vboxes = [
        float(x)
        for x in re.findall(r"Overfull \\vbox \(([0-9.]+)pt too high\)", text)
    ]
    large_vboxes = [x for x in vboxes if x > args.max_overfull_vbox_pt]
    if large_vboxes:
        failures.append(f"overfull vertical boxes above tolerance: {large_vboxes[:5]}")

    bad_patterns = {
        "undefined citations": r"Package natbib Warning: There were undefined citations",
        "undefined references": r"LaTeX Warning: There were undefined references",
        "multiply defined labels": r"LaTeX Warning: There were multiply-defined labels",
        "rerun unresolved references": r"Rerun to get cross-references right",
        "missing file": r"LaTeX Error: File `[^']+' not found",
    }
    for label, pattern in bad_patterns.items():
        if re.search(pattern, text):
            failures.append(label)

    # Latexmk may include warnings from early passes in an aggregate console log, but
    # main.log is the final pdflatex pass. Any citation still undefined here is fatal.
    undefined_cite_lines = re.findall(
        r"Package natbib Warning: Citation `[^']+'[^\n]*undefined", text
    )
    if undefined_cite_lines:
        failures.append(
            "individual undefined citation warnings on final pass: "
            + " | ".join(undefined_cite_lines[:5])
        )

    print(f"LaTeX quality audit: {args.log}")
    if failures:
        for issue in failures:
            print(f"FAIL: {issue}")
        raise SystemExit(1)
    print("LaTeX quality audit PASS: no overfull hboxes or unresolved citation/reference errors")


if __name__ == "__main__":
    main()
