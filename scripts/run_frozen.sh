#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src

run_or_resume() {
  local run_id="$1"; shift
  if [[ -f "results/raw/${run_id}/manifest.json" ]]; then
    echo "Resuming compatible run ${run_id} and replacing failed rows"
    python -m ullm.run "$@" --run-id "$run_id" --resume --retry-failures
  else
    python -m ullm.run "$@" --run-id "$run_id"
  fi
}

audit_run() {
  local run_id="$1" pattern="$2" expected_k="$3" out="$4"
  shopt -s nullglob
  local files=(results/raw/"$run_id"/$pattern)
  shopt -u nullglob
  if (( ${#files[@]} == 0 )); then
    echo "No outputs found for ${run_id}/${pattern}" >&2
    exit 1
  fi
  python scripts/audit_run.py "${files[@]}" \
    --manifest "results/raw/${run_id}/manifest.json" \
    --expected-k "$expected_k" --out "$out"
}

echo "[1/12] Validate project, preregistration, environment, and dataset"
python scripts/preflight.py

echo "[2/12] Snapshot live gateway model catalogue"
python scripts/check_models.py

echo "[3/12] Balanced smoke test: 20 examples x all five models"
run_or_resume smoke-neutral-v1 --mode deterministic --prompt neutral --limit 20

echo "[4/12] Hard-audit smoke before authorizing the paid study"
audit_run smoke-neutral-v1 '*__deterministic__neutral.jsonl' 1 results/processed/audit_smoke.json
smoke=(results/raw/smoke-neutral-v1/*__deterministic__neutral.jsonl)
python scripts/summarize_results.py "${smoke[@]}" --bins 15 --out results/processed/summary_smoke.csv
printf 'Smoke gate PASSED. Type RUN exactly to launch paid frozen calls: '
read -r answer
[[ "$answer" == "RUN" ]] || { echo "Stopped before paid full run."; exit 1; }

echo "[5/12] Full neutral deterministic run"
run_or_resume frozen-det-neutral-v1 --mode deterministic --prompt neutral
audit_run frozen-det-neutral-v1 '*__deterministic__neutral.jsonl' 1 results/processed/audit_deterministic.json

echo "[6/12] Full neutral repeated sampling (K=5)"
run_or_resume frozen-sampling-neutral-v1 --mode sampling --prompt neutral
audit_run frozen-sampling-neutral-v1 '*__sampling__neutral.jsonl' 5 results/processed/audit_sampling.json

echo "[7/12] Strict-logic robustness subset"
run_or_resume robust-strict-v1 --mode deterministic --prompt strict_logic --limit 120
audit_run robust-strict-v1 '*__deterministic__strict_logic.jsonl' 1 results/processed/audit_strict.json

echo "[8/12] Definition-aware robustness subset"
run_or_resume robust-definition-v1 --mode deterministic --prompt definition_aware --limit 120
audit_run robust-definition-v1 '*__deterministic__definition_aware.jsonl' 1 results/processed/audit_definition.json

echo "[9/12] Label-order robustness subset"
run_or_resume robust-label-order-v1 --mode deterministic --prompt neutral --label-order Unknown,False,True --limit 120
audit_run robust-label-order-v1 '*__deterministic__neutral.jsonl' 1 results/processed/audit_label_order.json

echo "[10/12] Full cached aspect-sensitive verifier"
run_or_resume frozen-verifier-v1 --mode deterministic --prompt verifier
audit_run frozen-verifier-v1 '*__deterministic__verifier.jsonl' 1 results/processed/audit_verifier.json

echo "[11/12] Run statistical analyses, vector figures, and generated tables"
bash scripts/analyze_frozen.sh

echo "[12/12] Final local tests"
pytest -q

echo "DONE: frozen calls, audits, analysis, figures, and manuscript tables completed."
