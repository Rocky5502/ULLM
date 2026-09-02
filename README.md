# The Imperfective Uncertainty in Large Language Models

Research artifact for an IASEAI'27 main-conference paper. The project builds on the ACL 2026 paper **“The Imperfective Paradox in Large Language Models”** but asks a different question: **when event completion is semantically underdetermined, do LLMs represent the correct uncertainty relation, is that uncertainty faithful to their errors, and can it control risk?**

## Locked scientific thesis

In the critical ImperfectiveNLI Group C, the *world outcome* is unknown but the *NLI relation* is determinately `Unknown`. An ideal model should therefore be **confidently uncertain about the event** (`P(Unknown)` high), not confidently complete it (`P(True)` high) and not diffusely guess among labels. This separates semantic uncertainty from predictive uncertainty.

## Exactly three RQs

1. **RQ1 — Uncertainty Recognition:** Do frontier API LLMs recognize semantic under-specification and remain calibrated across Groups A–D?
2. **RQ2 — Uncertainty Faithfulness:** Which black-box signal—verbalized probabilities or repeated-sampling disagreement—best identifies aspectual errors and teleological overconfidence?
3. **RQ3 — Uncertainty-Aware Control:** Can selective defer/recheck lower completion errors at useful coverage without degrading valid atelic entailments?

## Frozen gateway panel

Primary panel: `gpt-5.6-sol`, `claude-sonnet-5`, `deepseek-v4-pro`, `qwen3.8-max`, and `gemini-3.7-flash`, routed through the configured OpenAI-compatible gateway. These are **gateway routing identifiers**, not claims about immutable vendor-direct checkpoints. `scripts/check_models.py` snapshots the live `/v1/models` catalogue immediately before execution, while each response records both requested and returned model identifiers. Scientific claims attach to the routed endpoints actually observed on the recorded run date.

## Frozen experiment matrix

- **Data:** exact upstream ImperfectiveNLI artifact, 400 examples, 100/group, pair-validated A↔C and B↔D.
- **Primary prompt:** `neutral`; it does **not** teach the telic/atelic rule.
- **Prompt robustness:** fixed seed-42 A/B/C/D-balanced 120-example subset using `strict_logic`, `definition_aware`, and a reversed-label-order neutral condition.
- **Single pass:** temperature 0, structured `P(True), P(False), P(Unknown)`.
- **Repeated sampling:** temperature 0.7, `K=5` under the neutral prompt.
- **Verifier cache:** one independent aspect-sensitive prediction for every model/item, used to simulate RQ3 selective recheck policies without result-dependent API calling.
- **RQ1:** Acc A–D, TBR, ΔAA, SUR, TOR@0.80, ADG, Brier, NLL, top-label ECE and classwise ECE.
- **RQ2:** `1-maxprob`, predictive entropy, sampling variation ratio/entropy, error AUROC/AUPRC, AURC/E-AURC, paired A→C/B→D probability updates, prompt/order flip rates and JSD.
- **RQ3:** tie-aware risk–coverage, threshold-realizable fixed-coverage points, coverage at target risk, TBR, Group-C coverage, Group-D coverage/retention, and selective-verifier operational cost.
- **Statistics:** 10,000 verb-cluster bootstrap resamples, 95% CIs, paired contrasts, Holm correction, and verb-disjoint threshold tuning only if optimization is required.

Planned main-study budget before retries is **15,800 chat-completion calls**, plus a **100-call smoke test**. The compact RQ3 manuscript operating point (`1-maxprob >= 0.20`) is frozen before results; the full threshold sweep remains primary evidence. Token/cost reporting comes from gateway usage metadata when available rather than a stale price assumption.

## Zero-API validation first

