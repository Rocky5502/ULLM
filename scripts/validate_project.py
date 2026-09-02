#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from ullm.prompts import PROMPTS

EXPECTED_RQ_COUNT = 3
STALE_TOKENS = (
    "gpt-5.4",
    "llama-4-maverick",
    "primary_protocol",
    "protocols: [strict, bare]",
)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=Path("configs/experiment.yaml"))
    p.add_argument("--models", type=Path, default=Path("configs/models.yaml"))
    p.add_argument(
        "--hypotheses", type=Path, default=Path("configs/preregistered_hypotheses.yaml")
    )
    p.add_argument("--paper", type=Path, default=Path("paper/main.tex"))
    p.add_argument("--readme", type=Path, default=Path("README.md"))
    args = p.parse_args()

    errors: list[str] = []
    for path in (args.config, args.models, args.hypotheses, args.paper, args.readme):
        if not path.exists():
            fail(f"missing required file: {path}", errors)
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        raise SystemExit(1)

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    models_cfg = yaml.safe_load(args.models.read_text(encoding="utf-8"))
    hypotheses_cfg = yaml.safe_load(args.hypotheses.read_text(encoding="utf-8"))
    paper = args.paper.read_text(encoding="utf-8")
    readme = args.readme.read_text(encoding="utf-8")

    required_config = {
        "seed",
        "base_url",
        "input_file",
        "output_dir",
        "max_concurrency",
        "request_timeout_s",
        "max_retries",
        "max_tokens",
        "primary_prompt",
        "prompt_robustness",
        "label_order_robustness",
        "verifier",
        "deterministic",
        "sampling",
        "selective",
        "statistics",
        "labels",
    }
    missing_config = sorted(required_config - set(config))
    if missing_config:
        fail(f"experiment config missing keys: {missing_config}", errors)

    labels = list(config.get("labels", []))
    if labels != ["True", "False", "Unknown"]:
        fail(f"labels must be exactly [True, False, Unknown], found {labels}", errors)

    primary = config.get("primary_prompt")
    if primary != "neutral":
        fail(f"primary_prompt must remain neutral before frozen run, found {primary!r}", errors)
    if primary not in PROMPTS:
        fail(f"unknown primary prompt: {primary!r}", errors)

    robust = config.get("prompt_robustness", {})
    n_robust = int(robust.get("n_examples", 0))
    if n_robust <= 0 or n_robust % 4 != 0:
        fail("prompt_robustness.n_examples must be positive and divisible by four", errors)
    robust_prompts = list(robust.get("prompt_types", []))
    if robust_prompts != ["strict_logic", "definition_aware"]:
        fail(
            "prompt robustness must remain [strict_logic, definition_aware] before results",
            errors,
        )
    for prompt in robust_prompts:
        if prompt not in PROMPTS:
            fail(f"unknown robustness prompt: {prompt}", errors)

    verifier = config.get("verifier", {}).get("prompt_type")
    if verifier != "verifier" or verifier not in PROMPTS:
        fail(f"verifier prompt must be 'verifier', found {verifier!r}", errors)

    alternate = list(config.get("label_order_robustness", {}).get("alternate_order", []))
    if sorted(alternate) != sorted(labels) or alternate == labels:
        fail(f"invalid alternate label order: {alternate}", errors)

    if int(config.get("deterministic", {}).get("samples_per_item", 0)) != 1:
        fail("deterministic.samples_per_item must be 1", errors)
    if int(config.get("sampling", {}).get("samples_per_item", 0)) != 5:
        fail("primary sampling K must remain 5", errors)
    if float(config.get("deterministic", {}).get("temperature", -1)) != 0.0:
        fail("deterministic temperature must remain 0.0", errors)
    if float(config.get("sampling", {}).get("temperature", -1)) != 0.7:
        fail("sampling temperature must remain 0.7", errors)

    stats = config.get("statistics", {})
    if stats.get("cluster_key") != "verb":
        fail("statistics.cluster_key must remain verb", errors)
    if int(stats.get("bootstrap_replicates", 0)) != 10000:
        fail("statistics.bootstrap_replicates must remain 10000", errors)
    if stats.get("multiple_testing") != "holm":
        fail("statistics.multiple_testing must remain holm", errors)

    models = list(models_cfg.get("models", []))
    ids = [str(m.get("id")) for m in models]
    families = [str(m.get("family")) for m in models]
    if len(ids) != 5 or len(set(ids)) != 5:
        fail(f"expected exactly five unique model IDs, found {ids}", errors)
    if len(set(families)) != 5:
        fail(f"expected five distinct model families, found {families}", errors)
    for model_id in ids:
        if model_id not in paper:
            fail(f"configured model ID missing from manuscript: {model_id}", errors)
        if model_id not in readme:
            fail(f"configured model ID missing from README: {model_id}", errors)

    for token in STALE_TOKENS:
        if token in paper or token in readme:
            fail(f"stale pre-freeze token still present in paper/README: {token}", errors)

    hypotheses = hypotheses_cfg.get("hypotheses", {})
    if len(hypotheses) != 4:
        fail(
            f"expected four directional hypotheses H1-H4 in preregistration, found {len(hypotheses)}",
            errors,
        )
    rqs = {str(row.get("rq")) for row in hypotheses.values()}
    if rqs != {"RQ1", "RQ2", "RQ3"}:
        fail(f"hypotheses must cover exactly RQ1/RQ2/RQ3, found {sorted(rqs)}", errors)
    if paper.count("\\paragraph{RQ1:") != 1 or paper.count("\\paragraph{RQ2:") != 1 or paper.count("\\paragraph{RQ3:") != 1:
        fail("manuscript must contain exactly one paragraph definition for each RQ1/RQ2/RQ3", errors)

    required_generated = [
        Path("paper/generated/rq1_table.tex"),
        Path("paper/generated/rq2_table.tex"),
        Path("paper/generated/rq3_table.tex"),
    ]
    for path in required_generated:
        if not path.exists():
            fail(f"missing generated-table placeholder: {path}", errors)

    call_budget = (
        len(ids) * 400 * int(config["deterministic"]["samples_per_item"])
        + len(ids) * 400 * int(config["sampling"]["samples_per_item"])
        + len(ids) * n_robust * len(robust_prompts)
        + len(ids) * int(config["label_order_robustness"]["n_examples"])
        + len(ids) * 400
    )
    if call_budget != 15800:
        fail(f"frozen main-study call budget drifted from 15,800 to {call_budget}", errors)

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "models": ids,
        "prompts": sorted(PROMPTS),
        "primary_prompt": primary,
        "robustness_n": n_robust,
        "main_call_budget": call_budget,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
