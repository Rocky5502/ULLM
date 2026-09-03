$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

function Invoke-CheckedPython {
    param([Parameter(ValueFromRemainingArguments=$true)][object[]]$Args)

    # PowerShell can bind an explicitly parenthesized array argument as one nested
    # object when it crosses a function boundary. Flatten nested arrays here so
    # each JSONL path is forwarded to Python as its own argv element rather than
    # as one space-joined filename.
    $flatArgs = @()
    foreach ($arg in $Args) {
        if ($arg -is [System.Array]) {
            foreach ($item in $arg) {
                $flatArgs += [string]$item
            }
        } else {
            $flatArgs += [string]$arg
        }
    }

    & python @flatArgs
    if ($LASTEXITCODE -ne 0) { throw "Python command failed: python $($flatArgs -join ' ')" }
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

Write-Host "[1/12] Hard audit gates against frozen manifests under adjudication A1"
Invoke-CheckedPython scripts/audit_run.py @($det.FullName) --manifest "$detDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_deterministic.json
Invoke-CheckedPython scripts/audit_run.py @($samp.FullName) --manifest "$sampDir/manifest.json" --expected-k 5 --allow-argmax-inconsistency --out results/processed/audit_sampling.json
Invoke-CheckedPython scripts/audit_run.py @($strict.FullName) --manifest "$strictDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_strict.json
Invoke-CheckedPython scripts/audit_run.py @($definition.FullName) --manifest "$definitionDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_definition.json
Invoke-CheckedPython scripts/audit_run.py @($order.FullName) --manifest "$orderDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_label_order.json
Invoke-CheckedPython scripts/audit_run.py @($verifier.FullName) --manifest "$verifierDir/manifest.json" --expected-k 1 --allow-argmax-inconsistency --out results/processed/audit_verifier.json

Write-Host "[2/12] Exploratory decision-distribution consistency diagnostic"
$allOutputs = @($det.FullName) + @($samp.FullName) + @($strict.FullName) + @($definition.FullName) + @($order.FullName) + @($verifier.FullName)
Invoke-CheckedPython scripts/analyze_contract_consistency.py @allOutputs --out results/processed/decision_distribution_consistency.csv --items-out results/processed/decision_distribution_consistency_items.csv

Write-Host "[3/12] RQ1 deterministic summaries"
Invoke-CheckedPython scripts/summarize_results.py @($det.FullName) --bins 15 --out results/processed/summary_neutral.csv

Write-Host "[4/12] Verb-cluster bootstrap intervals"
Invoke-CheckedPython scripts/bootstrap_summary.py @($det.FullName) --bootstrap 10000 --confidence 0.95 --bins 15 --out results/processed/summary_bootstrap.csv

Write-Host "[5/12] RQ2 repeated-sampling uncertainty"
Invoke-CheckedPython scripts/analyze_sampling.py @($samp.FullName) --expected-k 5 --out results/processed/sampling.csv --ranking-out results/processed/sampling_ranking.csv

Write-Host "[6/12] Unified RQ2 failure ranking across all four signals"
Invoke-CheckedPython scripts/analyze_uncertainty_ranking.py @($det.FullName) --sampling results/processed/sampling.csv --out results/processed/uncertainty_ranking.csv

Write-Host "[7/12] Paired A-C / B-D semantic updates"
Invoke-CheckedPython scripts/analyze_pairwise.py @($det.FullName) --bootstrap 10000 --out results/processed/pairwise.csv --transitions-out results/processed/pairwise_transitions.csv

Write-Host "[8/12] Prompt and label-order robustness"
$robustAll = @($det.FullName) + @($strict.FullName) + @($definition.FullName) + @($order.FullName)
Invoke-CheckedPython scripts/analyze_prompt_robustness.py @robustAll --out results/processed/prompt_robustness.csv --item-out results/processed/prompt_robustness_items.csv

Write-Host "[9/12] RQ3 threshold-realizable risk-coverage"
Invoke-CheckedPython scripts/analyze_selective.py @($det.FullName) --sampling results/processed/sampling.csv --coverages 1.0 0.9 0.8 0.7 0.5 --target-risks 0.10 0.05 --out results/processed/selective.csv

Write-Host "[10/12] RQ3 cached selective-verifier policies"
Invoke-CheckedPython scripts/analyze_recheck.py --base @($det.FullName) --verifier @($verifier.FullName) --thresholds 0.10 0.20 0.30 0.40 --out results/processed/recheck.csv

Write-Host "[11/12] Publication vector figures"
Invoke-CheckedPython scripts/make_result_figures.py --summary results/processed/summary_neutral.csv --sampling results/processed/sampling.csv --ranking results/processed/uncertainty_ranking.csv --selective results/processed/selective.csv --pairwise results/processed/pairwise.csv --robustness results/processed/prompt_robustness.csv --recheck results/processed/recheck.csv --outdir results/figures

Write-Host "[12/12] Auto-generate LaTeX result tables (no hand-copied numbers)"
Invoke-CheckedPython scripts/make_paper_tables.py --summary results/processed/summary_neutral.csv --bootstrap results/processed/summary_bootstrap.csv --ranking results/processed/uncertainty_ranking.csv --recheck results/processed/recheck.csv --outdir paper/generated

Write-Host "Analysis complete. Stated labels remain discrete decisions; probability vectors remain continuous uncertainty reports; disagreement is separately quantified."
