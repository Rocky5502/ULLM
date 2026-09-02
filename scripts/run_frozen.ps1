$ErrorActionPreference = "Stop"

Write-Host "[1/5] Validate environment and frozen data"
python scripts/preflight.py

Write-Host "[2/5] Snapshot live gateway model catalogue"
python scripts/check_models.py

Write-Host "[3/5] Smoke test: 16 shuffled examples across all five models"
$env:PYTHONPATH = "src"
python -m ullm.run --mode deterministic --protocol strict --limit 16 --run-id smoke-v2

Write-Host "Inspect results/raw/smoke-v2 before continuing."
$answer = Read-Host "Type RUN to launch the frozen experiment"
if ($answer -ne "RUN") { throw "Stopped before paid full run." }

Write-Host "[4/5] Full deterministic runs: strict + bare robustness"
python -m ullm.run --mode deterministic --protocol strict --protocol bare --run-id frozen-det-v2

Write-Host "[5/5] Full repeated sampling: strict protocol, K from config"
python -m ullm.run --mode sampling --protocol strict --run-id frozen-sampling-v2

Write-Host "Frozen calls complete. Run scripts/analyze_frozen.ps1 next."
