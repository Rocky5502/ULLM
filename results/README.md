# Results artifacts

Generated empirical outputs are **not committed by default**. This keeps the public source artifact small, avoids redistributing provider-returned text or third-party benchmark content, and prevents local or partial runs from being confused with the audited evidence behind the study.

## Directory roles

- `results/raw/<run_id>/` — one experimental stage: `manifest.json` plus one JSONL file per model/condition.
- `results/raw/<run_id>.checksums.json` — external SHA-256 evidence manifest generated after a stage passes its audit.
- `results/catalog/` — live gateway `/models` snapshots captured immediately before execution.
- `results/processed/` — audit reports, summaries, bootstrap outputs, ranking/paired/selective/verifier CSVs.
- `results/figures/` — generated empirical vector figures.

These generated trees are ignored by Git by default. Documentation or empty directory markers may remain tracked.

## Raw run manifest

Each live run manifest records the dataset hash and selected IDs, model/config hashes, routed model panel, prompt type/hash, label order, mode, temperature, K, maximum completion budget, model-specific request controls, Git revision, Python/platform metadata, and `execution_mode=live`.

Dry rehearsals use `execution_mode=dry_run` and produce an exact request plan instead of provider outputs. Dry and live manifests are intentionally incompatible for resume.

## Per-call evidence

A live record preserves the benchmark example, requested/returned model IDs, prompt/message hashes, seed and decoding controls, temperature/repeat, parsed prediction, probability vector, short rationale, raw provider response, usage metadata, latency, request ID, final HTTP status, and the number of HTTP attempts used.

Request or parse failures are retained until the explicit safe-retry path replaces only failed rows. Successful records are never selectively rerun to improve an observed result.

## Audit policy

`scripts/audit_run.py` checks record coverage, malformed JSONL, duplicate keys, missing repeats, request/parse failures, prompt/config/order drift, invalid probability normalization, missing short rationales, model-ID consistency, and decoding controls. `scripts/audit_completion_budget.py` separately rejects preserved responses that ended because the completion budget was exhausted, while `scripts/audit_model_controls.py` verifies the frozen model-specific controls.

Under adjudication **A1**, schema-valid disagreement between the model's explicit label and the argmax of its reported probability distribution is preserved as observed behavior. The strict audit remains the default; the frozen analysis path uses the explicit `--allow-argmax-inconsistency` policy and records those cases as decision/distribution consistency warnings rather than rewriting, deleting, or selectively retrying them. See `docs/CONTRACT_ADJUDICATION_A1.md`.

## Evidence sealing

After a real stage passes its scientific audits, create an external checksum manifest:

```bash
python scripts/checksum_run.py results/raw/<run-id>
```

The checksum record is written outside the authenticated run directory so it cannot recursively authenticate itself.

## Analysis flow

The canonical analysis stack produces deterministic summaries and verb-cluster confidence intervals, K=5 sampling uncertainty, four-signal failure ranking, A↔C and B↔D paired analyses, prompt/order robustness, tie-aware risk–coverage, cached-verifier control summaries, and vector figures.

The intended evidence flow is:

```text
raw records → hard audits → checksums → processed statistics → figures/tables → manuscript
```

Do not manually transcribe terminal output when a generated processed artifact can provide the value reproducibly.

## Publication boundary

See `docs/ARTIFACT_POLICY.md`. Raw provider output, downloaded benchmark bytes, and generated empirical files are not automatically public just because the source repository is public. Any release of empirical artifacts should be reviewed for benchmark licensing, provider terms, privacy/credential leakage, and consistency with the archival manuscript.
