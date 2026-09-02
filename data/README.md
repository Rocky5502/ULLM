# Dataset

The study reuses **ImperfectiveNLI**, introduced in *The Imperfective Paradox in Large Language Models* (Ma & Miyao, ACL 2026).

We intentionally do **not** vendor the dataset in this repository by default. The paper states that the dataset is released under **CC BY-NC 4.0** for research use. Use the downloader below so the upstream source, attribution, and checksum remain explicit:

```bash
python scripts/fetch_imperfective_nli.py
```

Upstream artifact:
`https://github.com/boleima/ImperfectiveParadox/blob/main/data/imperfectiveNLI.json`

Expected schema: `id`, `group`, `verb_class`, `verb`, `premise`, `hypothesis`, `label`.

Before archival release, record the fetched file's SHA-256 in the experiment manifest.
