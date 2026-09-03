# Reproducibility and Audit Protocol

This project separates three evidence layers: **source/protocol evidence**, **provider execution evidence**, and **derived analysis evidence**. A paper claim is acceptable only when it can be traced through those layers without manually rewriting values.

## 1. Source and protocol identity

Before any paid request:

- ImperfectiveNLI is fetched from immutable upstream commit `8845a732d04a0b49e154fbf0db334d48d895b11f`.
- The downloader verifies Git blob `e20112c9de1f8c8ab27a8e2b969699b23dcdb186`, `100970` bytes, 400 examples, and required fields.
- `data/MANIFEST.local.json` records the local SHA-256 and immutable source provenance.
- `scripts/validate_dataset.py` checks canonical IDs, group/label counts, and A↔C / B↔D pair structure and writes `data/dataset_manifest.json`.
- `scripts/preflight.py` requires agreement among the committed manifest, downloaded file, local provenance manifest, and validator manifest.
- The exact model panel, experiment settings and directional hypotheses live in committed YAML files.
- `scripts/validate_project.py` guards the scientific invariants, 15,800-call main-study budget, repository safety ignores, frozen dependency snapshot, and zero-API rehearsal path.

## 2. Tested software environment

Two dependency views are retained:

- `requirements.txt` — supported version ranges exercised by broad CI;
- `requirements-frozen.txt` — exact Python package versions from the tested Python 3.11 environment intended for the frozen paid execution.

Run `python scripts/environment_snapshot.py` before the live experiment. It records Git revision/cleanliness, Python/platform metadata, `pip freeze`, and SHA-256 values for scientific configs, the local dataset and manuscript. It records only whether `ZZZ_API_KEY` is present; the credential itself is never written.

## 3. Full zero-API request rehearsal

The actual runner exposes `--dry-run`. In that mode it constructs the same system/user messages and seeds used by a live run, but writes only request metadata/hashes and never creates `OpenAICompatibleClient`.

`scripts/offline_rehearsal.py` rehearses all frozen main-study stages:

| Stage | Calls |
|---|---:|
| Neutral deterministic | 2,000 |
| Neutral K=5 sampling | 10,000 |
| Strict-logic robustness | 600 |
| Definition-aware robustness | 600 |
| Reversed-label-order robustness | 600 |
| Verifier cache | 2,000 |
| **Total** | **15,800** |

`scripts/audit_request_plan.py` checks exact model/example/repeat coverage; prompt, message and label-order hashes; seeds; temperature; maximum tokens; and duplicate keys. It also rejects request-plan artifacts that duplicate benchmark text or provider output fields.

The GitHub Actions workflow **Dataset and offline rehearsal** performs the immutable fetch, validator, preflight, and full 15,800-request rehearsal with no API secret. This provides an independent Linux/Python 3.11 pre-execution gate.

## 4. Live gateway identity

Immediately before paid execution, `scripts/check_models.py` snapshots the live gateway catalogue. Because the study uses an OpenAI-compatible third-party gateway, configured strings are treated as routing identifiers rather than immutable vendor checkpoint identities.

Each live response stores both requested and returned model identifiers, request/timestamp metadata and raw response payload. Claims are therefore scoped to the routed endpoints actually observed on the execution date.

## 5. Live run manifest

Every frozen live run records at minimum:

- `execution_mode=live`;
- dataset SHA-256 and exact selected example IDs;
- config/model file SHA-256 values;
- prompt type and prompt SHA-256;
- label order;
- mode, temperature, samples/item and maximum tokens;
- exact selected model IDs;
- Git commit;
- Python version and platform.

Dry-run manifests use `execution_mode=dry_run`. Execution mode is resume-critical, preventing an offline plan directory from being turned into a live experiment by `--resume`.

## 6. Per-call evidence

Every live API record stores:

- model requested and model returned;
- example payload and repeat index;
- prompt type/hash and exact message hash;
- requested temperature, maximum tokens and seed;
- UTC timestamp;
- latency and request ID when available;
- provider usage metadata when available;
- raw provider response and raw text;
- parsed three-way prediction;
- parser/request errors;
- probability-normalization and label/argmax diagnostics.

The study requests only a one-sentence rationale. It does not ask providers for hidden chain-of-thought and does not represent short rationales as privileged internal reasoning.

## 7. Resume and failure policy

Resume is keyed by `(example_id, repeat)` per model output file. A compatible resume requires the frozen manifest fields to match. `--resume --retry-failures` atomically removes failed request/parse rows before replacing them, preventing duplicate scientific keys.

Failed or incomplete calls must never be silently discarded during analysis. K=5 sampling items must have all five audited repeats or fail the corresponding audit.

## 8. Hard run audit

`scripts/audit_run.py` checks:

- malformed JSONL;
- duplicate/missing `(example_id, repeat)` records;
- exact selected-ID and repeat-index coverage;
- expected row count;
- request/parse failures;
- invalid labels/probabilities;
- label/argmax inconsistency;
- prompt/hash/label-order drift;
- decoding-setting drift;
- model-file coverage;
- current dataset/config/model hash agreement.

A failed audit blocks downstream analysis.

## 9. Analysis reproducibility

The analysis code implements the manuscript protocol before real results exist:

- original group accuracy, TBR and ΔAA;
- SUR, TOR@0.80 and ADG;
- Brier, NLL, top-label ECE and classwise/Unknown ECE;
- four black-box failure-ranking signals;
- error AUROC/AUPRC and tie-aware AURC/E-AURC;
- threshold-realizable coverage/risk operating points;
- paired A→C and B→D probability updates/transitions;
- prompt and label-order flip/JSD analyses;
- cached-verifier selective policies and operational token cost;
- 10,000 verb-cluster bootstrap intervals and Holm correction.

`scripts/synthetic_pipeline_smoke.py` exercises this pipeline with synthetic data purely as a software integration test. Synthetic values are never scientific evidence.

## 10. Derived artifact chain

The intended evidence flow is:

`raw JSONL → manifest audit → processed CSV → vector PDF/SVG figures + generated LaTeX tables → manuscript`

`paper/generated/rq1_table.tex`, `rq2_table.tex` and `rq3_table.tex` are produced by code after audited results. Before execution they contain explicit `TBD` placeholders. Final empirical numbers should not be hand-copied from a terminal when a generated path exists.

## 11. Raw evidence preservation

Immediately after a paid stage passes audit, preserve the raw directory before interpretation. `scripts/checksum_run.py results/raw/<run-id>` creates an external SHA-256 manifest of every file in that run directory. The checksum manifest is deliberately stored outside the authenticated directory.

The raw evidence backup should include run manifests, JSONL outputs, live model-catalogue snapshot, local dataset manifest, exact Git revision and a credential-safe environment snapshot. Provider billing/usage exports can be preserved separately for cost reconciliation if available.

## 12. Publication and data boundary

The downloaded third-party dataset is not committed under this repository's MIT software license. Local dataset files/manifests, raw API responses, processed outputs, empirical figures and local environment/rehearsal artifacts are ignored by Git by default. Publication/release of any of those artifacts is a separate deliberate step after license/privacy/provider-policy review.

Conceptual figures are editable TikZ. Empirical figures are generated as vector PDF + SVG. The manuscript build, citation-key integrity, and LaTeX layout/log quality are checked in CI.

## 13. Final traceability rule

Every final empirical paper statement must be answerable with:

1. which committed protocol/config generated it;
2. which exact benchmark bytes and gateway route were used;
3. which raw records support it;
4. which audit passed;
5. which analysis artifact produced the reported number/plot/table.

If that chain cannot be reconstructed, the claim is not submission-ready.
