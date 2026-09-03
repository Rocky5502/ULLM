# Main Stage 1 argmax-contract diagnostic — 2026-09-03

The first full neutral deterministic main-study stage (`frozen-det-neutral-v1`) completed all 2,000 requested records, but the manifest-aware scientific audit stopped the pipeline before Stage 6.

Observed audit state:

- `gpt-5.6-sol`: PASS.
- `deepseek-v4-pro`: PASS.
- `gemini-3.7-flash`: PASS, with 31 successful rows requiring more than one HTTP attempt.
- `claude-sonnet-5`: FAIL due to 10 label/probability argmax-contract violations.
- `qwen3.8-max`: FAIL due to 8 label/probability argmax-contract violations.

The frozen prompt explicitly requires the returned `label` to equal the highest-probability class unless there is an exact tie. The parser already accepts exact ties by defining all numerically equal maxima as admissible. Therefore these 18 rows must be inspected before any decision is made. No Stage-6 sampling calls should be started, no rows should be deleted or re-run, and no audit/parser threshold should be relaxed before examining the preserved raw outputs.

This is an execution/audit record, not an empirical conclusion for RQ1/RQ2/RQ3.
