$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

function Invoke-ULLMRun {
    param(
        [Parameter(Mandatory=$true)][string]$RunId,
        [Parameter(Mandatory=$true)][string[]]$RunArgs
    )
    $manifest = "results/raw/$RunId/manifest.json"
    if (Test-Path $manifest) {
        Write-Host "Resuming compatible run $RunId and replacing any failed rows"
        python -m ullm.run @RunArgs --run-id $RunId --resume --retry-failures
    } else {
        python -m ullm.run @RunArgs --run-id $RunId
    }
    if ($LASTEXITCODE -ne 0) { throw "Run failed: $RunId" }
}

function Audit-Run {
    param(
        [Parameter(Mandatory=$true)][string]$RunId,
        [Parameter(Mandatory=$true)][string]$Pattern,
        [Parameter(Mandatory=$true)][int]$ExpectedK,
        [Parameter(Mandatory=$true)][string]$OutFile
    )
    $files = Get-ChildItem "results/raw/$RunId/$Pattern"
    if ($files.Count -eq 0) { throw "No outputs found for $RunId / $Pattern" }
    python scripts/audit_run.py @($files.FullName) --manifest "results/raw/$RunId/manifest.json" --expected-k $ExpectedK --out $OutFile
    if ($LASTEXITCODE -ne 0) { throw "Audit failed: $RunId" }
}

Write-Host "[1/12] Validate project, preregistration, environment, and dataset"
python scripts/preflight.py
if ($LASTEXITCODE -ne 0) { throw "Preflight failed" }

Write-Host "[2/12] Snapshot live gateway model catalogue (no completion calls yet)"
python scripts/check_models.py
if ($LASTEXITCODE -ne 0) { throw "Configured gateway model catalogue check failed" }

Write-Host "No paid chat-completion calls have been made by this script yet."
$smokeAnswer = Read-Host "Type SMOKE exactly to authorize the 100-call paid smoke test"
if ($smokeAnswer -ne "SMOKE") { throw "Stopped before any paid completion call." }

Write-Host "[3/12] Balanced smoke test: 20 examples x all five models"
Invoke-ULLMRun -RunId "smoke-neutral-v1" -RunArgs @("--mode","deterministic","--prompt","neutral","--limit","20")

Write-Host "[4/12] Hard-audit smoke outputs before authorizing the full paid study"
Audit-Run -RunId "smoke-neutral-v1" -Pattern "*__deterministic__neutral.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_smoke.json"
$smoke = Get-ChildItem "results/raw/smoke-neutral-v1/*__deterministic__neutral.jsonl"
python scripts/summarize_results.py @($smoke.FullName) --bins 15 --out results/processed/summary_smoke.csv
if ($LASTEXITCODE -ne 0) { throw "Smoke summary failed" }

Write-Host "Smoke gate PASSED. Review the printed per-model rows and catalogue snapshot."
$answer = Read-Host "Type RUN exactly to authorize the remaining 15,800 main-study calls before retries"
if ($answer -ne "RUN") { throw "Stopped after smoke and before the full paid run." }

Write-Host "[5/12] Full neutral deterministic run: 400 items x 5 models"
Invoke-ULLMRun -RunId "frozen-det-neutral-v1" -RunArgs @("--mode","deterministic","--prompt","neutral")
Audit-Run -RunId "frozen-det-neutral-v1" -Pattern "*__deterministic__neutral.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_deterministic.json"

Write-Host "[6/12] Full repeated sampling: K=5 x 400 items x 5 models"
Invoke-ULLMRun -RunId "frozen-sampling-neutral-v1" -RunArgs @("--mode","sampling","--prompt","neutral")
Audit-Run -RunId "frozen-sampling-neutral-v1" -Pattern "*__sampling__neutral.jsonl" -ExpectedK 5 -OutFile "results/processed/audit_sampling.json"

Write-Host "[7/12] Fixed 120-item strict-logic robustness run"
Invoke-ULLMRun -RunId "robust-strict-v1" -RunArgs @("--mode","deterministic","--prompt","strict_logic","--limit","120")
Audit-Run -RunId "robust-strict-v1" -Pattern "*__deterministic__strict_logic.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_strict.json"

Write-Host "[8/12] Fixed 120-item definition-aware robustness run"
Invoke-ULLMRun -RunId "robust-definition-v1" -RunArgs @("--mode","deterministic","--prompt","definition_aware","--limit","120")
Audit-Run -RunId "robust-definition-v1" -Pattern "*__deterministic__definition_aware.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_definition.json"

Write-Host "[9/12] Fixed 120-item label-order audit"
Invoke-ULLMRun -RunId "robust-label-order-v1" -RunArgs @("--mode","deterministic","--prompt","neutral","--label-order","Unknown,False,True","--limit","120")
Audit-Run -RunId "robust-label-order-v1" -Pattern "*__deterministic__neutral.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_label_order.json"

Write-Host "[10/12] Full cached aspect-sensitive verifier run"
Invoke-ULLMRun -RunId "frozen-verifier-v1" -RunArgs @("--mode","deterministic","--prompt","verifier")
Audit-Run -RunId "frozen-verifier-v1" -Pattern "*__deterministic__verifier.jsonl" -ExpectedK 1 -OutFile "results/processed/audit_verifier.json"

Write-Host "[11/12] Run all statistical analyses, vector figures, and generated tables"
& "$PSScriptRoot/analyze_frozen.ps1"
if ($LASTEXITCODE -ne 0) { throw "Analysis pipeline failed" }

Write-Host "[12/12] Final local test suite"
pytest -q
if ($LASTEXITCODE -ne 0) { throw "Final tests failed" }

Write-Host "DONE: frozen calls, audits, analysis, figures, and manuscript tables completed."
