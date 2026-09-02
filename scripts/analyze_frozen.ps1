$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

$det = Get-ChildItem "results/raw/frozen-det-v2/*__deterministic__strict.jsonl"
$samp = Get-ChildItem "results/raw/frozen-sampling-v2/*__sampling__strict.jsonl"

python scripts/summarize_results.py @($det.FullName) --out results/processed/summary_strict.csv
python scripts/analyze_sampling.py @($samp.FullName) --out results/processed/sampling.csv --ranking-out results/processed/sampling_ranking.csv
python scripts/analyze_selective.py @($det.FullName) --sampling results/processed/sampling.csv --out results/processed/selective.csv
python scripts/make_result_figures.py --summary results/processed/summary_strict.csv --sampling results/processed/sampling.csv --selective results/processed/selective.csv --outdir results/figures

Write-Host "Analysis complete. Never copy a number into the paper unless traceable to these outputs."
