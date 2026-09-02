$ErrorActionPreference = "Stop"

Write-Host "[1/8] Validate environment, preregistration, and dataset"
python scripts/preflight.py

Write-Host "[2/8] Snapshot live gateway model catalogue"
python scripts/check_models.py

$env:PYTHONPATH = "src"

Write-Host "[3/8] Balanced smoke test: 20 examples, all five models, neutral prompt"
python -m ullm.run --mode deterministic --prompt neutral --limit 20 --run-id smoke-neutral-v1

Write-Host "Inspect results/raw/smoke-neutral-v1 before continuing."
$answer = Read-Host "Type RUN to launch paid frozen calls"
if ($answer -ne "RUN") { throw "Stopped before paid full run." }

Write-Host "[4/8] Full deterministic primary experiment: 400 items x 5 models"
python -m ullm.run --mode deterministic --prompt neutral --run-id frozen-det-neutral-v1

Write-Host "[5/8] Full repeated sampling: K=5 from config"
python -m ullm.run --mode sampling --prompt neutral --run-id frozen-sampling-neutral-v1

Write-Host "[6/8] Fixed 120-item prompt robustness: strict logic + definition aware"
python -m ullm.run --mode deterministic --prompt strict_logic --limit 120 --run-id robust-strict-v1
python -m ullm.run --mode deterministic --prompt definition_aware --limit 120 --run-id robust-definition-v1

Write-Host "[7/8] Fixed label-order audit on the same 120-item neutral subset"
python -m ullm.run --mode deterministic --prompt neutral --label-order "Unknown,False,True" --limit 120 --run-id robust-label-order-v1

Write-Host "[8/8] Cache full aspect-sensitive verifier predictions for RQ3"
python -m ullm.run --mode deterministic --prompt verifier --run-id frozen-verifier-v1

Write-Host "Frozen calls complete. Run scripts/analyze_frozen.ps1 after audits pass."
