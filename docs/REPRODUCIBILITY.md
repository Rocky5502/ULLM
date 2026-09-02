# Reproducibility and Audit Checklist

- Exact upstream Git-blob hash for dataset stored in `data/MANIFEST.json`.
- Local SHA-256 generated after download.
- 400-item schema, labels, group balance, A/C and B/D pairing validated.
- Model catalogue snapshotted immediately before experiment.
- Git commit, prompt hashes, dataset hash, configs, timestamps stored in manifests.
- Requested and returned model identifiers stored per response.
- Raw response, parsed response, parser error, latency, usage, temperature, repeat and requested seed stored per call.
- Resume is idempotent by `(example_id, repeat)`.
- No chain-of-thought requested or retained; only a one-sentence rationale.
- Statistics use verb clusters and multiplicity correction.
- Conceptual figures are TikZ; empirical figures generated as PDF + SVG from processed CSVs.
- Every final paper number must be reverse-traceable to a processed artifact and raw records.
