$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

function Assert-LastExit {
    param([Parameter(Mandatory=$true)][string]$Step)
    if ($LASTEXITCODE -ne 0) { throw "Python command failed during: $Step" }
}

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

if ($det.Count -ne 5 -or $samp.Count -ne 5 -or $strict.Count -ne 5 -or $definition.Count -ne 5 -or $order.Count -ne 5 -or $verifier.Count -ne 5) {
    throw "Expected exactly five model JSONL files for each canonical run."
}

Write-Host "[1/12] Hard audit gates against frozen manifests under adjudication A1"
python scripts/audit_run.py @($det.FullName) --manifest "$detDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_deterministic.json
Assert-LastExit "deterministic audit"
python scripts/audit_run.py @($samp.FullName) --manifest "$sampDir/manifest.json" --expected-k 5 --allow-argmax-inconsistency --out results/processed/audit_sampling.json
Assert-LastExit "sampling audit"
python scripts/audit_run.py @($strict.FullName) --manifest "$strictDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_strict.json
Assert-LastExit "strict audit"
python scripts/audit_run.py @($definition.FullName) --manifest "$definitionDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_definition.json
Assert-LastExit "definition audit"
python scripts/audit_run.py @($order.FullName) --manifest "$orderDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_label_order.json
Assert-LastExit "label-order audit"
python scripts/audit_run.py @($verifier.FullName) --manifest "$verifierDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_verifier.json
Assert-LastExit "verifier audit"

Write-Host "[2/12] Exploratory decision-distribution consistency diagnostic"
$allOutputs = @($det.FullName) + @($samp.FullName) + @($strict.FullName) + @($definition.FullName) + @($order.FullName) + @($verifier.FullName)
python scripts/analyze_contract_consistency.py @allOutputs --out results/processed/decision_distribution_consistency.csv --items-out results/processed/decision_distribution_consistency_items.csv
Assert-LastExit "contract-consistency analysis"

Write-Host "[3/12] RQ1 deterministic summaries"
python scripts/summarize_results.py @($det.FullName) --bins 15 --out results/processed/summary_neutral.csv
Assert-LastExit "RQ1 deterministic summaries"

Write-Host "[4/12] Verb-cluster bootstrap intervals"
python scripts/bootstrap_summary.py @($det.FullName) --bootstrap 10000 --confidence 0.95 --bins 15 --out results/processed/summary_bootstrap.csv
Assert-LastExit "RQ1 bootstrap"

Write-Host "[5/12] RQ2 repeated-sampling uncertainty"
python scripts/analyze_sampling.py @($samp.FullName) --expected-k 5 --out results/processed/sampling.csv --ranking-out results/processed/sampling_ranking.csv
Assert-LastExit "RQ2 sampling"

Write-Host "[6/12] Unified RQ2 failure ranking across all four signals"
python scripts/analyze_uncertainty_ranking.py @($det.FullName) --sampling results/processed/sampling.csv --out results/processed/uncertainty_ranking.csv
Assert-LastExit "RQ2 failure ranking"

Write-Host "[7/12] Paired A-C / B-D semantic updates"
python scripts/analyze_pairwise.py @($det.FullName) --bootstrap 10000 --out results/processed/pairwise.csv --transitions-out results/processed/pairwise_transitions.csv
Assert-LastExit "paired semantic analysis"

Write-Host "[8/12] Prompt and label-order robustness"
$robustAll = @($det.FullName) + @($strict.FullName) + @($definition.FullName) + @($order.FullName)
python scripts/analyze_prompt_robustness.py @robustAll --out results/processed/prompt_robustness.csv --item-out results/processed/prompt_robustness_items.csv
Assert-LastExit "prompt robustness"

Write-Host "[9/12] RQ3 threshold-realizable risk-coverage"
python scripts/analyze_selective.py @($det.FullName) --sampling results/processed/sampling.csv --coverages 1.0 0.9 0.8 0.7 0.5 --target-risks 0.10 0.05 --out results/processed/selective.csv
Assert-LastExit "RQ3 selective-risk analysis"

Write-Host "[10/12] RQ3 cached selective-verifier policies"
python scripts/analyze_recheck.py --base @($det.FullName) --verifier @($verifier.FullName) --thresholds 0.10 0.20 0.30 0.40 --out results/processed/recheck.csv
Assert-LastExit "RQ3 verifier analysis"

Write-Host "[11/12] Publication vector figures"
python scripts/make_result_figures.py --summary results/processed/summary_neutral.csv --sampling results/processed/sampling.csv --ranking results/processed/uncertainty_ranking.csv --selective results/processed/selective.csv --pairwise results/processed/pairwise.csv --robustness results/processed/prompt_robustness.csv --recheck results/processed/recheck.csv --outdir results/figures
Assert-LastExit "result figures"

Write-Host "[12/12] Auto-generate LaTeX result tables (no hand-copied numbers)"
python scripts/make_paper_tables.py --summary results/processed/summary_neutral.csv --bootstrap results/processed/summary_bootstrap.csv --ranking results/processed/uncertainty_ranking.csv --recheck results/processed/recheck.csv --outdir paper/generated
Assert-LastExit "paper tables"

Write-Host "Analysis complete. Stated labels remain discrete decisions; probability vectors remain continuous uncertainty reports; disagreement is separately quantified."
