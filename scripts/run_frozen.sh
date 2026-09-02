#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src
python scripts/preflight.py
python scripts/check_models.py
python -m ullm.run --mode deterministic --prompt neutral --limit 20 --run-id smoke-neutral-v1
printf 'Inspect smoke-neutral-v1. Type RUN to continue: '
read -r answer
[[ "$answer" == "RUN" ]] || { echo "Stopped before paid full run."; exit 1; }
python -m ullm.run --mode deterministic --prompt neutral --run-id frozen-det-neutral-v1
python -m ullm.run --mode sampling --prompt neutral --run-id frozen-sampling-neutral-v1
python -m ullm.run --mode deterministic --prompt strict_logic --limit 120 --run-id robust-strict-v1
python -m ullm.run --mode deterministic --prompt definition_aware --limit 120 --run-id robust-definition-v1
python -m ullm.run --mode deterministic --prompt neutral --label-order "Unknown,False,True" --limit 120 --run-id robust-label-order-v1
