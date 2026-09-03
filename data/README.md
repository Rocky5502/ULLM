# Data provenance: ImperfectiveNLI

The experiment reuses **ImperfectiveNLI** from Bolei Ma and Yusuke Miyao, *The Imperfective Paradox in Large Language Models* (ACL 2026 Best Paper). The source paper/release reports the dataset under **CC BY-NC 4.0** for research use. We preserve provenance rather than silently re-license it as project-owned data.

## Frozen upstream identity

The experiment no longer downloads from the mutable `main` branch. The exact source is pinned to:

- repository: `boleima/ImperfectiveParadox`
- commit: `8845a732d04a0b49e154fbf0db334d48d895b11f`
- path: `data/imperfectiveNLI.json`
- Git blob SHA-1: `e20112c9de1f8c8ab27a8e2b969699b23dcdb186`
- expected bytes: `100970`
- expected examples: `400`

At the time this record was prepared, the upstream GitHub repository did not expose a root `LICENSE` file. We therefore do not infer broader rights from the repository itself. See `THIRD_PARTY_DATA.md` for the explicit boundary between third-party data and this repository's MIT-licensed code.

## Fetch and validate

```bash
python scripts/fetch_imperfective_nli.py
python scripts/validate_dataset.py data/imperfectiveNLI.json
python scripts/preflight.py
```

The downloader rejects a payload whose Git-blob identity, byte count, schema, or example count differs from the frozen artifact. It writes `data/MANIFEST.local.json` containing the immutable source commit/path and local SHA-256.

The dataset validator independently checks:

- 400 unique canonical IDs (`A_001` ... `D_100`);
- 100 rows per A/B/C/D group;
- exact gold labels for each group;
- required fields;
- A↔C verb, hypothesis, and verb-class pairing;
- B↔D verb, hypothesis, and verb-class pairing.

It writes `data/dataset_manifest.json`. `scripts/preflight.py` then requires the downloaded bytes, committed `MANIFEST.json`, local download manifest, and validator manifest to agree before the experimental runner is considered ready.

## Expected semantic structure

- **A — Interrupted Accomplishment:** 100 examples, gold `False`.
- **B — Interrupted Activity:** 100 examples, gold `True`.
- **C — Ambiguous Accomplishment:** 100 examples, gold `Unknown`.
- **D — Ambiguous Activity:** 100 examples, gold `True`.

A/C share telic verbs item-wise; B/D share atelic verbs item-wise. That exact paired structure is used by the paper's A→C and B→D probability-update analyses.

## Git policy

`data/imperfectiveNLI.json`, `data/MANIFEST.local.json`, and `data/dataset_manifest.json` are intentionally ignored by Git. CI fetches the immutable benchmark on demand, validates it, performs the full zero-API request rehearsal, and uploads provenance manifests as workflow artifacts. This preserves reproducibility without presenting the third-party benchmark as project-owned source data.
