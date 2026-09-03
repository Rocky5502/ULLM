#!/usr/bin/env python3
"""Guard the boundary between pre-run placeholders and post-run empirical claims.

The pre mode is CI-safe and requires the manuscript to remain explicitly unevaluated.
The post mode is intended for the local real-results phase and refuses a submission-like
manuscript unless audited outputs and generated empirical artifacts exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "main.tex"
GENERATED = [
    ROOT / "paper" / "generated" / "rq1_table.tex",
    ROOT / "paper" / "generated" / "rq2_table.tex",
    ROOT / "paper" / "generated" / "rq3_table.tex",
]
EXPECTED_AUDITS = [
    ROOT / "results" / "processed" / "audit_deterministic.json",
    ROOT / "results" / "processed" / "audit_sampling.json",
    ROOT / "results" / "processed" / "audit_strict.json",
    ROOT / "results" / "processed" / "audit_definition.json",
    ROOT / "results" / "processed" / "audit_label_order.json",
    ROOT / "results" / "processed" / "audit_verifier.json",
]
EXPECTED_FIGURES = [
    ROOT / "results" / "figures" / "rq1_group_c_uncertainty.pdf",
]
CANONICAL_PROCESSED = [
    "summary_neutral.csv",
    "summary_bootstrap.csv",
    "sampling.csv",
    "uncertainty_ranking.csv",
    "uncertainty_ranking_bootstrap.csv",
    "pairwise.csv",
    "pairwise_transitions.csv",
    "prompt_robustness.csv",
    "selective.csv",
    "recheck.csv",
    "hypothesis_evidence.csv",
]
ANALYSIS_MANIFEST = ROOT / "results" / "processed" / "analysis_manifest.json"

PREDECLARED_SENTINELS = (
    "All empirical values in this section remain \\textbf{TBD}",
    "Empirical conclusions remain \\textbf{TBD}",
)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def json_obj(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def audit_status(path: Path) -> str | None:
    obj = json_obj(path)
    if obj is None:
        return None
    value = obj.get("status")
    return str(value) if value is not None else None


def pre_gate(errors: list[str]) -> None:
    paper = read(PAPER)
    for sentinel in PREDECLARED_SENTINELS:
        if sentinel not in paper:
            fail(errors, f"pre-run manuscript sentinel missing: {sentinel}")
    for path in GENERATED:
        text = read(path)
        if "TBD" not in text:
            fail(errors, f"pre-run generated table unexpectedly lacks TBD: {path.relative_to(ROOT)}")
    committed_like = [p for p in EXPECTED_FIGURES if p.exists()]
    if committed_like:
        fail(errors, f"pre-run empirical result figure unexpectedly present: {committed_like}")


def post_gate(errors: list[str]) -> None:
    paper = read(PAPER)
    if "TBD" in paper:
        fail(errors, "post-run manuscript still contains TBD")
    for path in GENERATED:
        text = read(path)
        if "TBD" in text:
            fail(errors, f"post-run generated table still contains TBD: {path.relative_to(ROOT)}")
    for path in EXPECTED_AUDITS:
        if not path.is_file():
            fail(errors, f"post-run audit missing: {path.relative_to(ROOT)}")
            continue
        status = audit_status(path)
        if status != "PASS":
            fail(errors, f"post-run audit is not PASS ({status!r}): {path.relative_to(ROOT)}")
    for path in EXPECTED_FIGURES:
        if not path.is_file() or path.stat().st_size == 0:
            fail(errors, f"post-run empirical figure missing/empty: {path.relative_to(ROOT)}")

    for name in CANONICAL_PROCESSED:
        path = ROOT / "results" / "processed" / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(errors, f"post-run processed artifact missing/empty: results/processed/{name}")

    provenance = json_obj(ANALYSIS_MANIFEST)
    if provenance is None:
        fail(errors, "post-run canonical analysis_manifest.json is missing or invalid")
    else:
        if provenance.get("status") != "PASS":
            fail(errors, "post-run analysis provenance manifest is not PASS")
        if provenance.get("evidence_class") != "canonical-live-analysis":
            fail(errors, "post-run analysis provenance is not marked canonical-live-analysis")
        if not provenance.get("analysis_git_commit"):
            fail(errors, "post-run analysis provenance lacks analysis Git commit")
        if provenance.get("scientific_tree_dirty") is not False:
            fail(errors, "post-run analysis provenance did not verify a clean scientific tree")
        if len(provenance.get("raw_runs", [])) != 6:
            fail(errors, "post-run analysis provenance does not cover all six raw run stages")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("pre", "post"), required=True)
    args = p.parse_args()

    errors: list[str] = []
    try:
        if args.mode == "pre":
            pre_gate(errors)
        else:
            post_gate(errors)
    except FileNotFoundError as exc:
        fail(errors, f"required manuscript artifact missing: {exc}")

    if errors:
        print(f"Manuscript evidence gate {args.mode.upper()} FAIL")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print(f"Manuscript evidence gate {args.mode.upper()} PASS")


if __name__ == "__main__":
    main()
