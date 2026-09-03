# The Imperfective Uncertainty in Large Language Models

Research artifact for an IASEAI'27 main-conference paper. The project builds on the ACL 2026 paper **“The Imperfective Paradox in Large Language Models”** but asks a different question: **when event completion is semantically underdetermined, do LLMs represent the correct uncertainty relation, is that uncertainty faithful to their errors, and can it control risk?**

> **Current phase (2026-09-03): zero-API preparation is operational.** The exact benchmark provenance, frozen protocol, request construction, full 15,800-call main-study plan, analysis stack, manuscript generation, and CI gates can all be exercised without a model API key. Real empirical results remain intentionally `TBD`.

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

## Reproducible environments

`requirements.txt` defines supported dependency ranges used by broad CI. `requirements-frozen.txt` records the exact Python package versions from the tested Python 3.11 environment and is the preferred environment for the later frozen paid execution.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-frozen.txt
python -m pip check
```

Core CI additionally exercises Python 3.10, 3.11, and 3.12 against the compatibility ranges.

## Prepare the exact benchmark locally

The dataset is third-party research data and is intentionally **not committed** into this repository. The fetcher is pinned to upstream commit `8845a732d04a0b49e154fbf0db334d48d895b11f`, not a mutable branch, and verifies Git blob `e20112c9de1f8c8ab27a8e2b969699b23dcdb186`, byte count `100970`, schema, and 400-example count.

```bash
python scripts/fetch_imperfective_nli.py
python scripts/validate_dataset.py data/imperfectiveNLI.json
python scripts/preflight.py
```

The fetcher writes `data/MANIFEST.local.json`; the validator writes `data/dataset_manifest.json`; preflight requires agreement among the committed provenance record, the downloaded bytes, the local SHA-256, and the validator manifest. `data/THIRD_PARTY_DATA.md` documents the licensing boundary. The upstream repository currently exposes no root `LICENSE` file, so this project does not infer broader rights from the repository itself and records the dataset terms as reported by the source paper/release.

## Complete zero-API rehearsal

The live runner supports `--dry-run`: it writes a frozen manifest and exact request-hash plan **without constructing an API client**. `scripts/audit_request_plan.py` verifies model/example/repeat coverage, seeds, decoding settings, prompt hashes, label order, message hashes, and ensures the request-plan artifact does not duplicate benchmark prompt text.

Run the complete study rehearsal with:

```bash
python scripts/offline_rehearsal.py
```

That command constructs and audits every planned main-study stage with no credential and no provider call:

| Stage | Planned calls |
|---|---:|
| Neutral deterministic | 2,000 |
| Neutral K=5 sampling | 10,000 |
| Strict-logic robustness | 600 |
| Definition-aware robustness | 600 |
| Reversed-label-order robustness | 600 |
| Verifier cache | 2,000 |
| **Total** | **15,800** |

The dedicated GitHub Actions workflow **Dataset and offline rehearsal** independently fetches the immutable benchmark and performs the same complete 15,800-request rehearsal. Its first full run passed successfully. No API secret is configured in that workflow.

## Zero-API analysis testing

In addition to the exact request-plan rehearsal, `scripts/synthetic_pipeline_smoke.py` creates a temporary synthetic A/B/C/D fixture and exercises manifest-aware audits, deterministic summaries, clustered bootstrap code, repeated-sampling analysis, all four uncertainty-ranking signals, paired analysis, selective prediction, verifier alignment, vector figure generation, and LaTeX table generation.

```bash
python scripts/validate_project.py
python scripts/synthetic_pipeline_smoke.py
pytest -q
```

**Synthetic outputs are never paper evidence.** They are plumbing tests only.

## Credential-safe environment evidence

Before a later paid run, record the local execution environment without recording the API key itself:

```bash
python scripts/environment_snapshot.py
```

The generated ignored JSON records Git revision/cleanliness, Python/platform information, `pip freeze`, hashes of the frozen configs, dataset and manuscript, and only a boolean stating whether `ZZZ_API_KEY` is present. The credential value is never written.

## Paid execution has two explicit human gates

Set `ZZZ_API_KEY` in your local shell **only after all offline gates pass**; never commit it. Then on Windows:

```powershell
.\scripts\run_frozen.ps1
```

or on POSIX:

```bash
bash scripts/run_frozen.sh
```

The canonical script first performs preflight and a live model-catalogue check. **No chat-completion call is made until you type `SMOKE`**, which authorizes the 100-call cross-model smoke test. The smoke outputs must then pass the hard audit and be inspected. Only after that do you type **`RUN`** to authorize the 15,800 main-study calls before retries.

Every paid stage is audited immediately. Compatible interrupted runs resume safely; request/parse failures can be replaced with `--resume --retry-failures` without creating duplicate `(example_id, repeat)` keys. A dry-run manifest cannot be resumed as a live run because `execution_mode` is a resume-critical manifest field.

For the exact local sequence, use `docs/LOCAL_RUNBOOK.md` rather than improvising the experiment.

## Audit-first analysis and manuscript generation

After all frozen stages pass their manifests, the analysis pipeline generates:

- RQ1 deterministic summaries and 10,000-replicate verb-cluster bootstrap intervals;
- RQ2 sampling statistics and unified four-signal failure ranking;
- paired A→C / B→D probability updates and transition matrices;
- prompt and label-order robustness analyses;
- tie-aware RQ3 risk–coverage and cached-verifier policies;
- publication vector figures in PDF + SVG; and
- `paper/generated/rq1_table.tex`, `rq2_table.tex`, and `rq3_table.tex` directly from processed CSVs.

A manuscript number should never be copied manually from console output. The committed generated tables contain only **TBD placeholders** before the frozen run.

After a real run, create an external checksum evidence manifest before moving/copying raw artifacts:

```bash
python scripts/checksum_run.py results/raw/<run-id>
```

The checksum file is written outside the authenticated run directory so it cannot recursively authenticate itself.

## Data provenance and publication boundary

`data/MANIFEST.json` freezes the upstream repository, immutable source commit, source path, exact Git blob SHA-1, expected byte size, expected example count, and the license reported by the source paper/release. `scripts/fetch_imperfective_nli.py` retrieves exactly that immutable artifact; `scripts/validate_dataset.py` checks canonical IDs, A/B/C/D counts and labels, required fields, and A↔C / B↔D pairing.

Downloaded benchmark data, local manifests, raw API outputs, processed outputs, local environment snapshots, and local rehearsal artifacts are ignored by Git. Only code, configs, documentation, manuscript sources, and pre-run placeholders belong in the public source tree unless an explicit release decision is made later.

## Reproducibility guarantees

Every frozen live run stores a manifest with dataset/config/model/prompt hashes, exact selected IDs, git commit, platform, decoding mode, maximum output tokens, label order, and `execution_mode=live`. Every API record stores model requested/returned, exact message hash, prompt condition/hash, requested seed/max tokens, timestamp, latency, usage, request ID, raw response, parsed response, probability-normalization delta and argmax consistency.

`scripts/audit_run.py` checks malformed JSONL, duplicate or missing records, exact ID coverage, repeat-index sets, request/parse failures, prompt/hash/order consistency, decoding settings, requested model coverage, current dataset/config hashes, and invalid label/probability contracts. A failed audit stops downstream analysis.

## Repository map

- `src/ullm/` — API client, prompt registry, parsing, metrics, statistics, manifest-safe live/dry runner
- `configs/` — frozen model panel, experiment settings, preregistered hypotheses
- `data/` — third-party provenance manifests + immutable-source downloader/validator
- `docs/` — research/analysis/experiment plans, progress ledger, reproducibility, local runbook, submission checklist
- `paper/` — provisional AAAI-2027-style working manuscript, editable TikZ, peer-reviewed references, generated result-table hooks
- `scripts/` — project/preflight validators, full offline rehearsal, environment/run evidence tools, frozen execution, hard audits, analyses, vector figures, LaTeX table generation
- `tests/` — parsing, metrics, clustered inference, selective ties, resume safety, and zero-API request-plan tests
- `results/` — ignored raw/processed/figure outputs generated during execution

## Progress record

`docs/PROGRESS_LOG.md` is the permanent human-readable research/engineering ledger. Git history is the authoritative machine record. The progress log separates completed zero-API work from the deliberately blocked live-gateway and empirical stages so we never confuse engineering readiness with scientific results.

## Status

**Zero-API preparation is complete enough for a frozen rehearsal and is continuously checked by GitHub Actions.** The immutable dataset fetch/validation workflow and full 15,800-request offline rehearsal have passed in CI; core project validation, citation integrity, unit tests, synthetic end-to-end analysis, manuscript compilation/log checks, and Overleaf packaging are automated. The exact local paid-run procedure is recorded in `docs/LOCAL_RUNBOOK.md`.

**Still intentionally blocked:** live gateway catalogue verification, the 100-call paid smoke, the 15,800-call main study, real result analysis, and replacement of manuscript `TBD` values. No empirical result or model ranking is claimed before those audited artifacts exist.
