$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

$detDir = "results/raw/frozen-det-neutral-v1"
$sampDir = "results/raw/frozen-sampling-neutral-v1"
$strictDir = "results/raw/robust-strict-v1"
$definitionDir = "results/raw/robust-definition-v1"
$orderDir = "results/raw/robust-label-order-v1"
$verifierDir = "results/raw/frozen-verifier-v1"

$det = Get-ChildItem "$detDir/*__deterministic__neutral.jsonl"
$samp = Get-ChildItem "$sampDir/*__sampling__neutral.jsonl"
$strict = Get-ChildItem "$strictDir/*__deterministic__strict_logic.jsonl"
$definition = Get-ChildItem "$definitionDir/*__deterministic__definition_aware.jsonl"
$order = Get-ChildItem "$orderDir/*__deterministic__neutral.jsonl"
$verifier = Get-ChildItem "$verifierDir/*__deterministic__verifier.jsonl"

Write-Host "[1/14] Hard audit gates against frozen manifests"
python scripts/audit_run.py @($det.FullName) --manifest "$detDir/manifest.json" --expected-k 1 --out results/processed/audit_deterministic.json
python scripts/audit_run.py @($samp.FullName) --manifest "$sampDir/manifest.json" --expected-k 5 --out results/processed/audit_sampling.json
python scripts/audit_run.py @($strict.FullName) --manifest "$strictDir/manifest.json" --expected-k 1 --out results/processed/audit_strict.json
python scripts/audit_run.py @($definition.FullName) --manifest "$definitionDir/manifest.json" --expected-k 1 --out results/processed/audit_definition.json
python scripts/audit_run.py @($order.FullName) --manifest "$orderDir/manifest.json" --expected-k 1 --out results/processed/audit_label_order.json
python scripts/audit_run.py @($verifier.FullName) --manifest "$verifierDir/manifest.json" --expected-k 1 --out results/processed/audit_verifier.json

Write-Host "[2/14] RQ1 deterministic summaries"
python scripts/summarize_results.py @($det.FullName) --bins 15 --out results/processed/summary_neutral.csv

Write-Host "[3/14] RQ1 verb-cluster bootstrap intervals"
python scripts/bootstrap_summary.py @($det.FullName) --bootstrap 10000 --confidence 0.95 --bins 15 --out results/processed/summary_bootstrap.csv

Write-Host "[4/14] RQ2 repeated-sampling uncertainty"
python scripts/analyze_sampling.py @($samp.FullName) --expected-k 5 --out results/processed/sampling.csv --ranking-out results/processed/sampling_ranking.csv

Write-Host "[5/14] Unified RQ2 failure ranking across all four signals"
python scripts/analyze_uncertainty_ranking.py @($det.FullName) --sampling results/processed/sampling.csv --out results/processed/uncertainty_ranking.csv

Write-Host "[6/14] RQ2 verb-cluster ranking intervals"
python scripts/bootstrap_uncertainty_ranking.py @($det.FullName) --sampling results/processed/sampling.csv --bootstrap 10000 --confidence 0.95 --out results/processed/uncertainty_ranking_bootstrap.csv

Write-Host "[7/14] Paired A-C / B-D semantic updates"
python scripts/analyze_pairwise.py @($det.FullName) --bootstrap 10000 --out results/processed/pairwise.csv --transitions-out results/processed/pairwise_transitions.csv

Write-Host "[8/14] Prompt and label-order robustness"
$robustAll = @($det.FullName) + @($strict.FullName) + @($definition.FullName) + @($order.FullName)
python scripts/analyze_prompt_robustness.py @robustAll --out results/processed/prompt_robustness.csv --item-out results/processed/prompt_robustness_items.csv

Write-Host "[9/14] RQ3 threshold-realizable risk-coverage"
python scripts/analyze_selective.py @($det.FullName) --sampling results/processed/sampling.csv --coverages 1.0 0.9 0.8 0.7 0.5 --target-risks 0.10 0.05 --out results/processed/selective.csv

Write-Host "[10/14] RQ3 cached selective-verifier policies"
python scripts/analyze_recheck.py --base @($det.FullName) --verifier @($verifier.FullName) --thresholds 0.10 0.20 0.30 0.40 --out results/processed/recheck.csv

Write-Host "[11/14] Predeclared H1-H4 evidence synthesis and Holm family"
python scripts/analyze_hypotheses.py --det @($det.FullName) --bootstrap results/processed/summary_bootstrap.csv --ranking-bootstrap results/processed/uncertainty_ranking_bootstrap.csv --recheck results/processed/recheck.csv --permutations 10000 --out results/processed/hypothesis_evidence.csv

Write-Host "[12/14] Publication vector figures"
python scripts/make_result_figures.py --summary results/processed/summary_neutral.csv --sampling results/processed/sampling.csv --ranking results/processed/uncertainty_ranking.csv --selective results/processed/selective.csv --pairwise results/processed/pairwise.csv --robustness results/processed/prompt_robustness.csv --recheck results/processed/recheck.csv --outdir results/figures

Write-Host "[13/14] Auto-generate LaTeX result tables (no hand-copied numbers)"
python scripts/make_paper_tables.py --summary results/processed/summary_neutral.csv --bootstrap results/processed/summary_bootstrap.csv --ranking results/processed/uncertainty_ranking.csv --ranking-bootstrap results/processed/uncertainty_ranking_bootstrap.csv --recheck results/processed/recheck.csv --outdir paper/generated

Write-Host "[14/14] Freeze dual-SHA analysis provenance"
python scripts/freeze_analysis_provenance.py --out results/processed/analysis_manifest.json

Write-Host "Analysis complete. Empirical outputs are PASS-audited, preregistered evidence is synthesized without best-result selection, and derived artifacts are sealed to raw-run + analysis-code provenance."
