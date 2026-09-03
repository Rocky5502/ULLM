# Experiment-Ready v3 Freeze

Date: 2026-09-03

`experiment-ready-v3` is the final pre-main-study completion-budget compatibility freeze derived from immutable `experiment-ready-v2` after the second 100-call smoke.

## Observed v2 smoke outcome

The v2 smoke kept the frozen neutral deterministic design and raised only `max_tokens` from 220 to 1024.

- GPT route: 20/20 parse-valid.
- Claude route: 20/20 parse-valid.
- Qwen route: 20/20 parse-valid.
- Gemini route: 20/20 parse-valid; the v1 truncation problem disappeared.
- DeepSeek route: 17/20 parse-valid; 3/20 remained parse failures.
- All three remaining DeepSeek failures were the exact same failure class: `finish_reason=length` at the 1024-token ceiling (`A_015`, `D_007`, `A_036`).

Thus v2 improved total parse validity from 82/100 to 97/100 and isolated the remaining blocker to DeepSeek completion-budget exhaustion.

## Single v3 execution-setting change

`max_tokens` is raised from **1024 to 4096** before any main-study result exists. This is only a ceiling; routes that stop normally are not forced to consume 4096 tokens.

No RQ, hypothesis, dataset item, model route, prompt, temperature, sampling K, robustness subset, metric, threshold, bootstrap setting, or analysis rule changes.

The parser remains strict and is not allowed to reconstruct truncated outputs.

## New hard audit

`scripts/audit_completion_budget.py` fails if any preserved live response ends with `finish_reason=length`, even if the partial output happened to be parseable. This closes the gap exposed by the v2 smoke.

A fresh `smoke-neutral-v3` must satisfy both the ordinary manifest-aware `audit_run.py` and the completion-budget audit for all five routes before the 15,800-call main study is authorized.

`experiment-ready-v1` and `experiment-ready-v2` remain immutable provenance checkpoints.
