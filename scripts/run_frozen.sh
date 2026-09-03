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
  local manifest="results/raw/${run_id}/manifest.json"
  python scripts/audit_run.py "${files[@]}" \
    --manifest "$manifest" \
    --expected-k "$expected_k" --out "$out"
  python scripts/audit_completion_budget.py "${files[@]}"
  python scripts/audit_model_controls.py "${files[@]}" --manifest "$manifest"
}

seal_run() {
  local run_id="$1"
  python scripts/checksum_run.py "results/raw/${run_id}" \
    --out "results/raw/${run_id}.checksums.json"
}

echo "[1/12] Validate exact dataset/protocol and rehearse the complete study without provider calls"
python scripts/preflight.py
python scripts/freeze_protocol.py
python scripts/offline_rehearsal.py
python scripts/environment_snapshot.py

echo "[2/12] Snapshot live gateway model catalogue (no completion calls yet)"
python scripts/check_models.py

echo "No paid chat-completion calls have been made by this script yet."
printf 'Type SMOKE exactly to authorize the 100-call paid v4 smoke test: '
read -r smoke_answer
[[ "$smoke_answer" == "SMOKE" ]] || { echo "Stopped before any paid completion call."; exit 1; }

echo "[3/12] Balanced v4 smoke: 20 examples x all five models"
run_or_resume smoke-neutral-v4 --mode deterministic --prompt neutral --limit 20

echo "[4/12] Hard-audit completion budget + model controls + integrity seal before full paid study"
audit_run smoke-neutral-v4 '*__deterministic__neutral.jsonl' 1 results/processed/audit_smoke_v4.json
seal_run smoke-neutral-v4
smoke=(results/raw/smoke-neutral-v4/*__deterministic__neutral.jsonl)
python scripts/summarize_results.py "${smoke[@]}" --bins 15 --out results/processed/summary_smoke_v4.csv
printf 'V4 smoke gate PASSED. Type RUN exactly to authorize the remaining 15,800 main-study calls before retries: '
read -r answer
[[ "$answer" == "RUN" ]] || { echo "Stopped after smoke and before the full paid run."; exit 1; }

echo "[5/12] Full neutral deterministic run"
run_or_resume frozen-det-neutral-v1 --mode deterministic --prompt neutral
audit_run frozen-det-neutral-v1 '*__deterministic__neutral.jsonl' 1 results/processed/audit_deterministic.json
seal_run frozen-det-neutral-v1

echo "[6/12] Full neutral repeated sampling (K=5)"
run_or_resume frozen-sampling-neutral-v1 --mode sampling --prompt neutral
audit_run frozen-sampling-neutral-v1 '*__sampling__neutral.jsonl' 5 results/processed/audit_sampling.json
seal_run frozen-sampling-neutral-v1

echo "[7/12] Strict-logic robustness subset"
run_or_resume robust-strict-v1 --mode deterministic --prompt strict_logic --limit 120
audit_run robust-strict-v1 '*__deterministic__strict_logic.jsonl' 1 results/processed/audit_strict.json
seal_run robust-strict-v1

echo "[8/12] Definition-aware robustness subset"
run_or_resume robust-definition-v1 --mode deterministic --prompt definition_aware --limit 120
audit_run robust-definition-v1 '*__deterministic__definition_aware.jsonl' 1 results/processed/audit_definition.json
seal_run robust-definition-v1

echo "[9/12] Label-order robustness subset"
run_or_resume robust-label-order-v1 --mode deterministic --prompt neutral --label-order Unknown,False,True --limit 120
audit_run robust-label-order-v1 '*__deterministic__neutral.jsonl' 1 results/processed/audit_label_order.json
seal_run robust-label-order-v1

echo "[10/12] Full cached aspect-sensitive verifier"
run_or_resume frozen-verifier-v1 --mode deterministic --prompt verifier
audit_run frozen-verifier-v1 '*__deterministic__verifier.jsonl' 1 results/processed/audit_verifier.json
seal_run frozen-verifier-v1

echo "[11/12] Run statistical analyses, vector figures, and generated tables"
bash scripts/analyze_frozen.sh

echo "[12/12] Final local tests and post-run environment snapshot"
pytest -q
python scripts/environment_snapshot.py

echo "DONE: frozen calls, hard audits, SHA-256 evidence manifests, analysis, figures, and manuscript tables completed."
