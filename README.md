# The Imperfective Uncertainty in Large Language Models

Research artifact for an IASEAI'27 main-conference paper. The project builds on the ACL 2026 Best Paper **“The Imperfective Paradox in Large Language Models”** but asks a different question: **when event completion is semantically underdetermined, do LLMs represent the correct uncertainty relation, is that uncertainty faithful to their errors, and can it control risk?**

## Locked scientific thesis

In the critical ImperfectiveNLI Group C, the *world outcome* is unknown but the *NLI relation* is determinately `Unknown`. An ideal model should therefore be **confidently uncertain about the event** (`P(Unknown)` high), not confidently complete it (`P(True)` high) and not diffusely guess among labels. This separates semantic uncertainty from predictive uncertainty.

## Exactly three RQs

1. **RQ1 — Uncertainty Recognition:** Do frontier API LLMs recognize semantic under-specification and remain calibrated across Groups A–D?
2. **RQ2 — Uncertainty Faithfulness:** Which black-box signal—verbalized probabilities or repeated-sampling disagreement—best identifies aspectual errors and teleological overconfidence?
3. **RQ3 — Uncertainty-Aware Control:** Can selective defer/recheck lower completion errors at useful coverage without degrading valid atelic entailments?

## Frozen API panel

Primary panel: `gpt-5.6-sol`, `claude-sonnet-5`, `deepseek-v4-pro`, `qwen3.8-max`, `gemini-3.7-flash`. These are external gateway dependencies. **Never assume an ID is still routed to the same backend:** `scripts/check_models.py` snapshots `/v1/models` immediately before each frozen run and the experiment records both requested and returned IDs.

## Experiment matrix

- **Data:** exact upstream ImperfectiveNLI artifact, 400 examples, 100/group, pair-validated A↔C and B↔D.
- **Prompting:** `strict` primary + `bare` robustness; no chain-of-thought collection.
- **Single pass:** temperature 0, structured `P(True), P(False), P(Unknown)`.
- **Repeated sampling:** temperature 0.7, `K=5`; optional pre-declared `K=10` Group-C sensitivity only if needed.
- **RQ1 metrics:** Acc A–D, TBR, ΔAA, SUR, TOR@0.80, ADG, ECE/classwise ECE, Brier, NLL, matched-pair consistency.
- **RQ2 metrics:** predictive entropy, `1-maxprob`, sampling variation ratio/entropy, error AUROC/AUPRC, subclass and confidently-consistent-error analysis.
- **RQ3 metrics:** full risk–coverage curves, AURC, matched-coverage TBR, Group-D retention, defer/recheck rate, token usage.
- **Statistics:** 10,000 verb-cluster bootstrap resamples, 95% CIs, paired contrasts, Holm correction, verb-disjoint threshold tuning if optimization is used.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_imperfective_nli.py
python scripts/validate_dataset.py data/imperfectiveNLI.json
pytest -q
```

Set `ZZZ_API_KEY` in your shell **only**; never commit it. Then on Windows:

```powershell
.\scripts\run_frozen.ps1
.\scripts\analyze_frozen.ps1
```

The run script stops after a cross-model smoke test and requires typing `RUN` before paid full calls.

## Reproducibility guarantees

`data/MANIFEST.json` freezes the source file's upstream Git blob SHA-1 and expected structure. Each local download writes SHA-256 provenance. Every API record stores prompt hash, model requested/returned, timestamp, latency, usage, raw output and parsed output. The runner resumes by `(example_id, repeat)` rather than duplicating successful calls. Result figures are produced as both PDF and SVG; conceptual figures are editable TikZ.

## Repository map

- `src/ullm/` — API client, prompts, parsing, metrics, statistics, runner
- `configs/` — model panel, experiment settings, pre-registered hypotheses
- `data/` — provenance manifests + exact-source downloader/validator
- `docs/` — research plan, analysis plan, experiment protocol, reproducibility checklist
- `paper/` — AAAI-2027-style provisional IASEAI manuscript, editable TikZ, references
- `scripts/` — preflight, frozen execution, analysis, vector result figures
- `results/` — raw/processed outputs; large raw responses stay untracked by Git

## Status

**Stage 2 complete:** deeper preregistered design, current cross-family model panel, exact data-integrity checks, paired analyses, calibration/ranking/selective-control pipeline, resumable frozen-run scripts, stronger vector figures, and an expanded manuscript. **Empirical Results remain intentionally TBD** until paid API calls are run from a machine with `ZZZ_API_KEY`.
