# Experiment Protocol

## Before any paid API call

1. Create/activate the Python environment and install `requirements.txt`.
2. `python scripts/fetch_imperfective_nli.py`.
3. `python scripts/validate_dataset.py data/imperfectiveNLI.json` and retain `data/dataset_manifest.json`.
4. Set `ZZZ_API_KEY` locally; never place it in Git, a screenshot, manuscript, or shared shell transcript.
5. `python scripts/check_models.py` immediately before execution and retain the model-catalog snapshot.
6. Confirm `configs/experiment.yaml`, `configs/models.yaml`, `configs/preregistered_hypotheses.yaml`, prompt source, and git commit are frozen.
7. Run `pytest -q`; do not begin full calls on a failing commit.

## Frozen run sequence

The canonical Windows entry point is `scripts/run_frozen.ps1`; POSIX users can use `scripts/run_frozen.sh`.

1. **Balanced smoke:** 20 A/B/C/D-balanced examples × five models under the neutral prompt (100 calls). Inspect request errors, parser behavior, returned model IDs and probability format.
2. **Primary deterministic:** 400 examples × five models × one neutral deterministic response = 2,000 calls.
3. **Repeated sampling:** 400 × five × K=5 neutral stochastic responses = 10,000 calls.
4. **Strict-logic robustness:** fixed balanced 120 × five = 600 calls.
5. **Definition-aware robustness:** fixed balanced 120 × five = 600 calls.
6. **Label-order robustness:** the same fixed balanced 120 × five under neutral prompt with reversed output label order = 600 calls.
7. **Verifier cache:** 400 × five independent aspect-sensitive verifier responses = 2,000 calls.

Main-study total: **15,800 calls before retries**, plus 100 smoke calls.

## Primary prompt rule

The primary neutral prompt must not teach the telic/atelic rule. It asks for ordinary three-way NLI using only supplied evidence and forbids adding unstated facts. `strict_logic` and `definition_aware` are robustness interventions, not candidates from which the best prompt will be chosen after results.

## Response contract

Each model returns a JSON object containing:

- `label`: True / False / Unknown;
- normalized `probabilities` for all three labels;
- one-sentence `reason_short`.

The runner stores raw and parsed outputs, raw probability sum, normalization delta, label/argmax consistency, prompt hash/type, label order, timestamp, requested/returned model ID, latency, request ID, usage metadata, repeat index, and the full example record.

## Failure/retry policy

- HTTP retryable failures use bounded exponential backoff and jitter.
- Runs are resumable by `(example_id, repeat)` and never intentionally duplicate completed records.
- Request failures and parse failures remain visible audit records; they are not silently dropped.
- A parser may normalize small probability-rounding error, but it may not repair a semantically invalid label or invent missing probability mass.
- If a provider/gateway changes a model alias during the experiment, stop, preserve artifacts, and document the drift before deciding whether a clean rerun is necessary.

## Analysis sequence

Run `scripts/analyze_frozen.ps1`. It first applies hard audits, then produces RQ1 summaries, RQ2 sampling and paired/prompt analyses, RQ3 selective and cached-verifier analyses, and PDF/SVG result figures. Manuscript values may be filled only from these processed artifacts after PASS audits.

## Reproducibility rule

Never change model panel, prompt wording, K, thresholds, or benchmark labels in response to observed main results without documenting the change as post-hoc exploratory analysis. The source dataset's attribution/license remains separate from the repository's software license.
