# ULLM progress ledger

This file is the human-readable project ledger for **The Imperfective Uncertainty in Large Language Models**. Git history remains the authoritative machine record; this ledger explains what each research/engineering phase accomplished and what remains intentionally blocked.

## 2026-09-03 — Pre-API research and engineering freeze

### Scientific design locked

- Paper title fixed as **The Imperfective Uncertainty in Large Language Models**.
- Exactly three research questions retained: uncertainty recognition (RQ1), uncertainty faithfulness (RQ2), and uncertainty-aware control (RQ3).
- Primary condition frozen to the `neutral` NLI prompt so the main result cannot be explained by explicitly teaching aspectual semantics.
- `strict_logic` and `definition_aware` retained only as fixed robustness interventions.
- Reversed label order retained as an output-format/order sensitivity audit.
- K=5 sampling at temperature 0.7 retained as the primary repeated-sampling uncertainty condition.
- One independent `verifier` prediction per model/item retained for counterfactual RQ3 selective-recheck analysis.
- Main-study budget frozen at **15,800 chat-completion calls before retries**, plus a separate 100-call smoke test.
- Compact RQ3 operating point frozen at `1-maxprob >= 0.20`; full threshold sweeps remain primary evidence.
- 10,000 verb-cluster bootstrap resamples, 95% intervals, Holm correction, and tie-aware selective risk retained.

### Dataset/provenance hardening

- ImperfectiveNLI is treated as third-party research data and remains outside the repository's MIT software license.
- Source is pinned to immutable upstream commit `8845a732d04a0b49e154fbf0db334d48d895b11f` rather than the mutable `main` branch.
- Expected upstream Git blob is frozen as `e20112c9de1f8c8ab27a8e2b969699b23dcdb186` with expected byte count 100970 and 400 examples.
- Dataset validator checks canonical IDs, required fields, exact A/B/C/D counts and labels, and A↔C / B↔D lexical pairing.
- Local download produces a SHA-256 provenance manifest that is required by preflight.
- `scripts/preflight.py` now cross-checks committed provenance, immutable source commit/blob, local byte count, local SHA-256, validator manifest, exact 400-item count, and the frozen 15,800-call budget.
- `.gitignore` explicitly blocks accidental commits of the downloaded benchmark, local provenance/validation manifests, raw/processed result trees, empirical figures, and local evidence snapshots.
- At the time of provenance review, the upstream GitHub repository exposed no root `LICENSE` file; the project therefore does not infer broader repository rights and records the dataset terms as reported by the source paper/release.

### Runner/reproducibility hardening

- Every live run stores dataset/config/model/prompt hashes, exact selected IDs, model panel, decoding settings, maximum tokens, label order, git revision, Python/platform metadata, and execution mode.
- Every response stores requested/returned model IDs, exact message hash, requested seed/max tokens, timestamps, latency, usage metadata, request ID, raw provider response, parsed output, and parser diagnostics.
- Resume safety rejects manifest drift and can atomically replace failed request/parse rows without duplicate keys.
- `--dry-run` constructs the exact request-hash plan without creating an API client or requiring `ZZZ_API_KEY`.
- Dry-run manifests are marked `execution_mode=dry_run`, preventing them from being resumed as live paid runs.
- `scripts/audit_request_plan.py` verifies complete model/example/repeat coverage and checks prompt/temperature/token/label-order consistency without storing raw benchmark text in the request-plan artifact.
- `scripts/offline_rehearsal.py` rehearses and audits all six main-study stages, totaling exactly 15,800 planned requests with **zero provider calls**.
- `scripts/environment_snapshot.py` records Git revision/cleanliness, Python/platform state, `pip freeze`, and hashes of scientific inputs while recording only a boolean for API-key presence, never the credential value.
- `scripts/checksum_run.py` creates an external SHA-256 evidence manifest for every file in a completed raw run directory so post-run backups can be integrity checked.
- `requirements-frozen.txt` records the exact tested Python 3.11 dependency environment intended for later frozen paid execution; compatibility CI still exercises supported ranges.

### Analysis pipeline complete before results

- Deterministic group metrics and paper-specific SUR/TOR/ADG diagnostics implemented.
- Brier, NLL, top-label ECE, Unknown-class ECE and classwise calibration implemented.
- Four black-box failure-ranking signals implemented: `1-maxprob`, predictive entropy, sampling variation ratio, and sampling label entropy.
- Error AUROC/AUPRC, AURC/E-AURC, threshold-realizable coverage, and tie-aware risk computation implemented.
- A→C / B→D paired semantic-update analyses and label-transition matrices implemented.
- Prompt and label-order robustness analyses implemented, including label flips and Jensen–Shannon divergence.
- Cached-verifier policy analysis implemented with Group-C TBR, Group-D retention, recheck rate, and token overhead.
- Publication result figures are generated as vector PDF/SVG.
- Manuscript result tables are generated from audited CSV artifacts rather than manually copied numbers.
- Synthetic end-to-end pipeline smoke test exists only for plumbing validation and is explicitly excluded from scientific evidence.
- Dedicated unit tests now cover zero-API request-plan construction and ensure dry/live execution mode is resume-critical.

### Manuscript/artifact pipeline

- Working manuscript expanded to a nine-page provisional AAAI-2027-style source before empirical results.
- All empirical result cells and claims remain intentionally `TBD`.
- Editable TikZ concept, paired-semantics, pipeline, and results-placeholder figures are included.
- Citation-key and LaTeX log-quality gates are automated.
- GitHub Actions builds the manuscript and separately packages an Overleaf-ready source archive.
- The detailed IASEAI'27 formatting guide is still pending; the AAAI style remains a provisional working layout and must be replaced if the official 2027 instructions differ.

### CI state at this phase

