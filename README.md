# The Imperfective Uncertainty in Large Language Models

Research artifact for an IASEAI'27 main-conference paper. The project builds on the ACL 2026 Best Paper **“The Imperfective Paradox in Large Language Models”** but asks a different question: **when event completion is semantically underdetermined, do LLMs represent the correct uncertainty relation, is that uncertainty faithful to their errors, and can it control risk?**

## Locked scientific thesis

In the critical ImperfectiveNLI Group C, the *world outcome* is unknown but the *NLI relation* is determinately `Unknown`. An ideal model should therefore be **confidently uncertain about the event** (`P(Unknown)` high), not confidently complete it (`P(True)` high) and not diffusely guess among labels. This separates semantic uncertainty from predictive uncertainty.

## Exactly three RQs

1. **RQ1 — Uncertainty Recognition:** Do frontier API LLMs recognize semantic under-specification and remain calibrated across Groups A–D?
2. **RQ2 — Uncertainty Faithfulness:** Which black-box signal—verbalized probabilities or repeated-sampling disagreement—best identifies aspectual errors and teleological overconfidence?
3. **RQ3 — Uncertainty-Aware Control:** Can selective defer/recheck lower completion errors at useful coverage without degrading valid atelic entailments?

## Frozen API panel

Primary panel: `gpt-5.4`, `claude-sonnet-5`, `deepseek-v4-pro`, `qwen3.8-max`, and `llama-4-maverick`, routed through `https://api.zhizengzeng.com/v1`. These are external gateway dependencies. **Never assume an ID is still routed to the same backend:** `scripts/check_models.py` snapshots `/v1/models` immediately before each frozen run, and the experiment records both requested and returned IDs.

## Frozen experiment matrix

- **Data:** exact upstream ImperfectiveNLI artifact, 400 examples, 100/group, pair-validated A↔C and B↔D.
- **Primary prompt:** `neutral`; it does **not** teach the telic/atelic rule.
- **Prompt robustness:** fixed 120-example balanced subset using `strict_logic`, `definition_aware`, and a reversed label-order neutral condition.
- **Single pass:** temperature 0, structured `P(True), P(False), P(Unknown)`.
- **Repeated sampling:** temperature 0.7, `K=5` under the neutral prompt.
- **Verifier cache:** one independent aspect-sensitive prediction for every model/item, used to simulate RQ3 selective recheck policies without result-dependent API calling.
- **RQ1:** Acc A–D, TBR, ΔAA, SUR, TOR@0.80, ADG, Brier, NLL, top-label ECE and classwise ECE.
- **RQ2:** `1-maxprob`, predictive entropy, sampling variation ratio/entropy, error AUROC/AUPRC, paired A→C/B→D probability updates, prompt/order flip rates and JSD.
- **RQ3:** risk–coverage, AURC/E-AURC, risk at fixed coverage, coverage at target risk, TBR, Group-C coverage, Group-D coverage/retention, selective verifier cost.
- **Statistics:** 10,000 verb-cluster bootstrap resamples, 95% CIs, paired contrasts, Holm correction, and verb-disjoint threshold tuning only if optimization is required.

Planned main-study budget before retries is **15,800 API calls**, plus a 100-call cross-model smoke test. Token/cost reporting comes from the gateway's actual usage metadata when available rather than a stale price assumption.

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

The run script stops after a balanced cross-model smoke test and requires typing `RUN` before paid full calls. The analysis script begins with hard audit gates; a failed run is not silently converted into a paper table.

## Data provenance

`data/MANIFEST.json` freezes the upstream repository, source path, exact Git blob SHA-1, expected byte size, expected example count, and reported CC BY-NC 4.0 license. `scripts/fetch_imperfective_nli.py` downloads that artifact; `scripts/validate_dataset.py` checks canonical IDs, A/B/C/D counts and labels, required fields, and A↔C / B↔D pairing before writing a local SHA-256 manifest. The dataset remains a third-party research artifact and is not re-licensed under the software license of this repository.

## Reproducibility guarantees

Every frozen run stores a manifest with dataset/config/model/prompt hashes, selected IDs, git commit, platform and decoding mode. Every API record stores model requested/returned, prompt condition/hash, label order, timestamp, latency, usage, request ID, raw response, parsed response, probability-normalization delta and argmax consistency. Runs are resumable by `(example_id, repeat)`. `scripts/audit_run.py` checks duplicate/missing records, API/parse failures, sampling completeness, prompt mixing, model-ID drift and malformed confidence outputs before analysis.

Result figures are generated directly from processed CSVs as **PDF and SVG**. Conceptual diagrams are editable **TikZ**, including the semantic-vs-predictive uncertainty figure and the paired A→C / B→D semantic-update figure.

## Repository map

- `src/ullm/` — API client, prompt registry, parsing, metrics, runner
- `configs/` — model panel, experiment settings, pre-registered hypotheses
- `data/` — provenance manifests + exact-source downloader/validator
- `docs/` — research plan, analysis plan, experiment protocol, reproducibility checklist
- `paper/` — expanded AAAI-2027-style provisional IASEAI manuscript, editable TikZ, peer-reviewed references
- `scripts/` — preflight, frozen execution, hard run audit, RQ analyses, vector result figures
- `results/` — raw/processed outputs; large raw responses stay untracked by Git

## Status

**Stage 2 / frozen-design hardening is active:** neutral primary protocol, current five-family panel, exact data-integrity checks, paired analyses, calibration/ranking/selective-control pipeline, prompt/order robustness, cached verifier policies, resumable frozen-run scripts, audit gates, stronger vector figures, and an expanded 10-page-ready manuscript are in the repository. **Empirical Results remain intentionally TBD** until paid API calls are run from a machine with `ZZZ_API_KEY` and pass the audit gates.
