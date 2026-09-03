#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EXPECTED_MAIN_CALLS = 15_800


def run(cmd: list[str], *, env: dict[str, str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def main() -> None:
    dataset = ROOT / "data" / "imperfectiveNLI.json"
    if not dataset.exists():
        raise SystemExit(
            "data/imperfectiveNLI.json is missing. Run: python scripts/fetch_imperfective_nli.py"
        )

    exp = yaml.safe_load((ROOT / "configs" / "experiment.yaml").read_text(encoding="utf-8"))
    robust_n = int(exp["prompt_robustness"]["n_examples"])
    alternate_order = ",".join(exp["label_order_robustness"]["alternate_order"])
    verifier_prompt = str(exp["verifier"]["prompt_type"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")

    stages = [
        {
            "name": "neutral-deterministic",
            "mode": "deterministic",
            "prompt": "neutral",
            "limit": 0,
            "label_order": None,
            "expected": 2_000,
        },
        {
            "name": "neutral-sampling",
            "mode": "sampling",
            "prompt": "neutral",
            "limit": 0,
            "label_order": None,
            "expected": 10_000,
        },
        {
            "name": "strict-robustness",
            "mode": "deterministic",
            "prompt": "strict_logic",
            "limit": robust_n,
            "label_order": None,
            "expected": 600,
        },
        {
            "name": "definition-robustness",
            "mode": "deterministic",
            "prompt": "definition_aware",
            "limit": robust_n,
            "label_order": None,
            "expected": 600,
        },
        {
            "name": "label-order-robustness",
            "mode": "deterministic",
            "prompt": "neutral",
            "limit": int(exp["label_order_robustness"]["n_examples"]),
            "label_order": alternate_order,
            "expected": 600,
        },
        {
            "name": "verifier-cache",
            "mode": "deterministic",
            "prompt": verifier_prompt,
            "limit": 0,
            "label_order": None,
            "expected": 2_000,
        },
    ]

    records: list[dict] = []
    total = 0
    for stage in stages:
        run_id = f"offline-{stamp}-{stage['name']}"
        cmd = [
            sys.executable,
            "-m",
            "ullm.run",
            "--dry-run",
            "--mode",
            str(stage["mode"]),
            "--prompt",
            str(stage["prompt"]),
            "--run-id",
            run_id,
        ]
        if int(stage["limit"]):
            cmd += ["--limit", str(stage["limit"])]
        if stage["label_order"]:
            cmd += ["--label-order", str(stage["label_order"])]
        run(cmd, env=env)

        run_dir = ROOT / str(exp["output_dir"]) / run_id
        run([sys.executable, "scripts/audit_request_plan.py", str(run_dir)], env=env)
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        rows = sum(1 for line in (run_dir / "request_plan.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
        if rows != int(stage["expected"]):
            raise RuntimeError(
                f"{stage['name']}: expected {stage['expected']} planned calls, found {rows}"
            )
        total += rows
        records.append(
            {
                "stage": stage["name"],
                "run_id": run_id,
                "rows": rows,
                "prompt_type": manifest["prompt_type"],
                "mode": manifest["mode"],
                "selected_n": manifest["selected_n"],
                "samples_per_item": manifest["samples_per_item"],
                "label_order": manifest["label_order"],
                "dataset_sha256": manifest["dataset_sha256"],
                "config_sha256": manifest["config_sha256"],
                "models_sha256": manifest["models_sha256"],
                "git_commit": manifest["git_commit"],
            }
        )

    if total != EXPECTED_MAIN_CALLS:
        raise RuntimeError(
            f"Frozen request-plan budget mismatch: expected {EXPECTED_MAIN_CALLS}, got {total}"
        )

    out_dir = ROOT / "artifacts" / "local"
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = out_dir / f"offline_rehearsal_{stamp}.json"
    payload = {
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "api_calls_made": 0,
        "planned_main_calls": total,
        "expected_main_calls": EXPECTED_MAIN_CALLS,
        "stages": records,
    }
    snapshot.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Offline rehearsal snapshot: {snapshot}")
    print("PASS: the complete 15,800-call main-study request plan was constructed and audited without an API key.")


if __name__ == "__main__":
    main()
