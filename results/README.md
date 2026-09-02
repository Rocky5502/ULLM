# Results artifacts

Generated outputs are intentionally not committed during design freeze.

Each run is written under `results/raw/<run_id>/` with a `manifest.json` and one JSONL file per model/mode. The manifest records dataset SHA-256, requested model IDs, configuration, run timestamp, and any smoke-test limit. Each JSONL record stores the benchmark example, parsed prediction, raw text, raw API response metadata, token usage, returned model ID, temperature, and repeat index.

Use `scripts/summarize_results.py` for deterministic confidence runs, `scripts/analyze_sampling.py` for repeated-sampling uncertainty, and `scripts/make_result_figures.py` for vector PDF figures after real results exist.

Large generated raw and processed outputs are gitignored by default. For the final archival release, freeze the exact run directory (or publish it as a release/archival artifact) together with checksums and the paper version that consumed it.
