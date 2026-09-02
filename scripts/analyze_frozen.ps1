$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

$det = Get-ChildItem "results/raw/frozen-det-neutral-v1/*__deterministic__neutral.jsonl"
$samp = Get-ChildItem "results/raw/frozen-sampling-neutral-v1/*__sampling__neutral.jsonl"
$strict = Get-ChildItem "results/raw/robust-strict-v1/*__deterministic__strict_logic.jsonl"
$definition = Get-ChildItem "results/raw/robust-definition-v1/*__deterministic__definition_aware.jsonl"
$order = Get-ChildItem "results/raw/robust-label-order-v1/*__deterministic__neutral.jsonl"
$verifier = Get-ChildItem "results/raw/frozen-verifier-v1/*__deterministic__verifier.jsonl"

Write-Host "[1/8] Hard audit gates"
python scripts/audit_run.py @($det.FullName) --expected-k 1 --out results/processed/audit_deterministic.json
python scripts/audit_run.py @($samp.FullName) --expected-k 5 --out results/processed/audit_sampling.json
python scripts/audit_run.py @($strict.FullName) --expected-k 1 --out results/processed/audit_strict.json
python scripts/audit_run.py @($definition.FullName) --expected-k 1 --out results/processed/audit_definition.json
python scripts/audit_run.py @($order.FullName) --expected-k 1 --out results/processed/audit_label_order.json
python scripts/audit_run.py @($verifier.FullName) --expected-k 1 --out results/processed/audit_verifier.json

Write-Host "[2/8] RQ1 deterministic summaries"
python scripts/summarize_results.py @($det.FullName) --bins 15 --out results/processed/summary_neutral.csv

Write-Host "[3/8] RQ2 sampling uncertainty"
python scripts/analyze_sampling.py @($samp.FullName) --expected-k 5 --out results/processed/sampling.csv --ranking-out results/processed/sampling_ranking.csv

Write-Host "[4/8] Paired A-C / B-D semantic updates"
python scripts/analyze_pairwise.py @($det.FullName) --bootstrap 10000 --out results/processed/pairwise.csv --transitions-out results/processed/pairwise_transitions.csv

Write-Host "[5/8] Prompt and label-order robustness"
$robustAll = @($det.FullName) + @($strict.FullName) + @($definition.FullName) + @($order.FullName)
python scripts/analyze_prompt_robustness.py @robustAll --out results/processed/prompt_robustness.csv --item-out results/processed/prompt_robustness_items.csv

Write-Host "[6/8] RQ3 risk-coverage"
python scripts/analyze_selective.py @($det.FullName) --sampling results/processed/sampling.csv --out results/processed/selective.csv

Write-Host "[7/8] RQ3 cached selective verifier policies"
python scripts/analyze_recheck.py --base @($det.FullName) --verifier @($verifier.FullName) --out results/processed/recheck.csv

Write-Host "[8/8] Publication vector figures"
python scripts/make_result_figures.py --summary results/processed/summary_neutral.csv --sampling results/processed/sampling.csv --ranking results/processed/sampling_ranking.csv --selective results/processed/selective.csv --pairwise results/processed/pairwise.csv --robustness results/processed/prompt_robustness.csv --recheck results/processed/recheck.csv --outdir results/figures

Write-Host "Analysis complete. Never copy a number into the paper unless traceable to these outputs and a PASS audit."
