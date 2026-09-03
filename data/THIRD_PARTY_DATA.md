# Third-party data notice

This repository's software license does **not** re-license ImperfectiveNLI.

## ImperfectiveNLI

- **Authors:** Bolei Ma and Yusuke Miyao
- **Paper:** *The Imperfective Paradox in Large Language Models* (ACL 2026)
- **Upstream repository:** `https://github.com/boleima/ImperfectiveParadox`
- **Pinned source commit:** `8845a732d04a0b49e154fbf0db334d48d895b11f`
- **Canonical path:** `data/imperfectiveNLI.json`
- **Frozen upstream Git blob:** `e20112c9de1f8c8ab27a8e2b969699b23dcdb186`
- **Expected byte count:** `100970`
- **Expected examples:** `400`
- **License reported by the source paper/release:** CC BY-NC 4.0

The local experiment fetches the dataset from the immutable upstream commit and verifies its Git-blob hash, byte count, schema, group counts, labels, and A↔C / B↔D lexical pairing before use. The local SHA-256 is then recorded in `data/MANIFEST.local.json` and copied into every frozen run manifest.

At the time this provenance record was prepared, the upstream GitHub repository did not expose a root `LICENSE` file. We therefore do not infer or broaden any rights from the repository itself; the project records the dataset terms as reported by the source paper/release and keeps the benchmark outside the MIT-licensed project code.

See `data/MANIFEST.json`, `scripts/fetch_imperfective_nli.py`, and `scripts/validate_dataset.py` for the machine-verifiable provenance chain.

Users of this repository are responsible for complying with the upstream dataset terms. The dataset is intentionally ignored by Git and is not committed as project-owned data.
