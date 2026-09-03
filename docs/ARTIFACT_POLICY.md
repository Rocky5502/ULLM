# Research artifact policy

This policy prevents three common reproducibility failures: accidentally publishing credentials/provider outputs, accidentally re-licensing third-party data, and losing the exact evidence used for a paper result.

## Artifact classes

### A. Public source artifacts — committed

These belong in Git history:

- `src/ullm/` implementation;
- experiment/model/hypothesis configs;
- prompt definitions;
- tests and CI workflows;
- analysis/figure/table generation code;
- manuscript source and pre-run `TBD` placeholders;
- provenance metadata that does not contain the third-party dataset itself;
- research plans, runbooks, progress and reproducibility documentation.

### B. Third-party benchmark bytes — local/untracked

`data/imperfectiveNLI.json` is fetched from the immutable upstream commit and is not project-owned source code. It remains ignored by Git together with local provenance/validation manifests.

A future public data bundle must be reviewed against the upstream terms before redistributing benchmark bytes. Until that review, reproducibility is provided by immutable source commit + Git blob + byte count + local SHA-256 verification.

### C. Provider execution evidence — local/untracked by default

Raw API artifacts may contain provider-returned text and potentially large response payloads:

- `results/raw/<run-id>/manifest.json`;
- raw JSONL response files;
- live gateway catalogue snapshots;
- provider usage/billing exports if retained separately.

These must not be committed casually. Immediately after a successful live stage, create an external SHA-256 evidence manifest with `scripts/checksum_run.py` and preserve a read-only backup before interpretation.

Before any public release of raw provider output, review provider terms, privacy/security exposure, accidental credential leakage, and whether short model rationales should be redistributed.

### D. Derived empirical artifacts — local during analysis; release deliberately

Processed CSVs and empirical figures are generated from audited raw records. They remain ignored by Git during the live research cycle so partial or stale results cannot be mistaken for frozen paper evidence.

For an eventual artifact release, publish only a version tied to the submitted/accepted manuscript commit and include:

- raw-run checksum manifests or stable evidence identifiers;
- exact analysis commit;
- processed CSVs used by the paper;
- final vector figures;
- generated LaTeX tables;
- a statement of which raw/provider artifacts are included or withheld and why.

### E. Credentials — never recorded

`ZZZ_API_KEY` must exist only in the local shell/environment or another credential manager. It must never appear in Git, issues, manuscripts, environment snapshots, request plans, raw manifests, screenshots, or shared archives.

`environment_snapshot.py` records only the boolean `api_key_present` and explicitly records `api_key_value_recorded=false`.

## Retention stages

### Before paid execution

Retain committed source/config/manuscript state and CI/offline-rehearsal artifacts. No empirical dataset/model result is claimed.

### Immediately after each paid stage

1. Require run audit PASS.
2. Create `scripts/checksum_run.py` manifest outside the run directory.
3. Copy raw run + checksum + local data manifest + environment snapshot + model catalogue snapshot to a read-only backup location.
4. Do not edit raw JSONL manually.

### During analysis

Derived files may be regenerated freely from immutable raw evidence. If analysis code changes, record a new Git commit and regenerate; do not silently overwrite the evidence identity used by a manuscript claim.

### At submission

Create a submission evidence bundle containing the exact manuscript source/PDF, Git commit, configs, provenance manifests, generated paper tables/figures, and checksum references to raw runs. The bundle should be immutable once the paper is submitted.

### After review/acceptance

Decide the public artifact contents only after checking IASEAI policy, upstream dataset terms, gateway/provider terms, anonymity status, and repository cleanliness. Public release is a deliberate publication action, not a side effect of the experiment.

## Naming and immutability rules

- Every experimental stage uses a stable run ID.
- Never reuse a live run ID for a scientifically different protocol.
- Resume only against a compatible manifest.
- Dry-run IDs are not live-run IDs; `execution_mode` prevents cross-mode resume.
- `TBD` placeholders remain committed until real audited result artifacts exist.
- Paper values should come from generated artifacts, not manual transcription.

## Release checklist

Before making any generated artifact public, verify:

- no `.env`, token, API key, authorization header, or credential-like value;
- no unreviewed third-party benchmark bytes;
- no stale/synthetic result file presented as empirical evidence;
- all model identifiers are described as gateway routing IDs where appropriate;
- all empirical files trace to PASS audits and checksum-protected raw evidence;
- the public artifact corresponds to the manuscript version it claims to reproduce.
