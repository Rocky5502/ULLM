#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src
python scripts/preflight.py
python scripts/check_models.py
python -m ullm.run --mode deterministic --protocol strict --limit 16 --run-id smoke-v2
printf 'Inspect smoke-v2. Type RUN to continue: '
read -r answer
[[ "$answer" == "RUN" ]] || { echo "Stopped before paid full run."; exit 1; }
python -m ullm.run --mode deterministic --protocol strict --protocol bare --run-id frozen-det-v2
python -m ullm.run --mode sampling --protocol strict --run-id frozen-sampling-v2
