# Experiment Protocol

1. `python scripts/fetch_imperfective_nli.py`
2. Set `ZZZ_API_KEY` locally; never place it in a command transcript or repository.
3. `python scripts/check_models.py` and save the printed availability snapshot.
4. Smoke test one model / 8 examples: `PYTHONPATH=src python -m ullm.run --mode deterministic --model gpt-5.4 --limit 8`
5. Freeze prompt/config/model IDs and commit **before** the full run.
6. Run deterministic confidence elicitation for all five models.
7. Run repeated sampling (`K=5`) for uncertainty ranking. If budget is tight, preregister K=3 before looking at results rather than changing it post hoc.
8. Summarize deterministic files with `scripts/summarize_results.py`.
9. Produce risk–coverage curves and verb-cluster bootstrap CIs.
10. Only then replace every `TBD` in the paper; never backfill a claim before the corresponding artifact exists.

## Reproducibility rules

- Store raw model text, parsed JSON, returned model ID, token usage, timestamp, decoding parameters, repeat index, and dataset SHA-256.
- Never silently repair a semantically invalid answer. Parsing normalization may only fix probability rounding; parse failures are counted and reported.
- Report API/gateway date because routed model implementations may change.
- Keep the source dataset's license/attribution separate from this repository's code license.