Before spending anything, CI and local validation exercise the non-provider-dependent pipeline:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate_project.py
python scripts/synthetic_pipeline_smoke.py
pytest -q
```

`synthetic_pipeline_smoke.py` creates a temporary synthetic A/B/C/D fixture and exercises manifest-aware audits, deterministic summaries, clustered bootstrap code, repeated-sampling analysis, all four uncertainty-ranking signals, paired analysis, selective prediction, verifier alignment, vector figure generation, and LaTeX table generation. **Synthetic outputs are never used as paper evidence.**

## Prepare the exact benchmark locally

```bash
python scripts/fetch_imperfective_nli.py
python scripts/preflight.py
```

The fetcher verifies the exact upstream Git-blob identity and writes `data/MANIFEST.local.json`; preflight then checks project consistency, dataset structure/provenance, the frozen 15,800-call budget, and API-key presence.

## Paid execution has two explicit human gates

Set `ZZZ_API_KEY` in your local shell **only**; never commit it. Then on Windows:

```powershell
.\scripts\run_frozen.ps1
```

or on POSIX:

```bash
bash scripts/run_frozen.sh
```

The canonical script first performs preflight and a live model-catalogue check. **No chat-completion call is made until you type `SMOKE`**, which authorizes the 100-call cross-model smoke test. The smoke outputs must then pass the hard audit and are summarized for inspection. Only after that do you type **`RUN`** to authorize the remaining 15,800 main-study calls before retries.

Every paid stage is audited immediately. Compatible interrupted runs resume safely; request/parse failures can be replaced with `--resume --retry-failures` without creating duplicate `(example_id, repeat)` keys. An incompatible manifest causes the resume to stop rather than silently mixing experiments.

## Audit-first analysis and manuscript generation

After all frozen stages pass their manifests, the run script invokes the complete analysis pipeline automatically. It generates:

- RQ1 deterministic summaries and 10,000-replicate verb-cluster bootstrap intervals;
- RQ2 sampling statistics and unified four-signal failure ranking;
- paired A→C / B→D probability updates and transition matrices;
- prompt and label-order robustness analyses;
- tie-aware RQ3 risk–coverage and cached-verifier policies;
- publication vector figures in PDF + SVG; and
- `paper/generated/rq1_table.tex`, `rq2_table.tex`, and `rq3_table.tex` directly from processed CSVs.

A manuscript number should never be copied manually from console output. The committed generated tables contain only **TBD placeholders** before the frozen run.

## Data provenance

`data/MANIFEST.json` freezes the upstream repository, source path, exact Git blob SHA-1, expected byte size, expected example count, and reported CC BY-NC 4.0 license. `data/THIRD_PARTY_DATA.md` explicitly separates the benchmark's terms from this repository's software license. `scripts/fetch_imperfective_nli.py` downloads the exact artifact; `scripts/validate_dataset.py` checks canonical IDs, A/B/C/D counts and labels, required fields, and A↔C / B↔D pairing before a local SHA-256 provenance manifest is accepted.

## Reproducibility guarantees

Every frozen run stores a manifest with dataset/config/model/prompt hashes, exact selected IDs, git commit, platform, decoding mode, maximum output tokens, and label order. Every API record stores model requested/returned, exact message hash, prompt condition/hash, requested seed/max tokens, timestamp, latency, usage, request ID, raw response, parsed response, probability-normalization delta and argmax consistency.

`scripts/audit_run.py` checks malformed JSONL, duplicate or missing records, exact ID coverage, repeat-index sets, request/parse failures, prompt/hash/order consistency, decoding settings, requested model coverage, current dataset/config hashes, and invalid label/probability contracts. A failed audit stops downstream analysis.

## Repository map

- `src/ullm/` — API client, prompt registry, parsing, metrics, statistics, manifest-safe runner
- `configs/` — frozen model panel, experiment settings, preregistered hypotheses
- `data/` — third-party provenance manifests + exact-source downloader/validator
- `docs/` — research plan, analysis plan, experiment protocol, reproducibility/submission checklists
- `paper/` — provisional AAAI-2027-style working manuscript, editable TikZ, peer-reviewed references, generated result-table hooks
- `scripts/` — project validation, zero-API smoke, preflight, frozen execution, hard audits, RQ analyses, vector figures, LaTeX table generation
- `tests/` — unit tests for parsing, metrics, clustered inference, ties, and safe resume behavior
- `results/` — raw/processed outputs; large raw responses stay untracked by Git

## Status

**Pre-paid-run engineering hardening is in progress through GitHub CI:** the neutral primary protocol, current five-family gateway panel, exact data-integrity checks, manifest-safe resume behavior, paired analyses, calibration/ranking/selective-control pipeline, prompt/order robustness, cached verifier policies, audit gates, zero-API end-to-end smoke, generated manuscript tables, vector figures, and expanded manuscript are all present. **Empirical results remain intentionally TBD** until authorized API calls produce frozen artifacts that pass every audit gate.
