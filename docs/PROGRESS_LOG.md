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

## Intentionally blocked until local API execution

The following steps cannot be scientifically completed without the user's local gateway credential and therefore remain open by design:

1. Snapshot the live `/v1/models` catalogue and verify all five configured routing IDs.
2. Authorize and run the 100-call paid smoke test.
3. Audit smoke outputs for routing, schema, parsing, usage metadata and response quality.
4. Explicitly authorize the 15,800-call frozen main study.
5. Retry only audited failed requests, without altering scientific settings.
6. Create checksum/evidence backups for the real raw runs.
7. Run the frozen analyses against real provider outputs.
8. Replace manuscript `TBD` cells/plots through the automated table/figure pipeline.
9. Write the empirical Results, Discussion and final Conclusion from audited outputs only.
10. Perform final reviewer-style statistical, artifact, anonymity and IASEAI-format audits.

## Scientific red lines

- Do not insert synthetic values into the paper.
- Do not change the primary prompt/model panel/thresholds after seeing main-study results without creating and documenting a new protocol version.
- Do not silently drop failed calls or incomplete K=5 sampling items.
- Do not choose a prompt or uncertainty metric because it produces the most favorable result.
- Do not describe gateway aliases as immutable vendor checkpoints.
- Do not commit API keys or downloaded third-party benchmark data.
- Do not manually transcribe manuscript result values when a generated table/figure path exists.
- Treat a green offline rehearsal as engineering/protocol evidence, never as evidence about model behavior.
