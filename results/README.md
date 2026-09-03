# Results artifacts

Generated empirical outputs are intentionally not committed during the design/pre-API freeze. This prevents synthetic, partial, stale, or provider-sensitive files from being mistaken for the evidence behind the paper.

## Directory roles

- `results/raw/<run_id>/` — one immutable experimental stage: `manifest.json` plus one JSONL file per model/condition.
- `results/raw/<run_id>.checksums.json` — external SHA-256 evidence manifest generated after a PASS audit.
- `results/catalog/` — live gateway `/models` snapshots captured immediately before paid execution.
- `results/processed/` — audit reports, summaries, bootstrap outputs, ranking/paired/selective/verifier CSVs.
- `results/figures/` — generated empirical PDF/SVG figures.

All of these generated trees are ignored by Git by default. Empty `.gitkeep`/documentation files may remain tracked.

## Raw run manifest

Each live run manifest records the exact dataset SHA-256 and selected IDs, model/config hashes, model panel, prompt type/hash, label order, mode, temperature, K, maximum tokens, Git revision, Python/platform metadata, and `execution_mode=live`.

Dry rehearsals use `execution_mode=dry_run` and produce `request_plan.jsonl` instead of provider output files. Dry and live manifests are intentionally incompatible for resume.

## Per-call evidence

Each successful live record contains the benchmark example, requested/returned model IDs, prompt/message hashes, requested seed/max tokens, temperature/repeat, parsed probability prediction, one-sentence rationale, raw text/response, usage metadata, latency, request ID, final HTTP status and number of HTTP attempts used. Request/parse failures are retained until the explicit safe-retry path replaces them.

The hard run audit rejects missing/incomplete records, duplicate keys, request/parse errors, invalid probabilities, label/argmax inconsistency, probability sums more than 0.02 away from one, missing required short rationale, prompt/config/order drift, wrong repeat sets, non-live manifests, and successful records with non-200 final HTTP status.

## Evidence sealing

After each real stage passes `scripts/audit_run.py`, run:

```bash
python scripts/checksum_run.py results/raw/<run-id>
```

The canonical `run_frozen.ps1` / `run_frozen.sh` scripts do this automatically after every successful smoke/main-stage audit. The checksum manifest is written **outside** the directory it authenticates so it cannot recursively hash itself.

Before interpretation, back up the raw run directories together with their checksum manifests, gateway catalogue snapshot, local data provenance, protocol-freeze snapshot and pre/post-run environment snapshots.

## Analysis

The canonical analysis pipeline produces:

- deterministic RQ1 summaries and 10,000-replicate verb-cluster intervals;
- K=5 sampling uncertainty;
- four-signal failure ranking;
- A→C / B→D paired updates;
- prompt/order robustness;
- tie-aware selective risk/coverage;
- cached-verifier RQ3 policies and token/call cost;
- vector PDF/SVG empirical figures;
- generated LaTeX result tables.

A paper number should flow from `raw → audit → processed → generated paper artifact`. Do not manually transcribe a terminal value when the generated table/figure pipeline can supply it.

## Publication boundary

See `docs/ARTIFACT_POLICY.md`. Raw provider output, third-party benchmark bytes, and generated empirical files are not automatically public just because the source repository is public. Any eventual artifact release must be tied to the submitted/accepted manuscript commit and reviewed for dataset license, provider terms, credential/privacy leakage, and evidence consistency.
