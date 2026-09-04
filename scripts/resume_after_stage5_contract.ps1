$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

function Invoke-ULLMRun {
    param(
        [Parameter(Mandatory=$true)][string]$RunId,
        [Parameter(Mandatory=$true)][string[]]$RunArgs
    )
    $manifest = "results/raw/$RunId/manifest.json"
    if (Test-Path $manifest) {
        Write-Host "Resuming compatible run $RunId and replacing only request/parse failures"
        python -m ullm.run @RunArgs --run-id $RunId --resume --retry-failures
    } else {
        python -m ullm.run @RunArgs --run-id $RunId
    }
    if ($LASTEXITCODE -ne 0) { throw "Run failed: $RunId" }
}

function Audit-Run-A1 {
    param(
        [Parameter(Mandatory=$true)][string]$RunId,
        [Parameter(Mandatory=$true)][string]$Pattern,
        [Parameter(Mandatory=$true)][int]$ExpectedK,
        [Parameter(Mandatory=$true)][string]$OutFile
    )
    $files = Get-ChildItem "results/raw/$RunId/$Pattern"
    if ($files.Count -eq 0) { throw "No outputs found for $RunId / $Pattern" }
    $manifest = "results/raw/$RunId/manifest.json"

    python scripts/audit_run.py @($files.FullName) `
      --manifest $manifest `
      --expected-k $ExpectedK `
      --allow-argmax-inconsistency `
      --out $OutFile
    if ($LASTEXITCODE -ne 0) { throw "Scientific record audit failed: $RunId" }

    python scripts/audit_completion_budget.py @($files.FullName)
    if ($LASTEXITCODE -ne 0) { throw "Completion-budget audit failed: $RunId" }

    python scripts/audit_model_controls.py @($files.FullName) --manifest $manifest
    if ($LASTEXITCODE -ne 0) { throw "Model-control audit failed: $RunId" }
}

function Seal-Run {
    param([Parameter(Mandatory=$true)][string]$RunId)
    python scripts/checksum_run.py "results/raw/$RunId" --out "results/raw/$RunId.checksums.json"
    if ($LASTEXITCODE -ne 0) { throw "Checksum evidence manifest failed: $RunId" }
}

Write-Host "[A1/8] Re-audit the already-collected Stage 5 without changing or rerunning any response"
$detDir = "results/raw/frozen-det-neutral-v1"
$det = Get-ChildItem "$detDir/*__deterministic__neutral.jsonl"
if ($det.Count -ne 5) { throw "Expected five Stage-5 model files, found $($det.Count)" }
Audit-Run-A1 -RunId "frozen-det-neutral-v1" -Pattern "*__deterministic__neutral.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_deterministic.json"
Seal-Run -RunId "frozen-det-neutral-v1"
python scripts/analyze_contract_consistency.py @($det.FullName) `
  --out results/processed/decision_distribution_consistency_stage5.csv `
  --items-out results/processed/decision_distribution_consistency_stage5_items.csv
if ($LASTEXITCODE -ne 0) { throw "Stage-5 contract consistency analysis failed" }

Write-Host "Stage 5 is preserved exactly as collected. No selective retry/relabel/repair was performed."
$answer = Read-Host "Type CONTINUE exactly to authorize the remaining 13,800 planned main-study calls before retries"
if ($answer -ne "CONTINUE") { throw "Stopped after Stage-5 adjudication and before any Stage-6 call." }

Write-Host "[A2/8] Stage 6: full neutral repeated sampling — 10,000 calls before retries"
Invoke-ULLMRun -RunId "frozen-sampling-neutral-v1" -RunArgs @("--mode","sampling","--prompt","neutral")
Audit-Run-A1 -RunId "frozen-sampling-neutral-v1" -Pattern "*__sampling__neutral.jsonl" -ExpectedK 5 -OutFile "results/processed/audit_sampling.json"
Seal-Run -RunId "frozen-sampling-neutral-v1"

Write-Host "[A3/8] Stage 7: strict-logic robustness — 600 calls"
Invoke-ULLMRun -RunId "robust-strict-v1" -RunArgs @("--mode","deterministic","--prompt","strict_logic","--limit","120")
Audit-Run-A1 -RunId "robust-strict-v1" -Pattern "*__deterministic__strict_logic.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_strict.json"
Seal-Run -RunId "robust-strict-v1"

Write-Host "[A4/8] Stage 8: definition-aware robustness — 600 calls"
Invoke-ULLMRun -RunId "robust-definition-v1" -RunArgs @("--mode","deterministic","--prompt","definition_aware","--limit","120")
Audit-Run-A1 -RunId "robust-definition-v1" -Pattern "*__deterministic__definition_aware.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_definition.json"
Seal-Run -RunId "robust-definition-v1"

Write-Host "[A5/8] Stage 9: reversed label-order robustness — 600 calls"
Invoke-ULLMRun -RunId "robust-label-order-v1" -RunArgs @("--mode","deterministic","--prompt","neutral","--label-order","Unknown,False,True","--limit","120")
Audit-Run-A1 -RunId "robust-label-order-v1" -Pattern "*__deterministic__neutral.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_label_order.json"
Seal-Run -RunId "robust-label-order-v1"

Write-Host "[A6/8] Stage 10: full cached aspect-sensitive verifier — 2,000 calls"
Invoke-ULLMRun -RunId "frozen-verifier-v1" -RunArgs @("--mode","deterministic","--prompt","verifier")
Audit-Run-A1 -RunId "frozen-verifier-v1" -Pattern "*__deterministic__verifier.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_verifier.json"
Seal-Run -RunId "frozen-verifier-v1"

Write-Host "[A7/8] Frozen empirical analyses, contract-consistency diagnostics, figures, and tables"
& "$PSScriptRoot/analyze_frozen.ps1"
if ($LASTEXITCODE -ne 0) { throw "Analysis pipeline failed" }

Write-Host "[A8/8] Final local tests and environment snapshot"
pytest -q
if ($LASTEXITCODE -ne 0) { throw "Final tests failed" }
python scripts/environment_snapshot.py
if ($LASTEXITCODE -ne 0) { throw "Post-run environment snapshot failed" }

Write-Host "DONE: Stage 5 preserved under adjudication A1; remaining frozen runs, audits, checksums, analysis, figures, and tables completed."