- Core Python CI runs on 3.10, 3.11, and 3.12.
- Citation integrity, project consistency, unit tests, and zero-API synthetic end-to-end analysis are automated.
- `scripts/validate_project.py` now also guards immutable dataset provenance fields, the public/private artifact boundary, frozen dependency pins, progress/runbook presence, the zero-API runner path, and the 15,800-call budget.
- The dedicated **Dataset and offline rehearsal** workflow fetches the immutable benchmark, validates its provenance/structure, runs preflight, rehearses all 15,800 planned main-study requests without an API key, records a credential-safe CI environment snapshot, and uploads provenance/rehearsal evidence.
- **First complete Dataset and offline rehearsal workflow run passed successfully on 2026-09-03.** This is a software/protocol readiness result only; it is not an empirical LLM result.
- Manuscript compilation, citation-key integrity, LaTeX log quality, PDF artifact upload and Overleaf source packaging are automated separately.

### Project coordination / progress recording

- `docs/PROGRESS_LOG.md` is the persistent human-readable ledger.
- `docs/LOCAL_RUNBOOK.md` is the exact handoff for later local credential-gated execution.
- `docs/REPRODUCIBILITY.md` documents the evidence chain from immutable source/protocol through live provider records to derived tables/figures.
- GitHub issue #1 has been rewritten as a phase-based execution board: Phase 0 zero-API work is checked complete; live catalogue/smoke, paid experiment, empirical analysis, manuscript evidence pass, and final IASEAI submission gates remain open.
- README, data documentation, provenance notes and experiment/paper descriptions are synchronized with the immutable source and offline rehearsal design.

## 2026-09-03 — Experiment-Ready v1 checkpoint

- Exact green pre-paid baseline: `8b4ccab4509e42da7d315e1161085e5a99591181`.
- Stable branch created: `experiment-ready-v1`.
- CI run `33707498253` completed successfully for that exact commit.
- Python 3.10, 3.11, and 3.12 matrix jobs passed.
- Python 3.11 additionally passed unit tests, POSIX frozen-runner syntax, PowerShell frozen-runner syntax, and the zero-API synthetic end-to-end analysis smoke.
- This checkpoint is the recommended local starting point for the credential-gated execution phase.
- No empirical LLM result was generated by this checkpoint; all manuscript result values remain `TBD`.
- Any later scientific-setting change must create a new protocol/checkpoint rather than silently moving `experiment-ready-v1`.

## 2026-09-03 — V1→V4 compatibility sequence and final smoke gate

- V1 smoke used a 220-token completion ceiling. The 100-call smoke had zero request failures but 12/20 DeepSeek parse failures and 6/20 Gemini parse failures; preserved responses showed completion-budget exhaustion.
- V2 raised only the ceiling to 1024. Gemini reached 20/20 valid outputs and DeepSeek improved to 17/20, with the remaining three failures all ending at `finish_reason=length`.
- V3 raised only the ceiling to 4096 and added a hard completion-budget audit. DeepSeek improved to 18/20, but `A_015` and `D_007` still exhausted the full 4096-token ceiling.
- V4 froze a DeepSeek-only request override that disables gateway thinking mode while retaining the 4096 ceiling and all scientific settings. The runner now records model-specific request overrides in manifests/request plans/raw rows, treats them as resume-critical, and audits them independently.
- Exact V4 frozen branch head: `213778b59f3838c4bbee51c963c81ee1559ed0b1` on `experiment-ready-v4`.
- V4 CI run `33722960766` completed successfully.
- The complete 15,800-request offline plan was reconstructed and audited at the V4 commit with zero provider calls.
- The live catalogue snapshot again exposed all five predeclared routing IDs within 842 entries with catalogue SHA-256 `904b9ec7a7b04d7e9e709558d58d2cfbffda0ebf9cdc1390b0543a6fd7b7157a`.
- The fresh V4 100-call balanced deterministic-neutral smoke passed for all five models at 20/20 valid records per route.
- The completion-budget audit checked all 100 preserved responses and found `exhausted=0`.
- The model-control audit checked all 100 rows and found `override_mismatches=0` and `reasoning_violations=0`.
- The V4 smoke run was sealed with a SHA-256 checksum manifest.
- All smoke statistics remain non-evidentiary engineering diagnostics. No smoke value is used as RQ1/RQ2/RQ3 evidence.
- V4 is therefore the compatibility-ready raw-execution baseline, subject to one final local worktree-cleanliness check before authorizing the 15,800-call main study.

## Remaining live execution sequence

The following steps remain intentionally gated:

1. Verify the local V4 scientific worktree is clean before the main paid run.
2. Explicitly authorize the 15,800-call frozen main study.
3. Audit each stage for request/parse/schema/model-control/completion-budget failures and retry only audited failed rows without changing scientific settings.
4. Create checksum/evidence backups for all six real raw runs.
5. Run the frozen analyses against real provider outputs.
6. Replace manuscript `TBD` cells/plots only through the automated table/figure pipeline.
7. Write the empirical Results, Discussion and final Conclusion from audited outputs only.
8. Perform final reviewer-style statistical, artifact, anonymity and IASEAI-format audits.

## Scientific red lines

- Do not insert synthetic values into the paper.
- Do not change the primary prompt/model panel/thresholds after seeing main-study results without creating and documenting a new protocol version.
- Do not silently drop failed calls or incomplete K=5 sampling items.
- Do not choose a prompt or uncertainty metric because it produces the most favorable result.
- Do not describe gateway aliases as immutable vendor checkpoints.
- Do not commit API keys or downloaded third-party benchmark data.
- Do not manually transcribe manuscript result values when a generated table/figure path exists.
- Treat a green offline rehearsal or smoke as engineering/protocol evidence, never as evidence about model behavior.
