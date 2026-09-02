# Experiment Protocol

## Before any paid API call

1. Create/activate the Python environment and install `requirements.txt`.
2. `python scripts/fetch_imperfective_nli.py`.
3. `python scripts/preflight.py`. This validates project/config consistency, exact dataset structure, and `data/MANIFEST.local.json` provenance.
4. Set `ZZZ_API_KEY` locally; never place it in Git, a screenshot, manuscript, or shared shell transcript.
5. `python scripts/check_models.py` immediately before execution and retain the timestamped model-catalog snapshot under `results/catalog/`.
6. Confirm `configs/experiment.yaml`, `configs/models.yaml`, `configs/preregistered_hypotheses.yaml`, prompt source, and git commit are frozen.
7. Run `pytest -q`; do not begin full calls on a failing commit.

## Frozen run sequence

The canonical Windows entry point is `scripts/run_frozen.ps1`; POSIX users can use `scripts/run_frozen.sh`. Both entry points are resumable and audit every stage.

1. **Balanced smoke:** 20 A/B/C/D-balanced examples × five models under the neutral prompt (100 calls). A hard manifest-aware audit and smoke summary must PASS before the script accepts the literal confirmation `RUN`.
2. **Primary deterministic:** 400 examples × five models × one neutral deterministic response = 2,000 calls, then immediate audit.
3. **Repeated sampling:** 400 × five × K=5 neutral stochastic responses = 10,000 calls, then exact-K audit.
4. **Strict-logic robustness:** fixed balanced 120 × five = 600 calls, then audit.
5. **Definition-aware robustness:** fixed balanced 120 × five = 600 calls, then audit.
6. **Label-order robustness:** the same deterministic seed-42 balanced 120 × five under the neutral prompt with reversed output label order = 600 calls, then audit.
7. **Verifier cache:** 400 × five independent aspect-sensitive verifier responses = 2,000 calls, then audit.
8. **Analysis:** all statistical outputs, vector figures, and LaTeX result tables are generated automatically only after every hard audit passes.

Main-study total: **15,800 calls before retries**, plus 100 smoke calls.

## Primary prompt rule

The primary neutral prompt must not teach the telic/atelic rule. It asks for ordinary three-way NLI using only supplied evidence and forbids adding unstated facts. `strict_logic` and `definition_aware` are robustness interventions, not candidates from which the best prompt will be chosen after results.

## Response contract

Each model returns a JSON object containing:

- `label`: True / False / Unknown;
- probabilities for all three labels;
- one-sentence `reason_short`.

The parser checks finite/range-valid probabilities and normalizes only numerical rounding deviation. The runner stores raw and parsed outputs, raw probability sum, normalization delta, label/argmax consistency, exact message hash, prompt hash/type, label order, requested seed/max tokens, timestamp, requested/returned model ID, latency, request ID, usage metadata, repeat index, and the full example record. Label/argmax disagreement is an audit failure rather than a silently repaired response.

## Failure/retry policy

- HTTP retryable failures use bounded exponential backoff, `Retry-After` when available, and jitter.
- Runs are resumable by `(example_id, repeat)` only when the frozen manifest's critical fields match the attempted resume.
- Request failures and parse failures remain visible audit records on the first attempt; they are not silently dropped.
- To retry them, use `--resume --retry-failures` (the canonical run scripts do this automatically when a compatible run directory already exists). Failed rows are atomically removed before replacement so duplicate keys are not created.
- A parser may normalize probability-rounding error, but it may not repair a semantically invalid label or invent missing probability values.
- If a provider/gateway changes a model alias or routing during the experiment, stop, preserve artifacts, and document the drift before deciding whether a clean rerun is necessary.

## Analysis sequence

Run `scripts/analyze_frozen.ps1` or `scripts/analyze_frozen.sh`. The pipeline:

1. validates every output against its frozen manifest;
2. produces RQ1 deterministic summaries and 10,000-replicate verb-cluster bootstrap intervals;
3. computes RQ2 sampling and unified four-signal failure ranking;
4. computes A→C / B→D paired semantic updates and prompt/order robustness;
5. computes tie-aware, threshold-realizable RQ3 risk–coverage and cached-verifier policies;
6. generates PDF/SVG result figures; and
7. regenerates `paper/generated/rq1_table.tex`, `rq2_table.tex`, and `rq3_table.tex` directly from processed CSVs.

No manuscript number should be hand-copied from console output.

## Reproducibility rule

Never change model panel, prompt wording, K, thresholds, or benchmark labels in response to observed main results without documenting the change as post-hoc exploratory analysis. The source dataset's attribution/license remains separate from the repository's software license. The compact RQ3 table operating point (`1-maxprob >= 0.20`) is frozen before results; the full threshold sweep remains primary evidence.
