# Experiment-Ready v2 Freeze

Date: 2026-09-03

`experiment-ready-v2` is a pre-main-study compatibility freeze derived from `experiment-ready-v1` after the first 100-call smoke test failed its structured-output audit.

## Observed v1 smoke failure

The smoke used the frozen neutral deterministic prompt, 20 balanced examples per model, and `max_tokens: 220`.

- GPT route: 20/20 parse-valid.
- Claude route: 20/20 parse-valid.
- Qwen route: 20/20 parse-valid.
- DeepSeek route: 8/20 parse-valid; 12/20 failed parsing.
- Gemini route: 14/20 parse-valid; 6/20 failed parsing.
- Request failures: 0 across all five routes.

Raw-response diagnosis showed completion-budget exhaustion rather than a semantic parser incompatibility:

- Every failed DeepSeek row had `finish_reason=length` and exactly 220 completion tokens. Eleven returned empty final `content` while preserving a long `reasoning_content`; one returned a JSON prefix truncated mid-object.
- Four of six failed Gemini rows reported `finish_reason=length`; all six raw `content` values were visibly truncated JSON/code-fence prefixes. The two Gemini rows that reported `finish_reason=stop` were still incomplete, so provider finish metadata alone is not accepted as evidence of response completeness.

## Single v2 scientific-setting change

`max_tokens` is raised from **220 to 1024** before any main-study result exists.

No RQ, hypothesis, dataset item, model route, neutral primary prompt, robustness condition, decoding temperature, sampling K, metric, threshold, bootstrap setting, or analysis rule changes.

The parser is intentionally **not** relaxed to reconstruct truncated JSON. Incomplete outputs remain audit failures. The 100-call smoke must be repeated from scratch under v2 and all five model files must pass the hard audit before the 15,800-call main study is authorized.

The original `experiment-ready-v1` branch remains immutable for provenance.
