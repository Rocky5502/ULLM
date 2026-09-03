#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src

collect() {
  local pattern="$1"
  shopt -s nullglob
  local files=($pattern)
  shopt -u nullglob
  if (( ${#files[@]} == 0 )); then
    echo "No files matched: $pattern" >&2
    exit 1
  fi
  printf '%s\n' "${files[@]}"
}

mapfile -t det < <(collect 'results/raw/frozen-det-neutral-v1/*__deterministic__neutral.jsonl')
mapfile -t samp < <(collect 'results/raw/frozen-sampling-neutral-v1/*__sampling__neutral.jsonl')
mapfile -t strict < <(collect 'results/raw/robust-strict-v1/*__deterministic__strict_logic.jsonl')
mapfile -t definition < <(collect 'results/raw/robust-definition-v1/*__deterministic__definition_aware.jsonl')
mapfile -t order < <(collect 'results/raw/robust-label-order-v1/*__deterministic__neutral.jsonl')
mapfile -t verifier < <(collect 'results/raw/frozen-verifier-v1/*__deterministic__verifier.jsonl')

echo "[1/12] Hard audit gates against frozen manifests"
python scripts/audit_run.py "${det[@]}" --manifest results/raw/frozen-det-neutral-v1/manifest.json --expected-k 1 --out results/processed/audit_deterministic.json
python scripts/audit_run.py "${samp[@]}" --manifest results/raw/frozen-sampling-neutral-v1/manifest.json --expected-k 5 --out results/processed/audit_sampling.json
python scripts/audit_run.py "${strict[@]}" --manifest results/raw/robust-strict-v1/manifest.json --expected-k 1 --out results/processed/audit_strict.json
python scripts/audit_run.py "${definition[@]}" --manifest results/raw/robust-definition-v1/manifest.json --expected-k 1 --out results/processed/audit_definition.json
python scripts/audit_run.py "${order[@]}" --manifest results/raw/robust-label-order-v1/manifest.json --expected-k 1 --out results/processed/audit_label_order.json
python scripts/audit_run.py "${verifier[@]}" --manifest results/raw/frozen-verifier-v1/manifest.json --expected-k 1 --out results/processed/audit_verifier.json

echo "[2/12] RQ1 deterministic summaries"
python scripts/summarize_results.py "${det[@]}" --bins 15 --out results/processed/summary_neutral.csv

echo "[3/12] RQ1 verb-cluster bootstrap intervals"
python scripts/bootstrap_summary.py "${det[@]}" --bootstrap 10000 --confidence 0.95 --bins 15 --out results/processed/summary_bootstrap.csv

echo "[4/12] RQ2 repeated-sampling uncertainty"
python scripts/analyze_sampling.py "${samp[@]}" --expected-k 5 --out results/processed/sampling.csv --ranking-out results/processed/sampling_ranking.csv

echo "[5/12] Unified RQ2 failure ranking"
python scripts/analyze_uncertainty_ranking.py "${det[@]}" --sampling results/processed/sampling.csv --out results/processed/uncertainty_ranking.csv

echo "[6/12] RQ2 verb-cluster ranking intervals"
python scripts/bootstrap_uncertainty_ranking.py "${det[@]}" --sampling results/processed/sampling.csv --bootstrap 10000 --confidence 0.95 --out results/processed/uncertainty_ranking_bootstrap.csv

echo "[7/12] Paired A-C / B-D semantic updates"
python scripts/analyze_pairwise.py "${det[@]}" --bootstrap 10000 --out results/processed/pairwise.csv --transitions-out results/processed/pairwise_transitions.csv

echo "[8/12] Prompt and label-order robustness"
robust_all=("${det[@]}" "${strict[@]}" "${definition[@]}" "${order[@]}")
python scripts/analyze_prompt_robustness.py "${robust_all[@]}" --out results/processed/prompt_robustness.csv --item-out results/processed/prompt_robustness_items.csv

echo "[9/12] RQ3 threshold-realizable risk-coverage"
python scripts/analyze_selective.py "${det[@]}" --sampling results/processed/sampling.csv --coverages 1.0 0.9 0.8 0.7 0.5 --target-risks 0.10 0.05 --out results/processed/selective.csv

echo "[10/12] RQ3 cached selective-verifier policies"
python scripts/analyze_recheck.py --base "${det[@]}" --verifier "${verifier[@]}" --thresholds 0.10 0.20 0.30 0.40 --out results/processed/recheck.csv

echo "[11/12] Publication vector figures"
python scripts/make_result_figures.py --summary results/processed/summary_neutral.csv --sampling results/processed/sampling.csv --ranking results/processed/uncertainty_ranking.csv --selective results/processed/selective.csv --pairwise results/processed/pairwise.csv --robustness results/processed/prompt_robustness.csv --recheck results/processed/recheck.csv --outdir results/figures

echo "[12/12] Auto-generate LaTeX result tables"
python scripts/make_paper_tables.py --summary results/processed/summary_neutral.csv --bootstrap results/processed/summary_bootstrap.csv --ranking results/processed/uncertainty_ranking.csv --recheck results/processed/recheck.csv --outdir paper/generated

echo "Analysis complete. Every manuscript number is generated from PASS-audited artifacts."
