# Data provenance: ImperfectiveNLI

The experiment reuses **ImperfectiveNLI** from Bolei Ma and Yusuke Miyao, *The Imperfective Paradox in Large Language Models* (ACL 2026 Best Paper). The source paper reports the dataset under **CC BY-NC 4.0** for research use. We preserve provenance rather than silently re-license it as project-owned data.

The canonical file is `boleima/ImperfectiveParadox:data/imperfectiveNLI.json`. `MANIFEST.json` freezes the upstream Git blob SHA-1 (`e20112c9de1f8c8ab27a8e2b969699b23dcdb186`), byte count, schema expectations, and group counts. Run:

```bash
python scripts/fetch_imperfective_nli.py
python scripts/validate_dataset.py data/imperfectiveNLI.json
```

The downloader rejects any payload whose Git-blob hash differs from the frozen upstream artifact, then records a local SHA-256 digest in `data/MANIFEST.local.json`. This makes the experimental dataset exact and auditable while keeping upstream attribution explicit.

Expected structure: 400 examples; 100 each in A (Interrupted Accomplishment, False), B (Interrupted Activity, True), C (Ambiguous Accomplishment, Unknown), and D (Ambiguous Activity, True). A/C share telic verbs item-wise; B/D share atelic verbs item-wise.
